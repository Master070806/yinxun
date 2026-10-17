"""State, privacy, and target-preservation tests independent of the full crawl."""

import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from engine.game import GameError, GameService, validate_settings
from engine.sampling import SamplingError, SamplingResult


class FakeCatalog:
    def __init__(self):
        self.genres = [{"id": i, "name": f"genre {i}", "color": "#123456"}
                       for i in range(6)]
        self.paths = [f"engenremap-canonical-{i}.html" for i in range(6)]
        self.requested_tracks = []
        self.requested_samples = []
        self.missing = set()

    def tracks(self, target):
        self.requested_tracks.append(target)
        if target in self.missing:
            return []
        return [{"position": i, "preview_url": f"https://private.invalid/{target}/{i}",
                 "track_id": f"private-track-{target}-{i}", "source_url": "private-source"}
                for i in (1, 2)]

    def samples(self, genre_id):
        self.requested_samples.append(genre_id)
        return [{"position": i, "preview_url": f"https://private.invalid/{genre_id}/{i}",
                 "track_id": f"private-track-{genre_id}-{i}", "source_url": "private-source"}
                for i in range(1, 6)]


class FakeProvider:
    def __init__(self):
        self.requests = []

    def get(self, settings):
        self.requests.append(settings.copy())
        return SimpleNamespace(distance=lambda left, right: abs(left - right))


def fake_sample(space, target, count, threshold, **kwargs):
    others = [i for i in range(6) if i != target]
    return SamplingResult((target, others[1], others[3]),
                          ((target, others[0]), tuple(others[1:3]), tuple(others[3:])), 1)


class GameTests(unittest.TestCase):
    def setUp(self):
        self.catalog = FakeCatalog()
        self.provider = FakeProvider()
        self.service = GameService(self.catalog, self.provider)
        self.sample_patch = patch("engine.game.sample", side_effect=fake_sample)
        self.sample = self.sample_patch.start()
        self.addCleanup(self.sample_patch.stop)

    def start(self, target=5):
        with patch("engine.game.secrets.randbelow", return_value=target):
            return self.service.start({"count": 3})

    @staticmethod
    def correct_cluster(game, target=5):
        return next(cluster for cluster in game["clusters"]
                    if any(genre["id"] == target for genre in cluster["genres"]))

    def test_uniform_draw_uses_entire_catalog_and_publishes_no_answer_metadata(self):
        with patch("engine.game.secrets.randbelow", return_value=5) as draw:
            game = self.service.start({"count": 3})
        draw.assert_called_once_with(len(self.catalog.genres))
        self.assertEqual(self.catalog.requested_tracks, [5])
        self.assertEqual(set(game), {"id", "stage", "clusters", "audio", "audio_available"})
        encoded = json.dumps(game)
        for secret in ("target", "center", "private", "track_id", "source_url", '"url"', "everynoise.com"):
            self.assertNotIn(secret, encoded)
        self.assertEqual(game["audio"], f"/api/games/{game['id']}/audio/1")
        self.assertTrue(game["audio_available"])
        self.assertEqual(sum(any(g["id"] == 5 for g in c["genres"])
                             for c in game["clusters"]), 1)

    def test_second_sample_and_final_answer_require_correct_first_round(self):
        game = self.start()
        with self.assertRaises(GameError) as locked:
            self.service.audio_source(game["id"], 2)
        self.assertEqual(locked.exception.status, 409)
        with self.assertRaises(GameError):
            self.service.choose_genre(game["id"], 5)
        correct = self.correct_cluster(game)
        final = self.service.choose_cluster(game["id"], correct["id"])
        self.assertEqual(final["stage"], "final")
        self.assertEqual(final["cluster"], correct)
        self.assertNotIn("target", final)
        self.assertNotIn('"url"', json.dumps(final))
        self.assertNotIn("everynoise.com", json.dumps(final))
        self.assertEqual(self.service.audio_source(game["id"], 2)["position"], 2)
        result = self.service.choose_genre(game["id"], 5)
        self.assertTrue(result["correct"])
        self.assertEqual(result["distance"], 0)
        self.assertEqual(result["target"]["id"], 5)
        self.assertEqual(result["target"]["url"], "https://everynoise.com/engenremap-canonical-5.html")
        with self.assertRaises(GameError) as replay:
            self.service.choose_genre(game["id"], 5)
        self.assertEqual(replay.exception.status, 409)

    def test_wrong_cluster_finishes_without_unlocking_second_sample(self):
        game = self.start()
        correct = self.correct_cluster(game)
        wrong = next(c for c in game["clusters"] if c["id"] != correct["id"])
        result = self.service.choose_cluster(game["id"], wrong["id"])
        self.assertEqual(result["stage"], "finished")
        self.assertFalse(result["correct"])
        self.assertEqual(result["target"]["id"], 5)
        self.assertEqual(result["target"]["url"], "https://everynoise.com/engenremap-canonical-5.html")
        with self.assertRaises(GameError):
            self.service.audio_source(game["id"], 2)
        with self.assertRaises(GameError):
            self.service.choose_cluster(game["id"], correct["id"])

    def test_invalid_selections_do_not_consume_a_round(self):
        game = self.start()
        for bad in ("unknown", [], 0):
            with self.assertRaises(GameError) as invalid:
                self.service.choose_cluster(game["id"], bad)
            self.assertEqual(invalid.exception.code, "invalid_selection")
        correct = self.correct_cluster(game)
        self.service.choose_cluster(game["id"], correct["id"])
        for bad in (4, "5", True, [], 900):
            with self.assertRaises(GameError):
                self.service.choose_genre(game["id"], bad)
        wrong = next(g["id"] for g in correct["genres"] if g["id"] != 5)
        result = self.service.choose_genre(game["id"], wrong)
        self.assertFalse(result["correct"])
        self.assertEqual(result["distance"], 5)
        self.assertEqual(result["target"]["url"], "https://everynoise.com/engenremap-canonical-5.html")

    def test_sampling_failure_retry_retains_target_and_can_change_parameters(self):
        self.sample.side_effect = SamplingError("private target detail", "exhausted")
        with patch("engine.game.secrets.randbelow", return_value=5) as draw:
            with self.assertRaises(GameError) as failure:
                self.service.start({"count": 3})
            game_id = failure.exception.payload["id"]
            self.assertEqual(failure.exception.code, "exhausted")
            self.assertTrue(failure.exception.payload["retryable"])
            self.assertNotIn("private target detail", json.dumps(failure.exception.payload))
            self.sample.side_effect = fake_sample
            retried = self.service.start({"count": 3, "alpha": .4}, retry_id=game_id)
            draw.assert_called_once_with(6)
        self.assertEqual(retried["id"], game_id)
        self.assertEqual(self.catalog.requested_tracks, [5, 5])
        self.assertEqual(self.provider.requests[-1]["alpha"], .4)
        with self.assertRaises(GameError):
            self.service.start({"count": 3}, retry_id=game_id)

    def test_missing_media_does_not_reroll_or_filter_target(self):
        self.catalog.missing.add(5)
        with patch("engine.game.secrets.randbelow", return_value=5) as draw:
            with self.assertRaises(GameError) as failure:
                self.service.start({"count": 3})
            draw.assert_called_once_with(6)
        self.assertEqual(failure.exception.code, "missing_samples")
        self.sample.assert_not_called()
        self.catalog.missing.clear()
        with patch("engine.game.secrets.randbelow") as redraw:
            result = self.service.start({"count": 3}, retry_id=failure.exception.payload["id"])
            redraw.assert_not_called()
        self.assertEqual(self.catalog.requested_tracks, [5, 5])
        self.assertEqual(result["stage"], "round-one")

    def test_missing_cached_preview_keeps_original_track_for_media_resolution(self):
        original = self.catalog.tracks
        def tracks(target):
            result = original(target)
            result[0]["preview_url"] = None
            return result
        self.catalog.tracks = tracks
        game = self.start()
        self.assertTrue(game["audio_available"])
        track = self.service.audio_source(game["id"], 1)
        self.assertIsNone(track["preview_url"])
        self.assertEqual(track["track_id"], "private-track-5-1")

    def test_unavailable_source_samples_keep_target_and_report_round_availability(self):
        original_tracks = self.catalog.tracks
        for unavailable_position in (1, 2):
            with self.subTest(unavailable_position=unavailable_position):
                def tracks(target):
                    result = original_tracks(target)
                    result[unavailable_position - 1].update(preview_url=None, track_id=None)
                    return result
                self.catalog.tracks = tracks
                with patch("engine.game.secrets.randbelow", return_value=5) as draw:
                    game = self.service.start({"count": 3})
                    draw.assert_called_once_with(6)
                self.assertEqual(game["stage"], "round-one")
                self.assertEqual(game["audio_available"], unavailable_position != 1)
                self.assertEqual(self.service._sessions[game["id"]].target, 5)
                correct = self.correct_cluster(game)
                final = self.service.choose_cluster(game["id"], correct["id"])
                self.assertEqual(final["stage"], "final")
                self.assertEqual(final["audio_available"], unavailable_position != 2)
                self.assertEqual(self.service.choose_genre(game["id"], 5)["target"]["id"], 5)

    def test_bad_sampler_cannot_publish_an_ambiguous_target(self):
        self.sample.side_effect = None
        self.sample.return_value = SamplingResult((5, 4, 1), ((5, 0), (5, 4), (1, 2, 3)), 1)
        with self.assertRaises(GameError) as error:
            self.start()
        self.assertEqual(error.exception.code, "preparation_failed")
        self.assertTrue(error.exception.payload["retryable"])

    def test_expiry_and_capacity_are_bounded(self):
        self.service.max_sessions = 1
        game = self.start()
        with self.assertRaises(GameError) as capacity:
            self.start()
        self.assertEqual(capacity.exception.code, "session_limit")
        self.service._sessions[game["id"]].expires = 0
        with self.assertRaises(GameError) as expired:
            self.service.audio_source(game["id"], 1)
        self.assertEqual(expired.exception.status, 404)
        self.assertEqual(self.start()["stage"], "round-one")

    def test_validation_rejects_nonfinite_and_degenerate_parameters_without_sampling(self):
        bad_settings = [{"count": True}, {"count": 2}, {"count": 11}, {"count": 3.0},
                        {"alpha": 0}, {"alpha": 1}, {"alpha": float("nan")},
                        {"separation": float("inf")}, {"separation": 10**1000},
                        {"metric": "graph", "separation": 2.5},
                        {"metric": "kernel", "regularization": 0},
                        {"metric": "kernel", "opposition": -1},
                        {"metric": "kernel", "separation": 2.1}]
        with patch("engine.game.secrets.randbelow") as draw:
            for settings in bad_settings:
                with self.subTest(settings=settings), self.assertRaises(GameError):
                    self.service.start(settings)
            draw.assert_not_called()
        self.assertEqual(validate_settings({"metric": "kernel"})["regularization"], .1)

    def test_count_and_cluster_size_boundaries_and_defaults(self):
        for metric in ("xyrgb", "graph", "kernel"):
            for count in (3, 10):
                for size in (5, 25):
                    with self.subTest(metric=metric, count=count, cluster_size=size):
                        settings = validate_settings({"metric": metric, "count": count,
                                                      "cluster_size": size})
                        self.assertEqual(settings["count"], count)
                        if metric == "graph":
                            self.assertNotIn("cluster_size", settings)
                        else:
                            self.assertEqual(settings["cluster_size"], size)
        for metric in ("xyrgb", "kernel"):
            self.assertEqual(validate_settings({"metric": metric})["cluster_size"], 20)

    def test_cluster_size_validation_occurs_before_drawing_a_target(self):
        with patch("engine.game.secrets.randbelow") as draw:
            for metric in ("xyrgb", "kernel"):
                for size in (True, False, 4, 26, 5.0, "20", None, float("nan"), float("inf")):
                    with self.subTest(metric=metric, cluster_size=size), self.assertRaises(GameError) as error:
                        self.service.start({"metric": metric, "count": 3, "cluster_size": size})
                    self.assertEqual(error.exception.code, "invalid_settings")
            draw.assert_not_called()
        self.assertEqual(self.provider.requests, [])

    def test_cluster_size_is_forwarded_for_continuous_metrics_and_ignored_for_graph(self):
        for metric, size in (("xyrgb", 5), ("kernel", 25), ("graph", "unused")):
            with self.subTest(metric=metric), patch("engine.game.secrets.randbelow", return_value=5):
                self.service.start({"metric": metric, "count": 3, "cluster_size": size})
            forwarded = self.provider.requests[-1]
            if metric == "graph":
                self.assertNotIn("cluster_size", forwarded)
            else:
                self.assertEqual(forwarded["cluster_size"], size)
            self.assertEqual(self.sample.call_args.args[2], 3)

    def test_ten_cluster_request_is_forwarded_and_returns_ten_clusters(self):
        catalog = FakeCatalog()
        catalog.genres = [{"id": i, "name": f"genre {i}", "color": "#123456"} for i in range(30)]
        catalog.paths = [f"engenremap-canonical-{i}.html" for i in range(30)]
        service = GameService(catalog, self.provider)
        self.sample.side_effect = None
        self.sample.return_value = SamplingResult(tuple(range(10)),
                                                 tuple((i,) for i in range(10)), 1)
        with patch("engine.game.secrets.randbelow", return_value=5):
            game = service.start({"count": 10, "cluster_size": 25})
        self.assertEqual(len(game["clusters"]), 10)
        self.assertEqual(self.sample.call_args.args[2], 10)
        self.assertEqual(self.provider.requests[-1]["cluster_size"], 25)

    def test_comparison_samples_exclude_both_target_clues_by_id_or_normalized_url(self):
        game = self.start()
        self.service.choose_cluster(game["id"], self.correct_cluster(game)["id"])
        forbidden = [
            {"position": 1, "track_id": "private-track-5-1", "preview_url": "https://private.invalid/different"},
            {"position": 2, "track_id": "private-track-5-2", "preview_url": None},
            {"position": 3, "track_id": "another-id", "preview_url": "https://private.invalid/5/1?token=new"},
            {"position": 4, "track_id": None, "preview_url": "https://PRIVATE.invalid:443/5/2?token=new#fragment"},
            {"position": 5, "track_id": None, "preview_url": None},
        ]
        allowed = [
            {"position": 6, "track_id": "comparison-id", "preview_url": None},
            {"position": 7, "track_id": None, "preview_url": "https://private.invalid/another-song"},
        ]
        self.catalog.samples = lambda genre_id: forbidden + allowed
        with patch.object(self.service._random, "choice", side_effect=lambda options: options[-1]) as choose:
            # Check a different genre too: a shared song must not reveal the target by exact replay.
            for genre_id in (0, 5):
                result = self.service.candidate_audio_source(game["id"], genre_id)
                self.assertEqual(choose.call_args.args[0], allowed)
                self.assertEqual(result, allowed[-1])

    def test_comparison_sample_is_stable_and_does_not_change_the_answer_or_round_audio(self):
        game = self.start()
        final = self.service.choose_cluster(game["id"], self.correct_cluster(game)["id"])
        original_clues = tuple(dict(self.service.audio_source(game["id"], i)) for i in (1, 2))
        with patch.object(self.service._random, "choice", side_effect=lambda options: options[0]) as choose:
            first = self.service.candidate_audio_source(game["id"], 5)
            replay = self.service.candidate_audio_source(game["id"], 5)
            choose.assert_called_once()
        self.assertEqual(first, replay)
        self.assertEqual(first["position"], 3)
        self.assertEqual(self.catalog.requested_samples, [5])
        first["track_id"] = "caller mutation"
        self.assertEqual(self.service.candidate_audio_source(game["id"], 5), replay)
        self.assertEqual(tuple(self.service.audio_source(game["id"], i) for i in (1, 2)), original_clues)
        session = self.service._sessions[game["id"]]
        self.assertEqual((session.target, session.stage), (5, "final"))
        self.assertEqual(set(session.comparison_tracks), {5})
        self.assertNotIn("track_id", json.dumps(final))
        self.assertNotIn("private", json.dumps(final))
        self.assertTrue(self.service.choose_genre(game["id"], 5)["correct"])

    def test_comparison_does_not_exclude_different_genres_own_first_two_samples(self):
        game = self.start()
        self.service.choose_cluster(game["id"], self.correct_cluster(game)["id"])
        with patch.object(self.service._random, "choice", side_effect=lambda options: options[0]) as choose:
            result = self.service.candidate_audio_source(game["id"], 0)
        self.assertEqual(result["position"], 1)
        self.assertEqual([track["position"] for track in choose.call_args.args[0]], [1, 2, 3, 4, 5])

    def test_comparison_requires_active_final_stage_and_strict_cluster_membership(self):
        game = self.start()
        with self.assertRaises(GameError) as early:
            self.service.candidate_audio_source(game["id"], 5)
        self.assertEqual(early.exception.status, 409)
        self.service.choose_cluster(game["id"], self.correct_cluster(game)["id"])
        for genre_id in (True, 5.0, "5", [], -1, 1, 999):
            with self.subTest(genre_id=genre_id), self.assertRaises(GameError) as invalid:
                self.service.candidate_audio_source(game["id"], genre_id)
            self.assertEqual(invalid.exception.code, "invalid_selection")
        self.assertEqual(self.catalog.requested_samples, [])
        self.assertEqual(self.service._sessions[game["id"]].comparison_tracks, {})
        self.service.candidate_audio_source(game["id"], 0)
        self.service.choose_genre(game["id"], 5)
        with self.assertRaises(GameError) as finished:
            self.service.candidate_audio_source(game["id"], 0)
        self.assertEqual(finished.exception.status, 409)

    def test_unavailable_comparison_is_safe_and_keeps_the_game_target(self):
        game = self.start()
        self.service.choose_cluster(game["id"], self.correct_cluster(game)["id"])
        clues = list(self.service._sessions[game["id"]].tracks)
        with patch.object(self.catalog, "samples", return_value=clues + [{"preview_url": None, "track_id": None}]) as samples:
            for _ in range(2):
                with self.assertRaises(GameError) as unavailable:
                    self.service.candidate_audio_source(game["id"], 0)
                self.assertEqual(unavailable.exception.code, "audio_unavailable")
                self.assertEqual(unavailable.exception.status, 502)
                payload = json.dumps(unavailable.exception.payload)
                self.assertNotIn("private", payload)
                self.assertNotIn("target", payload)
            samples.assert_called_once_with(0)
        self.assertEqual(self.service._sessions[game["id"]].target, 5)
        self.assertEqual(self.service._sessions[game["id"]].stage, "final")
        self.assertTrue(self.service.choose_genre(game["id"], 5)["correct"])

    def test_comparison_catalog_failure_has_no_private_details_and_can_retry(self):
        game = self.start()
        self.service.choose_cluster(game["id"], self.correct_cluster(game)["id"])
        with patch.object(self.catalog, "samples", side_effect=RuntimeError("private path to target genre")):
            with self.assertRaises(GameError) as unavailable:
                self.service.candidate_audio_source(game["id"], 5)
        self.assertEqual(unavailable.exception.code, "audio_unavailable")
        self.assertNotIn("private", json.dumps(unavailable.exception.payload))
        self.assertEqual(self.service._sessions[game["id"]].comparison_tracks, {})
        self.assertGreater(self.service.candidate_audio_source(game["id"], 5)["position"], 2)


if __name__ == "__main__":
    unittest.main()
