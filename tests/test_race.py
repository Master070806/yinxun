"""Genrerace topology, immutable session state, and move validation."""

from collections import deque
import gc
from types import SimpleNamespace
import unittest
import weakref

import numpy as np

from engine.game import GameError
from engine.metrics import MetricProvider
from engine.race import RaceService, validate_race_settings


CLUSTERS = ((0, 1, 4), (1, 0, 2), (2, 3), (3,), (4, 5), (5, 4),
            (6, 0), (7,), (8, 6), (9, 8))


def catalog(size=10, near=None):
    return SimpleNamespace(
        genres=[{"id": i, "name": f"genre {i}", "color": "#123456", "x": i, "y": 0}
                for i in range(size)],
        near=near if near is not None else [frozenset() for _ in range(size)],
        opposite=[frozenset() for _ in range(size)],
        tracks=lambda *_: (_ for _ in ()).throw(AssertionError("Races must not filter on audio.")),
    )


class FakeSpace:
    def __init__(self, clusters=CLUSTERS):
        self.clusters = clusters
        self.distances = np.zeros((len(clusters), len(clusters)))
        self.reverse = tuple(tuple(center for center, members in enumerate(clusters) if node in members)
                             for node in range(len(clusters)))

    def reverse_clusters(self, node):
        return self.reverse[node]


class FakeProvider:
    def __init__(self, clusters=CLUSTERS):
        self.space = FakeSpace(clusters)
        self.requests = []

    def get(self, settings):
        self.requests.append(dict(settings))
        return self.space


def path_between(clusters, start, goal):
    pending = deque([start])
    parent = {start: None}
    while pending:
        node = pending.popleft()
        if node == goal:
            path = [node]
            while parent[node] is not None:
                node = parent[node]
                path.append(node)
            return path[::-1]
        for neighbor in clusters[node]:
            if neighbor not in parent:
                parent[neighbor] = node
                pending.append(neighbor)
    raise AssertionError("Fixture route is unreachable.")


class RaceTests(unittest.TestCase):
    def setUp(self):
        self.catalog = catalog()
        self.provider = FakeProvider()
        self.service = RaceService(self.catalog, self.provider)

    def start(self, start=0, goal=3, settings=None):
        return self.service.start(start, goal, {"metric": "xyrgb"} if settings is None else settings)

    def test_full_catalog_high_ids_are_available_later_without_injecting_goal(self):
        race = self.start(9, 3)
        self.assertEqual(race["catalog_size"], 10)
        self.assertEqual([genre["id"] for genre in race["cluster"]["genres"]], [9, 8])
        self.assertNotIn(3, [genre["id"] for genre in race["cluster"]["genres"]])
        self.assertEqual(race["route"], [race["current"]])
        for index, destination in enumerate((8, 6, 0, 1, 2, 3)):
            race = self.service.move(race["id"], destination, race["revision"])
            self.assertEqual(race["current"]["id"], destination)
            self.assertEqual((race["moves"], race["revision"]), (index + 1, index + 1))
            if destination != 3:
                self.assertEqual([genre["id"] for genre in race["cluster"]["genres"]],
                                 list(CLUSTERS[destination]))
        self.assertEqual(race["stage"], "win")
        self.assertEqual(race["cluster"], {"center_id": 3, "genres": []})
        self.assertEqual([genre["id"] for genre in race["route"]], [9, 8, 6, 0, 1, 2, 3])
        self.assertEqual(len(self.provider.requests), 1)

    def test_real_nearest_k_neighborhoods_use_the_whole_source(self):
        data = catalog(30)
        provider = MetricProvider(data)
        service = RaceService(data, provider)
        settings = {"metric": "xyrgb", "alpha": .8, "cluster_size": 5}
        space = provider.get(settings)
        route = path_between(space.clusters, 0, 29)
        self.assertGreater(len(route), 2)
        race = service.start(0, 29, settings)
        for current, destination in zip(route, route[1:]):
            self.assertEqual(race["current"]["id"], current)
            self.assertEqual([genre["id"] for genre in race["cluster"]["genres"]],
                             list(space.clusters[current]))
            self.assertEqual(len(race["cluster"]["genres"]), 5)
            race = service.move(race["id"], destination, race["revision"])
        self.assertEqual(race["stage"], "win")
        self.assertEqual(race["goal"]["id"], 29)

    def test_graph_keeps_entire_unit_ball_and_kernel_keeps_selected_nearest_k(self):
        size = 30
        near = [frozenset(range(1, size))] + [frozenset({0}) for _ in range(1, size)]
        data = catalog(size, near)
        provider = MetricProvider(data)
        service = RaceService(data, provider)
        graph = service.start(0, 29, {"metric": "graph", "cluster_size": 5})
        self.assertEqual(len(graph["cluster"]["genres"]), 30)
        self.assertNotIn("cluster_size", graph["settings"])
        self.assertEqual(graph["stage"], "race")  # Merely showing the destination is not a win.
        self.assertEqual(service.move(graph["id"], 29, 0)["stage"], "win")
        settings = {"metric": "kernel", "cluster_size": 5, "opposition": 1, "regularization": .1}
        space = provider.get(settings)
        goal = next(node for node in space.clusters[29] if node != 29)
        kernel = service.start(29, goal, settings)
        self.assertEqual([genre["id"] for genre in kernel["cluster"]["genres"]], list(space.clusters[29]))
        self.assertEqual(len(kernel["cluster"]["genres"]), 5)

    def test_directed_reachability_rejects_unreachable_starts_without_mutation(self):
        # 6 -> 0 -> 1 -> 2 -> 3 exists, but 3 cannot return to 6.
        self.assertTrue(self.start(6, 3)["goal_reachable"])
        for start, goal in ((3, 6), (7, 3), (4, 3)):
            with self.subTest(start=start, goal=goal), self.assertRaises(GameError) as error:
                self.start(start, goal)
            self.assertEqual((error.exception.status, error.exception.code), (422, "unreachable_goal"))
        self.assertEqual(len(self.service._sessions), 1)

    def test_legal_directed_dead_end_is_allowed_without_pruning_or_resetting(self):
        race = self.start()
        self.assertIn(4, [genre["id"] for genre in race["cluster"]["genres"]])
        trapped = self.service.move(race["id"], 4, 0)
        self.assertFalse(trapped["goal_reachable"])
        self.assertEqual(trapped["stage"], "race")
        self.assertEqual(trapped["goal"]["id"], 3)
        self.assertEqual([genre["id"] for genre in trapped["cluster"]["genres"]], [4, 5])
        trapped = self.service.move(race["id"], 5, 1)
        self.assertEqual([genre["id"] for genre in trapped["route"]], [0, 4, 5])
        self.assertFalse(trapped["goal_reachable"])

    def test_revisits_and_backtracking_count_only_when_actual_edges_exist(self):
        race = self.start()
        race = self.service.move(race["id"], 1, 0)
        race = self.service.move(race["id"], 0, 1)
        self.assertEqual([genre["id"] for genre in race["route"]], [0, 1, 0])
        self.assertEqual(race["moves"], 2)

    def test_settings_and_snapshot_mutations_cannot_change_the_race(self):
        settings = {"metric": "xyrgb", "alpha": .4, "cluster_size": 5,
                    "count": "unused", "separation": "unused"}
        race = self.start(settings=settings)
        self.assertEqual(race["settings"], {"metric": "xyrgb", "alpha": .4, "cluster_size": 5})
        settings.update(metric="graph", alpha=.9, cluster_size=25)
        race["settings"]["alpha"] = .1
        race["cluster"]["genres"][0]["name"] = "tampered"
        race["route"].clear()
        actual = self.service.get(race["id"])
        self.assertEqual(actual["settings"]["alpha"], .4)
        self.assertEqual(actual["route"][0]["name"], "genre 0")
        self.assertEqual(actual["cluster"]["genres"][0]["name"], "genre 0")
        self.assertEqual(self.service.get(race["id"]), actual)
        self.assertEqual(len(self.provider.requests), 1)

    def test_invalid_ids_parameters_and_noncontiguous_catalog_are_rejected(self):
        for bad_id in (True, 1.0, "1", [], -1, 10, None):
            for pair in ((bad_id, 3), (0, bad_id)):
                with self.subTest(pair=pair), self.assertRaises(GameError) as error:
                    self.start(*pair)
                self.assertEqual(error.exception.code, "invalid_genre")
        for settings in (None, [], {"metric": "unknown"}, {"alpha": 0}, {"alpha": 1},
                         {"alpha": float("nan")}, {"cluster_size": True}, {"cluster_size": 5.0},
                         {"cluster_size": 4}, {"cluster_size": 26},
                         {"metric": "kernel", "opposition": 0},
                         {"metric": "kernel", "regularization": float("inf")}):
            with self.subTest(settings=settings), self.assertRaises(GameError):
                self.service.start(0, 3, settings)
        self.assertEqual(self.provider.requests, [])
        self.assertEqual(validate_race_settings({})["cluster_size"], 12)
        self.assertEqual(validate_race_settings({"metric": "graph", "cluster_size": "unused"}),
                         {"metric": "graph"})
        for ids in ([0, 0], [0, 2], [1, 0], [False, 1]):
            broken = catalog(2)
            for genre, genre_id in zip(broken.genres, ids):
                genre["id"] = genre_id
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                RaceService(broken, self.provider)

    def test_partial_or_invalid_metric_universe_is_not_used(self):
        for clusters in (CLUSTERS[:-1], ((0, 99), *CLUSTERS[1:]), ((1,), *CLUSTERS[1:])):
            with self.subTest(clusters=clusters):
                service = RaceService(self.catalog, FakeProvider(clusters))
                with self.assertRaises(GameError) as error:
                    service.start(0, 3, {})
                self.assertEqual((error.exception.status, error.exception.code), (503, "geometry_unavailable"))
                self.assertEqual(service._sessions, {})

    def test_invalid_moves_and_revisions_do_not_consume_a_move(self):
        race = self.start()
        for destination in (0, 3, True, 1.0, "1", [], -1, 100):
            with self.subTest(destination=destination), self.assertRaises(GameError) as error:
                self.service.move(race["id"], destination, 0)
            self.assertEqual(error.exception.code, "invalid_move")
            self.assertEqual(self.service.get(race["id"]), race)
        for revision in (True, 0.0, "0", -1, None):
            with self.subTest(revision=revision), self.assertRaises(GameError) as error:
                self.service.move(race["id"], 1, revision)
            self.assertEqual(error.exception.code, "invalid_revision")
        self.assertEqual(self.service.get(race["id"]), race)

    def test_stale_moves_return_current_snapshot_without_appending(self):
        race = self.start()
        current = self.service.move(race["id"], 1, 0)
        for revision in (0, 100):
            with self.subTest(revision=revision), self.assertRaises(GameError) as error:
                self.service.move(race["id"], 2, revision)
            self.assertEqual((error.exception.status, error.exception.code), (409, "stale_move"))
            self.assertEqual(error.exception.payload["race"], current)
        self.assertEqual(self.service.get(race["id"])["moves"], 1)

    def test_start_equals_goal_wins_without_moves_and_finished_moves_are_rejected(self):
        race = self.start(7, 7)
        self.assertEqual((race["stage"], race["moves"], race["revision"]), ("win", 0, 0))
        self.assertEqual(race["cluster"], {"center_id": 7, "genres": []})
        self.assertTrue(race["goal_reachable"])
        with self.assertRaises(GameError) as error:
            self.service.move(race["id"], 7, 0)
        self.assertEqual((error.exception.status, error.exception.code), (409, "invalid_stage"))
        self.assertEqual(self.service.get(race["id"]), race)

    def test_expiry_and_session_capacity_do_not_evict_active_races(self):
        self.service.max_sessions = 1
        race = self.start()
        with self.assertRaises(GameError) as error:
            self.start()
        self.assertEqual(error.exception.code, "session_limit")
        self.assertEqual(self.service.get(race["id"]), race)
        self.service._sessions[race["id"]].expires = 0
        with self.assertRaises(GameError) as error:
            self.service.get(race["id"])
        self.assertEqual((error.exception.status, error.exception.code), (404, "race_not_found"))
        won = self.start(3, 3)
        self.start()
        with self.assertRaises(GameError):
            self.service.get(won["id"])

    def test_sessions_do_not_retain_metric_spaces_or_dense_matrices(self):
        space_refs, matrix_refs = [], []
        class EphemeralProvider:
            def get(self, settings):
                space = FakeSpace()
                space_refs.append(weakref.ref(space))
                matrix_refs.append(weakref.ref(space.distances))
                return space
        service = RaceService(self.catalog, EphemeralProvider())
        race = service.start(0, 3, {})
        gc.collect()
        self.assertIsNone(space_refs[0]())
        self.assertIsNone(matrix_refs[0]())
        session = service._sessions[race["id"]]
        self.assertIsInstance(session.clusters, tuple)
        self.assertTrue(all(isinstance(row, tuple) for row in session.clusters))
        self.assertEqual(service.move(race["id"], 1, 0)["current"]["id"], 1)


if __name__ == "__main__":
    unittest.main()
