"""Uniform target-conditioned sampling of separated cluster-center sets."""

from dataclasses import dataclass
import math
import random

import numpy as np


class SamplingError(ValueError):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SamplingResult:
    centers: tuple[int, ...]
    clusters: tuple[tuple[int, ...], ...]
    attempts: int


def sample(space, target, count, threshold, rng=None, max_attempts=5000):
    """Keep target fixed; return a uniform valid set, or a bounded failure.

    An anchor a is proposed with weight C(|B_a|, count-1), then a uniform
    distractor subset is proposed. Every complete proposal has equal mass.
    Rejecting the WHOLE proposal when distractors conflict preserves uniformity.
    """
    size = len(space.clusters)
    if not 0 <= target < size or not 1 <= count <= size:
        raise ValueError("Invalid target or cluster count.")
    if not math.isfinite(threshold) or threshold < 0:
        raise ValueError("Separation must be a finite nonnegative number.")
    if max_attempts < 1:
        raise ValueError("At least one sampling attempt is required.")
    rng = rng or random.SystemRandom()
    anchors = space.reverse_clusters(target)
    is_correct = np.zeros(size, dtype=bool)
    is_correct[list(anchors)] = True
    proposals = []
    total_weight = 0
    distractor_count = count - 1
    for anchor in anchors:
        eligible = np.flatnonzero(space.compatibility_mask(anchor, threshold) & ~is_correct)
        if len(eligible) < distractor_count:
            continue
        # Python integers avoid overflow and floating-point weighting bias.
        weight = math.comb(len(eligible), distractor_count)
        total_weight += weight
        proposals.append((int(anchor), tuple(int(index) for index in eligible), total_weight))
    if total_weight == 0:
        raise SamplingError(
            "No valid cluster set exists for this target with these settings. Reduce the cluster count or separation.",
            "infeasible",
        )

    for attempt in range(1, max_attempts + 1):
        ticket = rng.randrange(total_weight)
        for anchor, eligible, cumulative in proposals:
            if ticket < cumulative:
                break
        distractors = rng.sample(eligible, distractor_count)
        if not all(space.compatible(left, right, threshold)
                   for index, left in enumerate(distractors)
                   for right in distractors[index + 1:]):
            continue
        centers = [anchor, *distractors]
        rng.shuffle(centers)
        clusters = []
        for center in centers:
            members = list(space.clusters[center])
            rng.shuffle(members)
            clusters.append(tuple(members))
        if sum(target in cluster for cluster in clusters) != 1:
            raise AssertionError("The sampled target must occur in exactly one cluster.")
        return SamplingResult(tuple(centers), tuple(clusters), attempt)

    raise SamplingError(
        "Could not find a valid cluster set within the attempt limit. This does not prove these settings are impossible; reduce the cluster count or separation and retry.",
        "exhausted",
    )
