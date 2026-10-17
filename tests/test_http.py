"""Real loopback HTTP routes with tiny in-memory game and media dependencies."""

from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from threading import Thread
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from engine.audio import AudioError
from engine.game import GameService
from engine.sampling import SamplingError, SamplingResult
from serve import Handler


class FakeAudioStore:
    data = b"\xff\xfb" + bytes(range(32))

    def __init__(self):
        self.tracks = []
        self.error = None

    def get(self, track):
        self.tracks.append(track)
        if self.error:
            raise self.error
        return self.data


class QuietHandler(Handler):
    def log_message(self, *args):
        pass


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
        cls.thread = Thread(target=cls.server.serve_forever,
                            kwargs={"poll_interval": .01}, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def setUp(self):
        def track(target, position):
            return {"position": position,
                    "preview_url": f"https://private.invalid/{target}/{position}",
                    "track_id": f"private-track-{target}-{position}",
                    "source_url": "private-genre-map"}

        def samples(target):
            if target == 1:
                # Both clues reappear under another candidate: one by ID and
                # one by URL with a changed signature/default port/fragment.
                return [
                    {**track(0, 1), "preview_url": "https://private.invalid/reissue/1?token=other"},
                    {**track(0, 2), "track_id": "different-id-for-clue-two",
                     "preview_url": "https://private.invalid:443/0/2?token=other#fragment"},
                    track(1, 3),
                ]
            return [track(target, position) for position in range(1, 6)]

        catalog = SimpleNamespace(
            genres=[{"id": i, "name": f"genre {i}", "color": "#123456"} for i in range(6)],
            paths=[f"engenremap-canonical-{i}.html" for i in range(6)],
            tracks=lambda target: [track(target, position) for position in (1, 2)],
            samples=samples,
        )
        provider = SimpleNamespace(get=lambda settings: SimpleNamespace(distance=lambda x, y: abs(x - y)))
        self.service = GameService(catalog, provider)
        self.audio = FakeAudioStore()
        QuietHandler.game_service = self.service
        QuietHandler.audio_store = self.audio
        draw = patch("engine.game.secrets.randbelow", return_value=0)
        draw.start()
        self.addCleanup(draw.stop)
        sampler = patch("engine.game.sample", return_value=SamplingResult(
            (0, 2, 4), ((0, 1), (2, 3), (4, 5)), 1))
        self.sampler = sampler.start()
        self.addCleanup(sampler.stop)

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

    def start(self):
        status, headers, body = self.request("POST", "/api/games", {"settings": {"count": 3}})
        self.assertEqual(status, 200, body)
        return json.loads(body)

    @staticmethod
    def correct_cluster(game):
        return next(cluster for cluster in game["clusters"]
                    if any(genre["id"] == 0 for genre in cluster["genres"]))

    def test_status_and_anonymous_start_contract(self):
        status, headers, body = self.request("GET", "/api/status")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"ready": True, "genres": 6})
        self.assertEqual(headers["Cache-Control"], "no-store")
        game = self.start()
        self.assertEqual(game["stage"], "round-one")
        encoded = json.dumps(game)
        for secret in ("target", "center", "private.invalid", "track_id", "source_url", '"url"', "everynoise.com"):
            self.assertNotIn(secret, encoded)
        self.assertEqual(len(game["clusters"]), 3)

    def test_http_round_transitions_types_and_replay_guards(self):
        game = self.start()
        base = f"/api/games/{game['id']}"
        self.assertEqual(self.request("GET", base + "/audio/2")[0], 409)
        self.assertEqual(self.request("POST", base + "/genre", {"genre_id": 0})[0], 409)
        self.assertEqual(self.request("POST", base + "/cluster", {"cluster_id": []})[0], 400)
        correct = self.correct_cluster(game)
        status, _, body = self.request("POST", base + "/cluster", {"cluster_id": correct["id"]})
        self.assertEqual(status, 200)
        final = json.loads(body)
        self.assertEqual(final["stage"], "final")
        self.assertEqual(final["cluster"], correct)
        self.assertNotIn('"url"', json.dumps(final))
        self.assertNotIn("everynoise.com", json.dumps(final))
        self.assertEqual(self.request("GET", final["audio"])[0], 200)
        self.assertEqual(self.audio.tracks[-1]["position"], 2)
        self.assertEqual(self.request("POST", base + "/genre", {"genre_id": "0"})[0], 400)
        status, _, body = self.request("POST", base + "/genre", {"genre_id": 0})
        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertTrue(result["correct"])
        self.assertEqual(result["distance"], 0)
        self.assertEqual(result["target"]["id"], 0)
        self.assertEqual(result["target"]["url"], "https://everynoise.com/engenremap-canonical-0.html")
        self.assertEqual(self.request("POST", base + "/genre", {"genre_id": 0})[0], 409)

    def test_wrong_cluster_never_unlocks_second_sample(self):
        game = self.start()
        correct = self.correct_cluster(game)
        wrong = next(c for c in game["clusters"] if c["id"] != correct["id"])
        base = f"/api/games/{game['id']}"
        status, _, body = self.request("POST", base + "/cluster", {"cluster_id": wrong["id"]})
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(body)["correct"])
        self.assertEqual(json.loads(body)["target"]["url"], "https://everynoise.com/engenremap-canonical-0.html")
        self.assertEqual(self.request("GET", base + "/audio/2")[0], 409)
        self.assertEqual(self.request("GET", base + "/candidate/0/audio")[0], 409)
        self.assertEqual(self.request("POST", base + "/cluster", {"cluster_id": correct["id"]})[0], 409)

    def test_wrong_final_reveals_target_source_page_not_guessed_genre_page(self):
        game = self.start()
        base = f"/api/games/{game['id']}"
        correct = self.correct_cluster(game)
        self.assertEqual(self.request("POST", base + "/cluster", {"cluster_id": correct["id"]})[0], 200)
        status, _, body = self.request("POST", base + "/genre", {"genre_id": 1})
        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertFalse(result["correct"])
        self.assertEqual(result["target"]["id"], 0)
        self.assertEqual(result["target"]["url"], "https://everynoise.com/engenremap-canonical-0.html")

    def test_audio_has_anonymous_headers_and_correct_byte_ranges(self):
        game = self.start()
        audio = game["audio"]
        status, headers, body = self.request("GET", audio)
        self.assertEqual(status, 200)
        self.assertEqual(body, self.audio.data)
        self.assertEqual(headers["Content-Type"], "audio/mpeg")
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["Content-Disposition"], 'inline; filename="sample.mp3"')
        self.assertNotIn("private", str(headers))
        self.assertNotIn("Location", headers)
        status, headers, body = self.request("GET", audio, headers={"Range": "bytes=2-6"})
        self.assertEqual(status, 206)
        self.assertEqual(body, self.audio.data[2:7])
        self.assertEqual(headers["Content-Range"], f"bytes 2-6/{len(self.audio.data)}")
        status, _, body = self.request("GET", audio, headers={"Range": "bytes=-3"})
        self.assertEqual(status, 206)
        self.assertEqual(body, self.audio.data[-3:])
        status, headers, body = self.request("HEAD", audio, headers={"Range": "bytes=0-1"})
        self.assertEqual(status, 206)
        self.assertEqual(headers["Content-Length"], "2")
        self.assertEqual(body, b"")
        for invalid in ("bytes=9999-", "bytes=-0", "bytes=6-2", "bytes=0-1,3-4", "garbage"):
            with self.subTest(range=invalid):
                status, headers, body = self.request("GET", audio, headers={"Range": invalid})
                self.assertEqual(status, 416)
                self.assertEqual(headers["Content-Range"], f"bytes */{len(self.audio.data)}")

    def test_candidate_audio_requires_active_final_and_chosen_cluster_membership(self):
        game = self.start()
        base = f"/api/games/{game['id']}"
        for method in ("GET", "HEAD"):
            self.assertEqual(self.request(method, base + "/candidate/0/audio")[0], 409)
        self.assertEqual(self.audio.tracks, [])
        self.assertEqual(self.request("POST", base + "/cluster",
                                      {"cluster_id": self.correct_cluster(game)["id"]})[0], 200)
        for genre_id in (2, 5, 9999):
            with self.subTest(genre_id=genre_id):
                status, _, body = self.request("GET", base + f"/candidate/{genre_id}/audio")
                self.assertEqual(status, 400)
                self.assertEqual(json.loads(body)["code"], "invalid_selection")
        self.assertEqual(self.audio.tracks, [])
        for genre_id in ("-1", "true", "0.5", "not-a-number"):
            self.assertEqual(self.request("GET", base + f"/candidate/{genre_id}/audio")[0], 404)
        self.assertEqual(self.request("GET", base + "/candidate/1/audio")[0], 200)
        status, _, body = self.request("POST", base + "/genre", {"genre_id": 0})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["correct"])
        for method in ("GET", "HEAD"):
            self.assertEqual(self.request(method, base + "/candidate/0/audio")[0], 409)

    def test_candidate_audio_is_anonymous_stable_and_supports_range_and_head(self):
        game = self.start()
        base = f"/api/games/{game['id']}"
        self.assertEqual(self.request("POST", base + "/cluster",
                                      {"cluster_id": self.correct_cluster(game)["id"]})[0], 200)
        endpoint = base + "/candidate/0/audio"
        status, headers, body = self.request("GET", endpoint)
        self.assertEqual(status, 200)
        self.assertEqual(body, self.audio.data)
        self.assertEqual(headers["Content-Type"], "audio/mpeg")
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["Content-Disposition"], 'inline; filename="sample.mp3"')
        self.assertEqual(headers["Accept-Ranges"], "bytes")
        self.assertNotIn("private", str(headers))
        self.assertNotIn("Location", headers)
        first_source = self.audio.tracks[-1]
        self.assertIn(first_source["position"], (3, 4, 5))
        self.assertNotIn(first_source["track_id"], {"private-track-0-1", "private-track-0-2"})
        status, headers, body = self.request("GET", endpoint, headers={"Range": "bytes=3-7"})
        self.assertEqual(status, 206)
        self.assertEqual(body, self.audio.data[3:8])
        self.assertEqual(headers["Content-Range"], f"bytes 3-7/{len(self.audio.data)}")
        status, headers, body = self.request("HEAD", endpoint)
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Length"], str(len(self.audio.data)))
        self.assertEqual(body, b"")
        status, headers, body = self.request("HEAD", endpoint, headers={"Range": "bytes=0-1"})
        self.assertEqual(status, 206)
        self.assertEqual(headers["Content-Length"], "2")
        self.assertEqual(body, b"")
        self.assertTrue(all(source == first_source for source in self.audio.tracks))
        self.assertEqual(self.service._sessions[game["id"]].stage, "final")
        self.assertEqual(self.request("POST", base + "/genre", {"genre_id": 0})[0], 200)

    def test_candidate_audio_excludes_both_clue_identities_even_in_other_genres(self):
        game = self.start()
        base = f"/api/games/{game['id']}"
        self.assertEqual(self.request("POST", base + "/cluster",
                                      {"cluster_id": self.correct_cluster(game)["id"]})[0], 200)
        endpoint = base + "/candidate/1/audio"
        for _ in range(3):
            self.assertEqual(self.request("GET", endpoint)[0], 200)
            self.assertEqual(self.audio.tracks[-1]["track_id"], "private-track-1-3")
        self.assertEqual(self.service._sessions[game["id"]].stage, "final")

    def test_candidate_without_an_eligible_song_has_safe_error_and_preserves_answer(self):
        game = self.start()
        base = f"/api/games/{game['id']}"
        self.service.catalog.samples = lambda genre_id: self.service.catalog.tracks(0)
        self.assertEqual(self.request("POST", base + "/cluster",
                                      {"cluster_id": self.correct_cluster(game)["id"]})[0], 200)
        status, headers, body = self.request("GET", base + "/candidate/1/audio")
        self.assertEqual(status, 502)
        self.assertEqual(json.loads(body)["code"], "audio_unavailable")
        self.assertEqual(headers["Cache-Control"], "no-store")
        for secret in ("private", "track_id", "source_url", "genre 0", '"target"'):
            self.assertNotIn(secret, body.decode())
        self.assertEqual(self.audio.tracks, [])
        self.assertEqual(self.request("POST", base + "/genre", {"genre_id": 0})[0], 200)

    def test_candidate_media_failure_is_anonymous_and_retry_does_not_change_song(self):
        game = self.start()
        base = f"/api/games/{game['id']}"
        self.assertEqual(self.request("POST", base + "/cluster",
                                      {"cluster_id": self.correct_cluster(game)["id"]})[0], 200)
        endpoint = base + "/candidate/0/audio"
        for error, expected_status in ((AudioError(), 502),
                                       (RuntimeError("private source with target name"), 503)):
            self.audio.error = error
            status, _, body = self.request("GET", endpoint)
            self.assertEqual(status, expected_status)
            self.assertNotIn("private", body.decode())
            self.assertNotIn("track_id", body.decode())
            self.assertNotIn('"target"', body.decode())
        self.audio.error = None
        self.assertEqual(self.request("GET", endpoint)[0], 200)
        self.assertTrue(all(source == self.audio.tracks[0] for source in self.audio.tracks))
        self.assertEqual(self.request("POST", base + "/genre", {"genre_id": 0})[0], 200)

    def test_failed_generation_can_retry_same_session_over_http(self):
        self.sampler.side_effect = SamplingError("secret internal detail", "exhausted")
        status, _, body = self.request("POST", "/api/games", {"settings": {"count": 3}})
        self.assertEqual(status, 422)
        error = json.loads(body)
        self.assertTrue(error["retryable"])
        self.assertNotIn("secret", body.decode())
        self.assertEqual(self.service._sessions[error["id"]].target, 0)
        self.sampler.side_effect = None
        status, _, body = self.request("POST", "/api/games", {
            "settings": {"count": 3, "alpha": .4}, "retry_id": error["id"],
        })
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["id"], error["id"])

    def test_bad_json_types_and_cross_site_writes_are_rejected(self):
        for raw in (b"{", b"[]", b"null", b'"string"'):
            with self.subTest(raw=raw):
                status, _, body = self.request("POST", "/api/games", raw=raw,
                                                headers={"Content-Type": "application/json"})
                self.assertEqual(status, 400)
                self.assertEqual(json.loads(body)["code"], "invalid_request")
        for payload in ({}, {"settings": []}, {"settings": {"count": True}},
                        {"settings": {"count": 2}}, {"settings": {"count": 11}},
                        {"settings": {"cluster_size": 4}}, {"settings": {"cluster_size": 26}},
                        {"settings": {"cluster_size": 5.0}}, {"settings": {"cluster_size": True}},
                        {"settings": {"alpha": float("nan")}}):
            with self.subTest(payload=payload):
                self.assertEqual(self.request("POST", "/api/games", payload)[0], 400)
        self.assertEqual(self.request("POST", "/api/games", {"settings": {"count": 3}},
                                      headers={"Origin": "https://unrelated.example"})[0], 403)
        self.assertEqual(self.request("POST", "/api/games", {"settings": {"count": 3}},
                                      headers={"Sec-Fetch-Site": "cross-site"})[0], 403)
        self.assertEqual(len(self.service._sessions), 0)

    def test_private_files_and_unrecognized_api_routes_are_not_served(self):
        for path in ("/engine/game.py", "/.cache/catalog.json", "/README.md", "/../serve.py",
                     "/%2e%2e/serve.py", "/genreguessr-demo.json", "/api/games/not-real/audio/3"):
            with self.subTest(path=path):
                self.assertEqual(self.request("GET", path)[0], 404)
        self.assertEqual(self.request("GET", "/api/games/not-real/audio/1")[0], 404)
        self.assertEqual(self.request("GET", "/genreguessr")[0], 200)

    def test_media_failures_are_public_errors_without_source_details(self):
        game = self.start()
        self.audio.error = AudioError()
        status, _, body = self.request("GET", game["audio"])
        self.assertEqual(status, 502)
        self.assertEqual(json.loads(body)["code"], "audio_unavailable")
        self.assertNotIn("private", body.decode())
        self.audio.error = RuntimeError("private source with target name")
        status, _, body = self.request("GET", game["audio"])
        self.assertEqual(status, 503)
        self.assertNotIn("private", body.decode())
        self.audio.error = None
        self.assertEqual(self.request("GET", game["audio"])[0], 200)


if __name__ == "__main__":
    unittest.main()
