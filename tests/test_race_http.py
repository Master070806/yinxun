"""Race HTTP contracts with real sessions and a small directed neighborhood graph."""

from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from threading import Thread
from types import SimpleNamespace
import unittest

from engine.game import GameService
from serve import Handler


class FakeSpace:
    def __init__(self, clusters):
        self.clusters = tuple(tuple(cluster) for cluster in clusters)

    def reverse_clusters(self, member):
        return tuple(center for center, cluster in enumerate(self.clusters) if member in cluster)


class FakeProvider:
    def __init__(self):
        self.space = FakeSpace(((0, 1, 2, 3, 4), (1, 2, 3, 4, 5), (2, 0, 1, 3, 4),
                                (3, 0, 1, 2, 4), (4, 0, 1, 2, 3), (5, 1, 2, 4, 6),
                                (6, 1, 2, 4, 5)))
        self.requests = []
        self.error = None

    def get(self, settings):
        self.requests.append(dict(settings))
        if self.error:
            raise self.error
        return self.space


def make_catalog(prefix="genre"):
    return SimpleNamespace(genres=[
        {"id": i, "name": f"{prefix} {i}", "color": "#123456", "x": i, "y": i,
         "preview_url": "https://private.invalid/sample", "track_id": "private-track"}
        for i in range(7)
    ])


class RaceHandler(Handler):
    def log_message(self, *args):
        pass


class RaceHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), RaceHandler)
        cls.thread = Thread(target=cls.server.serve_forever,
                            kwargs={"poll_interval": .01}, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def setUp(self):
        self.catalog = make_catalog()
        self.provider = FakeProvider()
        self.game = GameService(self.catalog, self.provider)
        RaceHandler.game_service = self.game
        RaceHandler.race_service = None
        RaceHandler.audio_store = object()

    def request(self, method, path, payload=None, *, raw=None, headers=None):
        headers = dict(headers or {})
        if payload is not None:
            raw = json.dumps(payload).encode()
            headers.setdefault("Content-Type", "application/json")
        connection = HTTPConnection(*self.server.server_address, timeout=5)
        try:
            connection.request(method, path, body=raw, headers=headers)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def start(self, start=0, goal=6, settings=None):
        status, _, body = self.request("POST", "/api/races", {
            "start_id": start, "goal_id": goal,
            "settings": settings or {"metric": "xyrgb", "cluster_size": 5, "alpha": .8},
        })
        self.assertEqual(status, 200, body)
        return json.loads(body)

    def move(self, race, genre_id, **extra):
        return self.request("POST", f"/api/races/{race['id']}/move", {
            "genre_id": genre_id, "revision": race["revision"], **extra,
        })

    def test_start_state_privacy_and_shared_geometry_provider(self):
        race = self.start()
        self.assertEqual(set(race), {"id", "stage", "current", "goal", "cluster", "route", "moves",
                                     "revision", "goal_reachable", "catalog_size", "settings"})
        self.assertEqual(race["stage"], "race")
        self.assertEqual(race["current"]["id"], 0)
        self.assertEqual(race["goal"]["id"], 6)
        self.assertEqual(race["cluster"]["center_id"], 0)
        self.assertEqual({g["id"] for g in race["cluster"]["genres"]}, {0, 1, 2, 3, 4})
        self.assertEqual(race["moves"], 0)
        self.assertEqual(race["revision"], 0)
        self.assertEqual(race["catalog_size"], 7)
        self.assertTrue(race["goal_reachable"])
        for genre in [race["current"], race["goal"], *race["cluster"]["genres"]]:
            self.assertEqual(set(genre), {"id", "name", "color"})
        for secret in ('"x"', '"y"', "private", "preview_url", "track_id", "source_url", "distances"):
            self.assertNotIn(secret, json.dumps(race))
        self.assertIs(RaceHandler.race_service.catalog, self.catalog)
        self.assertIs(RaceHandler.race_service.provider, self.provider)
        self.assertEqual(len(self.provider.requests), 1)
        self.assertEqual(self.game._sessions, {})

    def test_valid_moves_recenter_increment_and_finish_at_fixed_goal(self):
        race = self.start()
        for count, genre_id in enumerate((1, 5, 6), start=1):
            status, _, body = self.move(race, genre_id)
            self.assertEqual(status, 200, body)
            race = json.loads(body)
            self.assertEqual(race["current"]["id"], genre_id)
            self.assertEqual(race["cluster"]["center_id"], genre_id)
            self.assertEqual(race["moves"], count)
            self.assertEqual(race["revision"], count)
            self.assertEqual(race["goal"]["id"], 6)
            self.assertEqual(len(race["route"]), count + 1)
        self.assertEqual(race["stage"], "win")
        status, _, body = self.move(race, 5)
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(body)["code"], "invalid_stage")
        status, _, body = self.request("GET", f"/api/races/{race['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), race)

    def test_get_and_head_are_read_only_and_uncached(self):
        race = self.start()
        path = f"/api/races/{race['id']}"
        status, headers, body = self.request("GET", path)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), race)
        self.assertEqual(headers["Cache-Control"], "no-store")
        status, head_headers, head_body = self.request("HEAD", path)
        self.assertEqual(status, 200)
        self.assertEqual(head_body, b"")
        self.assertEqual(head_headers["Content-Length"], str(len(body)))
        self.assertEqual(json.loads(self.request("GET", path)[2]), race)
        self.assertEqual(len(self.provider.requests), 1)

    def test_invalid_member_self_and_types_leave_state_unchanged(self):
        race = self.start()
        for genre_id in (6, 99, 0, "1", True, 1.0, None):
            with self.subTest(genre_id=genre_id):
                status, _, body = self.move(race, genre_id)
                self.assertEqual(status, 400)
                self.assertEqual(json.loads(body)["code"], "invalid_move")
        for revision in (-1, True, "0", 0.0, None):
            with self.subTest(revision=revision):
                status, _, body = self.move(race, 1, revision=revision)
                self.assertEqual(status, 400)
                self.assertEqual(json.loads(body)["code"], "invalid_revision")
        self.assertEqual(json.loads(self.request("GET", f"/api/races/{race['id']}")[2]), race)

    def test_forged_goal_stage_and_move_count_cannot_change_server_state(self):
        race = self.start()
        status, _, body = self.move(race, 1, goal_id=1, stage="win", moves=100,
                                    current_id=6, route=[0, 6], settings={"metric": "graph"})
        self.assertEqual(status, 200)
        moved = json.loads(body)
        self.assertEqual(moved["stage"], "race")
        self.assertEqual(moved["current"]["id"], 1)
        self.assertEqual(moved["goal"]["id"], 6)
        self.assertEqual(moved["moves"], 1)
        self.assertEqual(moved["settings"], race["settings"])
        self.assertEqual(len(moved["route"]), 2)

    def test_duplicate_move_is_a_conflict_with_current_snapshot(self):
        race = self.start()
        status, _, body = self.move(race, 1)
        self.assertEqual(status, 200)
        moved = json.loads(body)
        status, headers, body = self.move(race, 1)
        self.assertEqual(status, 409)
        error = json.loads(body)
        self.assertEqual(error["code"], "stale_move")
        self.assertEqual(error["race"], moved)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(json.loads(self.request("GET", f"/api/races/{race['id']}")[2]), moved)

    def test_concurrent_duplicate_moves_increment_counter_once(self):
        race = self.start()
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: self.move(race, 1), range(2)))
        self.assertEqual(sorted(status for status, _, _ in outcomes), [200, 409])
        current = json.loads(self.request("GET", f"/api/races/{race['id']}")[2])
        self.assertEqual(current["moves"], 1)
        self.assertEqual(current["revision"], 1)
        self.assertEqual(len(current["route"]), 2)

    def test_unknown_races_and_invalid_start_goal_ids(self):
        for method in ("GET", "HEAD"):
            status, _, body = self.request(method, "/api/races/not-real")
            self.assertEqual(status, 404)
            if method == "GET":
                self.assertEqual(json.loads(body)["code"], "race_not_found")
            else:
                self.assertEqual(body, b"")
        status, _, body = self.request("POST", "/api/races/not-real/move", {"genre_id": 1, "revision": 0})
        self.assertEqual(status, 404)
        self.assertEqual(json.loads(body)["code"], "race_not_found")
        for value in (-1, 99, "0", True, 0.0, None):
            for field in ("start_id", "goal_id"):
                with self.subTest(field=field, value=value):
                    payload = {"start_id": 0, "goal_id": 6, "settings": {"metric": "graph"}, field: value}
                    status, _, body = self.request("POST", "/api/races", payload)
                    self.assertEqual(status, 400)
                    self.assertEqual(json.loads(body)["code"], "invalid_genre")

    def test_unreachable_goal_is_reported_without_inventing_a_path(self):
        self.provider.space = FakeSpace(((0, 1), (1, 0), (2,), (3,), (4,), (5, 6), (6, 5)))
        status, _, body = self.request("POST", "/api/races", {
            "start_id": 0, "goal_id": 6, "settings": {"metric": "graph"},
        })
        self.assertEqual(status, 422)
        self.assertEqual(json.loads(body)["code"], "unreachable_goal")

    def test_starting_at_goal_is_an_immediate_zero_move_win(self):
        race = self.start(start=3, goal=3)
        self.assertEqual(race["stage"], "win")
        self.assertEqual(race["moves"], 0)
        self.assertEqual(race["revision"], 0)
        self.assertEqual(len(race["route"]), 1)
        self.assertEqual(self.move(race, 1)[0], 409)

    def test_write_guards_cover_both_race_routes(self):
        race = self.start()
        for path, payload in (("/api/races", {"start_id": 0, "goal_id": 6, "settings": {"metric": "graph"}}),
                              (f"/api/races/{race['id']}/move", {"genre_id": 1, "revision": 0})):
            for headers in ({"Origin": "https://unrelated.invalid"}, {"Sec-Fetch-Site": "cross-site"}):
                self.assertEqual(self.request("POST", path, payload, headers=headers)[0], 403)
            for raw in (b"{", b"[]", b"null", b"x" * 16385):
                self.assertEqual(self.request("POST", path, raw=raw,
                                              headers={"Content-Type": "application/json"})[0], 400)
            self.assertEqual(self.request("POST", path, raw=b"{}",
                                          headers={"Content-Type": "text/plain"})[0], 400)
        self.assertEqual(json.loads(self.request("GET", f"/api/races/{race['id']}")[2]), race)

    def test_catalog_replacement_discards_stale_race_service_and_reuses_new_provider(self):
        old_race = self.start()
        previous_service = RaceHandler.race_service
        replacement = make_catalog("replacement")
        replacement_provider = FakeProvider()
        RaceHandler.game_service = GameService(replacement, replacement_provider)
        self.assertEqual(self.request("GET", f"/api/races/{old_race['id']}")[0], 404)
        race = self.start()
        self.assertIsNot(RaceHandler.race_service, previous_service)
        self.assertIs(RaceHandler.race_service.catalog, replacement)
        self.assertIs(RaceHandler.race_service.provider, replacement_provider)
        self.assertEqual(race["current"]["name"], "replacement 0")
        self.assertEqual(len(replacement_provider.requests), 1)

    def test_internal_failures_do_not_expose_private_sources(self):
        self.provider.error = RuntimeError("private source path /Users/example and track_id")
        status, _, body = self.request("POST", "/api/races", {
            "start_id": 0, "goal_id": 6, "settings": {"metric": "graph"},
        })
        self.assertEqual(status, 503)
        for secret in ("private", "/Users/", "track_id", "RuntimeError"):
            self.assertNotIn(secret, body.decode())


if __name__ == "__main__":
    unittest.main()
