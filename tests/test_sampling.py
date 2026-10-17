from collections import defaultdict
from fractions import Fraction
from itertools import combinations
import random
import unittest

import numpy as np

from engine.metrics import MetricSpace
from engine.sampling import SamplingError, sample


def fixture_space():
    # Distances 1/2 form a metric. Threshold 2 exposes this compatibility graph.
    distances = np.ones((6, 6))
    np.fill_diagonal(distances, 0)
    for left, right in [(0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4), (1, 5), (2, 3), (3, 4), (4, 5)]:
        distances[left, right] = distances[right, left] = 2
    return MetricSpace("xyrgb", distances, ((0, 1), (0, 2), (2,), (3,), (4,), (5,)))


class ProposalRng:
    def __init__(self, ticket, subset):
        self.ticket = ticket
        self.subset = subset

    def randrange(self, total):
        assert total == 9
        return self.ticket

    def sample(self, eligible, count):
        assert count == len(self.subset)
        assert set(self.subset) <= set(eligible)
        return list(self.subset)

    def shuffle(self, items):
        pass


class SamplingTests(unittest.TestCase):
    def test_every_valid_set_has_exactly_equal_proposal_mass(self):
        space = fixture_space()
        masses = defaultdict(Fraction)
        for ticket in range(9):
            candidates = (2, 3, 4) if ticket < 3 else (2, 3, 4, 5)
            subsets = list(combinations(candidates, 2))
            for subset in subsets:
                try:
                    result = sample(space, 0, 3, 2, ProposalRng(ticket, subset), max_attempts=1)
                except SamplingError as error:
                    self.assertEqual(error.code, "exhausted")
                    continue
                masses[tuple(sorted(result.centers))] += Fraction(1, 9 * len(subsets))
        self.assertEqual(set(masses), {(0, 2, 3), (0, 3, 4), (1, 2, 3), (1, 3, 4), (1, 4, 5)})
        self.assertEqual(set(masses.values()), {Fraction(1, 9)})

    def test_target_is_in_exactly_one_cluster_and_all_centers_are_separated(self):
        space = fixture_space()
        rng = random.Random(42)
        for _ in range(200):
            result = sample(space, 0, 3, 2, rng)
            self.assertEqual(sum(0 in cluster for cluster in result.clusters), 1)
            self.assertTrue(all(space.compatible(left, right, 2) for left, right in combinations(result.centers, 2)))
            for center, members in zip(result.centers, result.clusters):
                self.assertEqual(set(members), set(space.clusters[center]))

    def test_impossibility_is_different_from_exhaustion(self):
        space = fixture_space()
        with self.assertRaises(SamplingError) as impossible:
            sample(space, 0, 3, 3)
        self.assertEqual(impossible.exception.code, "infeasible")
        with self.assertRaises(SamplingError) as exhausted:
            sample(space, 0, 3, 2, ProposalRng(0, (2, 4)), max_attempts=1)
        self.assertEqual(exhausted.exception.code, "exhausted")

    def test_rejection_discards_the_anchor_and_resamples_the_whole_proposal(self):
        class TwoAttempts:
            def __init__(self):
                self.tickets = iter((0, 3))
                self.subsets = iter(((2, 4), (4, 5)))
                self.draws = 0

            def randrange(self, total):
                self.assert_total = total
                self.draws += 1
                return next(self.tickets)

            def sample(self, eligible, count):
                return list(next(self.subsets))

            def shuffle(self, items):
                pass

        rng = TwoAttempts()
        result = sample(fixture_space(), 0, 3, 2, rng, max_attempts=2)
        self.assertEqual(result.centers, (1, 4, 5))
        self.assertEqual(result.attempts, 2)
        self.assertEqual(rng.draws, 2)
        self.assertEqual(rng.assert_total, 9)

    def test_nonfinite_separation_is_rejected_before_sampling(self):
        for threshold in (-1, float("nan"), float("inf")):
            with self.subTest(threshold=threshold), self.assertRaises(ValueError):
                sample(fixture_space(), 0, 3, threshold)

    def test_single_cluster_still_contains_target(self):
        result = sample(fixture_space(), 0, 1, 100, random.Random(7))
        self.assertEqual(len(result.clusters), 1)
        self.assertIn(0, result.clusters[0])


if __name__ == "__main__":
    unittest.main()
