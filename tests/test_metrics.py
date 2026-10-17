import math
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from engine.metrics import MetricProvider, _nearest_clusters
from engine.game import GameError, validate_settings


def catalog(points, near=(), opposite=()):
    count = len(points)
    def layer(edges):
        result = [set() for _ in points]
        for left, right in edges:
            result[left].add(right)
            result[right].add(left)
        return [frozenset(neighbors) for neighbors in result]
    return SimpleNamespace(
        genres=[{"id": index, "name": str(index), "x": point[0], "y": point[1], "color": point[2]}
                for index, point in enumerate(points)],
        near=layer(near), opposite=layer(opposite),
    )


class MetricTests(unittest.TestCase):
    def test_xyrgb_uses_one_spatial_scale_and_distinct_pair_rms(self):
        data = catalog([(0, 0, "#000000"), (3, 0, "#030000"), (0, 4, "#000400")])
        space = MetricProvider(data).get({"metric": "xyrgb", "alpha": 0.8})
        scale_squared = (9 + 16 + 25) / 3
        self.assertAlmostEqual(space.metadata["position_scale"] ** 2, scale_squared)
        self.assertAlmostEqual(space.metadata["color_scale"] ** 2, scale_squared)
        self.assertAlmostEqual(space.distance(0, 1), 3 / math.sqrt(scale_squared))
        self.assertAlmostEqual(space.distance(0, 2), 4 / math.sqrt(scale_squared))
        np.testing.assert_array_equal(space.distances, space.distances.T)
        np.testing.assert_array_equal(np.diag(space.distances), 0)

    def test_changing_weight_changes_actual_geometry(self):
        data = catalog([(0, 0, "#000000"), (1, 0, "#ffffff"), (10, 0, "#010101")])
        provider = MetricProvider(data)
        spatial = provider.get({"metric": "xyrgb", "alpha": 0.99})
        color = provider.get({"metric": "xyrgb", "alpha": 0.01})
        self.assertLess(spatial.distance(0, 1), spatial.distance(0, 2))
        self.assertGreater(color.distance(0, 1), color.distance(0, 2))
        self.assertIs(spatial, provider.get({"metric": "xyrgb", "alpha": 0.99}))

    def test_nearest_twenty_include_center_with_deterministic_id_ties(self):
        distances = np.ones((23, 23))
        np.fill_diagonal(distances, 0)
        clusters = _nearest_clusters(distances)
        self.assertEqual(clusters[22], (22, *range(19)))
        self.assertTrue(all(len(cluster) == 20 and index in cluster for index, cluster in enumerate(clusters)))

    def test_configurable_cluster_size_endpoints_preserve_ties_and_share_geometry(self):
        # Every off-diagonal kernel distance is sqrt(2), so ID tie-breaking is observable.
        data = catalog([(0, 0, "#000000") for _ in range(30)])
        for kind, build_method in (("xyrgb", "_xyrgb"), ("kernel", "_kernel")):
            with self.subTest(metric=kind):
                provider = MetricProvider(data)
                with patch.object(provider, build_method, wraps=getattr(provider, build_method)) as build:
                    small = provider.get({"metric": kind, "cluster_size": 5})
                    large = provider.get({"metric": kind, "cluster_size": 25})
                    default = provider.get({"metric": kind})
                self.assertEqual(build.call_count, 1)
                self.assertIs(small.distances, large.distances)
                self.assertIs(default.distances, large.distances)
                self.assertEqual(set(small.clusters[29]), {29, 0, 1, 2, 3})
                self.assertEqual(set(large.clusters[29]), {29, *range(24)})
                for space, size in ((small, 5), (large, 25), (default, 20)):
                    self.assertTrue(all(len(members) == size and center in members
                                        for center, members in enumerate(space.clusters)))
                    self.assertEqual(space.metadata["cluster_size"], size)
                self.assertEqual(small.reverse_clusters(10), (10,))
                self.assertEqual(large.reverse_clusters(10), tuple(range(30)))
                self.assertIs(small, provider.get({"metric": kind, "cluster_size": 5}))

    def test_cluster_size_views_and_geometry_cache_remain_bounded(self):
        provider = MetricProvider(catalog([(index, 0, "#000000") for index in range(30)]), cache_size=1)
        first = provider.get({"metric": "xyrgb", "alpha": .8, "cluster_size": 5})
        with patch.object(provider, "_xyrgb", wraps=provider._xyrgb) as build:
            for size in (10, 15, 20, 25, 5):
                space = provider.get({"metric": "xyrgb", "alpha": .8, "cluster_size": size})
                self.assertIs(space.distances, first.distances)
            self.assertEqual(build.call_count, 0)
            self.assertLessEqual(len(next(iter(provider._cache.values()))), 3)
            provider.get({"metric": "xyrgb", "alpha": .7, "cluster_size": 5})
            self.assertEqual(len(provider._cache), 1)
            rebuilt = provider.get({"metric": "xyrgb", "alpha": .8, "cluster_size": 5})
            self.assertEqual(build.call_count, 2)
            self.assertIsNot(rebuilt.distances, first.distances)

    def test_continuous_cluster_size_is_strictly_validated(self):
        provider = MetricProvider(catalog([(index, 0, "#000000") for index in range(30)]))
        for kind in ("xyrgb", "kernel"):
            for size in (None, False, 4, 26, 5.0, "5", float("nan"), [], {}):
                with self.subTest(metric=kind, size=size), self.assertRaises(ValueError):
                    provider.get({"metric": kind, "cluster_size": size})

    def test_reverse_nearest_membership_is_not_forward_membership(self):
        points = [(index, 0, "#000000") for index in range(21)] + [(10000, 0, "#000000")]
        space = MetricProvider(catalog(points)).get({"metric": "xyrgb"})
        self.assertEqual(space.reverse_clusters(21), (21,))
        self.assertEqual(len(space.clusters[21]), 20)

    def test_repeated_concurrent_builds_share_one_cached_space(self):
        provider = MetricProvider(catalog([(0, 0, "#000000"), (1, 0, "#ffffff")]))
        with patch.object(provider, "_xyrgb", wraps=provider._xyrgb) as build:
            with ThreadPoolExecutor(max_workers=4) as pool:
                spaces = list(pool.map(lambda _: provider.get({"metric": "xyrgb"}), range(16)))
        self.assertEqual(build.call_count, 1)
        self.assertTrue(all(space is spaces[0] for space in spaces))

    def test_graph_hausdorff_overlap_and_disconnected_genres(self):
        data = catalog([(index, 0, "#000000") for index in range(6)],
                       near=[(0, 1), (1, 2), (2, 3), (3, 4)])
        space = MetricProvider(data).get({"metric": "graph"})
        self.assertEqual(space.clusters[1], (0, 1, 2))
        self.assertEqual(space.clusters[3], (2, 3, 4))
        self.assertEqual(space.separation(1, 3), 2)
        self.assertEqual(set(space.clusters[1]) & set(space.clusters[3]), {2})
        self.assertEqual(space.separation(0, 4), 3)
        self.assertEqual(space.clusters[5], (5,))
        self.assertEqual(space.distance(0, 5), math.inf)
        self.assertEqual(space.separation(0, 5), math.inf)
        for threshold in (0, 1, 1.5, 2, 3, 4):
            for anchor in range(6):
                expected = [space.separation(anchor, other) >= threshold for other in range(6)]
                np.testing.assert_array_equal(space.compatibility_mask(anchor, threshold), expected)
                self.assertEqual([space.compatible(anchor, other, threshold) for other in range(6)], expected)

    def test_graph_identical_balls_have_zero_hausdorff(self):
        data = catalog([(0, 0, "#000000"), (1, 0, "#ffffff")], near=[(0, 1)])
        space = MetricProvider(data).get({"metric": "graph"})
        self.assertEqual(space.distance(0, 1), 1)
        self.assertEqual(space.separation(0, 1), 0)

    def test_graph_ignores_cluster_size_and_keeps_complete_closed_balls(self):
        data = catalog([(index, 0, "#000000") for index in range(30)],
                       near=[(0, index) for index in range(1, 30)])
        provider = MetricProvider(data)
        original = provider.get({"metric": "graph"})
        self.assertEqual(original.clusters[0], tuple(range(30)))
        self.assertEqual(original.clusters[1], (0, 1))
        for size in (5, 25, None, "ignored", False):
            self.assertIs(provider.get({"metric": "graph", "cluster_size": size}), original)

    def test_graph_or_symmetrizes_directed_neighbors(self):
        data = catalog([(index, 0, "#000000") for index in range(3)])
        data.near = [frozenset([1]), frozenset(), frozenset([1])]
        space = MetricProvider(data).get({"metric": "graph"})
        self.assertEqual(space.clusters, ((0, 1), (0, 1, 2), (1, 2)))
        self.assertEqual(space.distance(0, 2), 2)
        np.testing.assert_array_equal(space.distances, space.distances.T)

    def test_signed_kernel_matches_inverse_with_overlapping_signs(self):
        data = catalog([(index, 0, "#000000") for index in range(4)],
                       near=[(0, 1), (1, 2)], opposite=[(0, 1), (0, 2)])
        lam, eta = 1.7, 0.3
        near = np.array([[0, 1, 0, 0], [1, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 0]])
        opposite = np.array([[0, 1, 1, 0], [1, 0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]])
        laplacian = np.diag(near.sum(axis=1)) - near + lam * (np.diag(opposite.sum(axis=1)) + opposite)
        kernel = np.linalg.inv(laplacian + eta * np.eye(4))
        normalized = kernel / np.sqrt(np.outer(np.diag(kernel), np.diag(kernel)))
        expected = np.sqrt(np.maximum(0, 2 - 2 * normalized))
        np.fill_diagonal(expected, 0)
        provider = MetricProvider(data)
        space = provider.get({"metric": "kernel", "opposition": lam, "regularization": eta})
        np.testing.assert_allclose(space.distances, expected, atol=1e-12)
        np.testing.assert_array_equal(space.distances, space.distances.T)
        self.assertAlmostEqual(space.distance(0, 3), math.sqrt(2))
        other = provider.get({"metric": "kernel", "opposition": 0.1, "regularization": eta})
        self.assertFalse(np.allclose(space.distances, other.distances))
        for left in range(4):
            for middle in range(4):
                for right in range(4):
                    self.assertLessEqual(space.distance(left, right), space.distance(left, middle) + space.distance(middle, right) + 1e-12)

    def test_kernel_overflow_fails_instead_of_returning_nan_clusters(self):
        provider = MetricProvider(catalog([(0, 0, "#000000")]))
        with np.errstate(all="ignore"), self.assertRaises(ArithmeticError):
            provider.get({"metric": "kernel", "opposition": 1, "regularization": 1e-320})

    def test_public_settings_reject_nonfinite_wrong_types_and_boundary_weights(self):
        invalid = [
            None, [], {"metric": []}, {"metric": "unknown"},
            {"count": True}, {"count": 4.0}, {"count": "4"},
            {"alpha": 0}, {"alpha": 1}, {"alpha": "0.8"}, {"alpha": True},
            {"alpha": float("nan")}, {"alpha": float("inf")}, {"alpha": 10 ** 400},
            {"separation": -1}, {"separation": float("nan")}, {"separation": False},
            {"metric": "graph", "separation": 1.5},
            {"metric": "kernel", "separation": 2.1},
            {"metric": "kernel", "opposition": 0},
            {"metric": "kernel", "regularization": False},
            {"metric": "kernel", "regularization": float("inf")},
        ]
        for settings in invalid:
            with self.subTest(settings=settings), self.assertRaises(GameError) as error:
                validate_settings(settings)
            self.assertEqual(error.exception.code, "invalid_settings")


if __name__ == "__main__":
    unittest.main()
