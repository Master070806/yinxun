"""Multiplayer API contracts over real loopback requests and isolated room services."""

from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from threading import Thread
import unittest
from unittest.mock import patch

from engine.game import GameService
from serve import Handler
from test_multiplayer import FakeProvider, SAMPLE, make_catalog


class FakeAudioStore:
    data = b"\xff\xfb" + bytes(range(32))

    def __init__(self):
        self.tracks = []

    def get(self, track):
        self.tracks.append(dict(track))
        return self.data


class MultiplayerHandler(Handler):
    def log_message(self, *args):
        pass


class MultiplayerHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), MultiplayerHandler)
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
        self.audio = FakeAudioStore()
        MultiplayerHandler.game_service = self.game
        MultiplayerHandler.race_service = None
        MultiplayerHandler.multiplayer_service = None
        MultiplayerHandler.audio_store = self.audio
        for name, kwargs in (("engine.game.sample", {"return_value": SAMPLE}),
                             ("engine.game.secrets.randbelow", {"return_value": 0})):
            mocked = patch(name, **kwargs)
            mocked.start()
            self.addCleanup(mocked.stop)

    def request(self, method, path, payload=None, *, token=None, raw=None, headers=None):
        headers = dict(headers or {})
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
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

    def create(self, mode="guessr", **extra):
        status, headers, body = self.request("POST", "/api/rooms", {
            "mode": mode, "name": "Host", "rounds": 1,
            "settings": {"count": 3, "cluster_size": 5},
            "start_id": 0, "goal_id": 6, **extra,
        })
        self.assertEqual(status, 200, body)
        self.assertEqual(headers["Cache-Control"], "no-store")
        return json.loads(body)

    def join(self, host):
        status, _, body = self.request("POST", f"/api/rooms/{host['room']['id']}/join", {"name": "Guest"})
        self.assertEqual(status, 200, body)
        return json.loads(body)

    def action(self, player, action, **payload):
        return self.request("POST", f"/api/rooms/{player['room']['id']}/{action}", payload,
                            token=player["token"])

    def ok_action(self, player, action, **payload):
        status, _, body = self.action(player, action, **payload)
        self.assertEqual(status, 200, body)
        return json.loads(body)

    def get(self, player):
        status, _, body = self.request("GET", f"/api/rooms/{player['room']['id']}", token=player["token"])
        self.assertEqual(status, 200, body)
        return json.loads(body)

    def start(self, mode="guessr"):
        host = self.create(mode)
        guest = self.join(host)
        return host, guest, self.ok_action(host, "start")

    @staticmethod
    def correct_cluster(room):
        return next(c["id"] for c in room["game"]["clusters"] if any(g["id"] == 0 for g in c["genres"]))

    def test_invite_lobby_preview_and_join_issue_separate_private_credentials(self):
        host = self.create(rounds=4)
        path = f"/api/rooms/{host['room']['id']}"
        status, headers, body = self.request("GET", path)
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(json.loads(body)["stage"], "lobby")
        self.assertNotIn(host["token"], body.decode())
        self.assertNotIn("game", json.loads(body))
        guest = self.join(host)
        self.assertNotEqual(host["token"], guest["token"])
        self.assertEqual(len(self.get(host)["players"]), 2)
        self.assertEqual(self.get(host)["self_id"], host["player_id"])
        self.assertEqual(self.get(guest)["self_id"], guest["player_id"])
        for member in (host, guest):
            encoded = json.dumps(self.get(member))
            self.assertNotIn(host["token"], encoded)
            self.assertNotIn(guest["token"], encoded)

    def test_authenticated_get_and_head_are_uncached_read_only_and_refreshable(self):
        host, _, room = self.start()
        path = f"/api/rooms/{room['id']}"
        status, headers, body = self.request("GET", path, token=host["token"])
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), room)
        self.assertEqual(headers["Cache-Control"], "no-store")
        status, head_headers, head_body = self.request("HEAD", path, token=host["token"])
        self.assertEqual(status, 200)
        self.assertEqual(head_body, b"")
        self.assertEqual(head_headers["Content-Length"], str(len(body)))
        self.assertEqual(self.get(host), room)
        for secret in ('"target"', '"center"', "private", "track_id", "source_url", "everynoise.com"):
            self.assertNotIn(secret, body.decode())

    def test_only_member_bearer_token_authorizes_actions_and_private_snapshot(self):
        host, guest, room = self.start()
        outsider = self.create()
        path = f"/api/rooms/{room['id']}"
        payload = {"cluster_id": self.correct_cluster(room), "round_number": 1,
                   "token": host["token"], "player_id": host["player_id"]}
        for token in ("wrong-token", outsider["token"]):
            with self.subTest(token=token):
                self.assertIn(self.request("GET", path, token=token)[0], (401, 403))
                self.assertIn(self.request("POST", f"{path}/cluster", payload, token=token)[0], (401, 403))
        for endpoint in (path, f"{path}?token={host['token']}"):
            status, _, body = self.request("GET", endpoint)
            self.assertEqual(status, 200)
            preview = json.loads(body)
            self.assertIsNone(preview["self_id"])
            for key in ("game", "race", "result", "routes"):
                self.assertNotIn(key, preview)
        self.assertIn(self.request("POST", f"{path}/cluster", payload)[0], (401, 403))
        self.assertIn(self.request("POST", f"{path}/cluster?token={host['token']}", payload)[0], (401, 403))
        self.assertEqual(self.get(host), room)
        self.assertEqual(self.action(guest, "start")[0], 403)
        self.assertEqual(self.request("POST", f"{path}/join", {"name": "Late"})[0], 409)

    def test_audio_auth_stage_entitlement_and_byte_ranges(self):
        host, guest, room = self.start()
        base = f"/api/rooms/{room['id']}/audio/1"
        first = f"{base}/clue/1"
        second = f"{base}/clue/2"
        self.assertIn(self.request("GET", first)[0], (401, 403))
        self.assertIn(self.request("GET", first + "?token=wrong")[0], (401, 403))
        self.assertEqual(self.audio.tracks, [])
        status, headers, body = self.request("GET", first + f"?token={host['token']}")
        self.assertEqual(status, 200)
        self.assertEqual(body, self.audio.data)
        self.assertEqual(headers["Content-Type"], "audio/mpeg")
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertNotIn("Location", headers)
        self.assertNotIn("private", str(headers))
        status, headers, body = self.request("GET", first, token=guest["token"], headers={"Range": "bytes=2-6"})
        self.assertEqual((status, body), (206, self.audio.data[2:7]))
        self.assertEqual(headers["Content-Range"], f"bytes 2-6/{len(self.audio.data)}")
        status, headers, body = self.request("HEAD", first + f"?token={host['token']}", headers={"Range": "bytes=2-6"})
        self.assertEqual((status, body, headers["Content-Length"]), (206, b"", "5"))
        self.assertIn(self.request("GET", second, token=host["token"])[0], (403, 409))
        correct = self.correct_cluster(room)
        wrong = next(c["id"] for c in room["game"]["clusters"] if c["id"] != correct)
        self.ok_action(host, "cluster", cluster_id=correct, round_number=1)
        self.assertIn(self.request("GET", second, token=host["token"])[0], (403, 409))
        self.ok_action(guest, "cluster", cluster_id=wrong, round_number=1)
        self.assertEqual(self.request("GET", second, token=host["token"])[0], 200)
        self.assertEqual(self.audio.tracks[-1]["position"], 2)
        self.assertIn(self.request("GET", second, token=guest["token"])[0], (403, 409))
        self.assertIn(self.request("GET", base + "/candidate/0", token=guest["token"])[0], (403, 409))
        self.assertEqual(self.request("GET", base + "/candidate/0", token=host["token"])[0], 200)
        self.assertNotIn(self.audio.tracks[-1]["position"], (1, 2))
        self.assertEqual(self.request("GET", f"/api/rooms/{room['id']}/audio/2/clue/1", token=host["token"])[0], 409)

    def test_guessr_http_round_waits_scores_and_finishes_for_all_members(self):
        host, guest, room = self.start()
        cluster_id = self.correct_cluster(room)
        room = self.ok_action(host, "cluster", cluster_id=cluster_id, round_number=1)
        self.assertEqual(room["stage"], "cluster")
        room = self.ok_action(guest, "cluster", cluster_id=cluster_id, round_number=1)
        self.assertEqual(room["stage"], "genre")
        room = self.ok_action(host, "genre", genre_id=1, round_number=1,
                              score=999999, target=1, player_id=guest["player_id"])
        self.assertEqual(room["stage"], "genre")
        self.assertNotIn("result", room)
        room = self.ok_action(guest, "genre", genre_id=0, round_number=1)
        self.assertEqual(room["stage"], "round_result")
        scores = {p["id"]: p["score"] for p in room["players"]}
        self.assertEqual(scores, {host["player_id"]: 500, guest["player_id"]: 1000})
        self.assertEqual(room["result"]["target"]["id"], 0)
        self.assertEqual(self.ok_action(host, "ready", round_number=1)["stage"], "round_result")
        room = self.ok_action(guest, "ready", round_number=1)
        self.assertEqual(room["stage"], "finished")
        self.assertEqual(room["winner_ids"], [guest["player_id"]])
        self.assertEqual(self.get(host)["winner_ids"], room["winner_ids"])

    def test_race_first_winner_stops_http_moves_and_reports_every_trace(self):
        host, guest, room = self.start("race")
        self.assertEqual(room["race"]["current"]["id"], 0)
        self.assertEqual(self.get(guest)["race"]["goal"]["id"], 6)
        self.ok_action(guest, "move", genre_id=2, revision=0)
        for revision, genre_id in enumerate((1, 5, 6)):
            room = self.ok_action(host, "move", genre_id=genre_id, revision=revision)
        self.assertEqual(room["stage"], "finished")
        self.assertEqual(room["winner_ids"], [host["player_id"]])
        routes = {p["id"]: [g["id"] for g in p["route"]] for p in room["routes"]}
        self.assertEqual(routes, {host["player_id"]: [0, 1, 5, 6], guest["player_id"]: [0, 2]})
        frozen = self.get(guest)
        self.assertEqual(self.action(guest, "move", genre_id=1, revision=1)[0], 409)
        self.assertEqual(self.get(guest), frozen)

    def test_concurrent_winning_http_requests_commit_only_first_finish(self):
        host, guest, _ = self.start("race")
        for player in (host, guest):
            self.ok_action(player, "move", genre_id=1, revision=0)
            self.ok_action(player, "move", genre_id=5, revision=1)
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda p: self.action(p, "move", genre_id=6, revision=2), (host, guest)))
        self.assertEqual(sorted(outcome[0] for outcome in outcomes), [200, 409])
        room = self.get(host)
        self.assertEqual(len(room["winner_ids"]), 1)
        self.assertCountEqual([len(p["route"]) for p in room["routes"]], [3, 4])

    def test_host_can_remove_an_unresponsive_member_to_unblock_selection(self):
        host, guest, room = self.start()
        self.ok_action(host, "cluster", cluster_id=self.correct_cluster(room), round_number=1)
        self.assertEqual(self.action(guest, "remove", player_id=host["player_id"])[0], 403)
        room = self.ok_action(host, "remove", player_id=guest["player_id"])
        self.assertEqual(room["stage"], "genre")
        self.assertTrue(next(p for p in room["players"] if p["id"] == guest["player_id"])["left"])

    def test_write_guards_cover_creation_join_and_authenticated_actions(self):
        host = self.create()
        path = f"/api/rooms/{host['room']['id']}"
        for endpoint, payload in (("/api/rooms", {"mode": "guessr", "name": "Other"}),
                                  (path + "/join", {"name": "Guest"}),
                                  (path + "/start", {})):
            for headers in ({"Origin": "https://unrelated.invalid"}, {"Sec-Fetch-Site": "cross-site"}):
                with self.subTest(endpoint=endpoint, headers=headers):
                    self.assertEqual(self.request("POST", endpoint, payload, token=host["token"], headers=headers)[0], 403)
            for raw in (b"{", b"[]", b"null", b"x" * 16385):
                with self.subTest(endpoint=endpoint, raw=raw[:8]):
                    self.assertEqual(self.request("POST", endpoint, raw=raw, token=host["token"],
                                                  headers={"Content-Type": "application/json"})[0], 400)
            self.assertEqual(self.request("POST", endpoint, raw=b"{}", token=host["token"],
                                          headers={"Content-Type": "text/plain"})[0], 400)
        self.assertEqual(self.get(host)["stage"], "lobby")
        self.assertEqual(len(self.get(host)["players"]), 1)

    def test_same_host_https_origin_allows_a_reverse_proxy_invitation(self):
        host = self.create()
        host_header = f"127.0.0.1:{self.server.server_port}"
        status, _, body = self.request("POST", f"/api/rooms/{host['room']['id']}/join", {"name": "Proxy guest"},
                                      headers={"Origin": f"https://{host_header}"})
        self.assertEqual(status, 200, body)

    def test_host_lobby_configuration_is_shared_and_cannot_change_after_start(self):
        host = self.create()
        guest = self.join(host)
        self.assertEqual(self.action(guest, "configure", rounds=3)[0], 403)
        room = self.ok_action(host, "configure", rounds=3,
                              settings={"metric": "xyrgb", "count": 3, "cluster_size": 5, "alpha": .4})
        self.assertEqual(room["total_rounds"], 3)
        self.assertEqual(self.get(guest)["settings"]["alpha"], .4)
        self.ok_action(host, "start")
        self.assertEqual(self.action(host, "configure", rounds=1)[0], 409)

    def test_unknown_rooms_and_malformed_audio_paths_do_not_expose_private_sources(self):
        for method, path, payload in (("GET", "/api/rooms/missing", None),
                                      ("POST", "/api/rooms/missing/join", {"name": "Guest"}),
                                      ("POST", "/api/rooms/missing/start", {}),
                                      ("GET", "/api/rooms/missing/audio/1/clue/1", None)):
            with self.subTest(path=path):
                status, _, body = self.request(method, path, payload, token="unknown")
                self.assertEqual(status, 404, body)
                self.assertNotIn("private", body.decode())
        host, _, room = self.start()
        for tail in ("0/clue/1", "1/clue/3", "one/clue/1", "1/other/0", "1/candidate/999"):
            status, _, body = self.request("GET", f"/api/rooms/{room['id']}/audio/{tail}", token=host["token"])
            self.assertIn(status, (400, 403, 404, 409), body)
        self.assertEqual(self.audio.tracks, [])

    def test_catalog_replacement_does_not_keep_stale_rooms_or_credentials(self):
        host = self.create()
        old_service = MultiplayerHandler.multiplayer_service
        replacement = make_catalog()
        replacement.genres[0]["name"] = "replacement genre"
        new_provider = FakeProvider()
        MultiplayerHandler.game_service = GameService(replacement, new_provider)
        status, _, _ = self.request("GET", f"/api/rooms/{host['room']['id']}", token=host["token"])
        self.assertEqual(status, 404)
        created = self.create("race")
        self.assertIsNot(MultiplayerHandler.multiplayer_service, old_service)
        self.assertIs(MultiplayerHandler.race_service.provider, new_provider)
        self.assertEqual(created["room"]["race"]["start"]["name"], "replacement genre")

    def test_internal_preparation_errors_are_safe_and_leave_lobby_retryable(self):
        host = self.create()
        self.join(host)
        with patch("engine.game.sample", side_effect=RuntimeError("private source /Users/example track_id")):
            status, _, body = self.action(host, "start")
        self.assertGreaterEqual(status, 400)
        for secret in ("private", "/Users/", "track_id", "RuntimeError"):
            self.assertNotIn(secret, body.decode())
        self.assertEqual(self.get(host)["stage"], "lobby")
        self.assertEqual(self.ok_action(host, "start")["stage"], "cluster")


if __name__ == "__main__":
    unittest.main()
