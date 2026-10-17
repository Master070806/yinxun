"""Room synchronization, scoring and authorization on a tiny deterministic catalog."""

from concurrent.futures import ThreadPoolExecutor
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from engine.game import GameError, GameService
from engine.multiplayer import MultiplayerService
from engine.race import RaceService
from engine.sampling import SamplingError, SamplingResult


RACE_CLUSTERS = ((0, 1, 2, 3, 4), (1, 2, 3, 4, 5), (2, 0, 1, 3, 4),
                 (3, 0, 1, 2, 4), (4, 0, 1, 2, 3), (5, 1, 2, 4, 6),
                 (6, 1, 2, 4, 5))
SAMPLE = SamplingResult((0, 3, 5), ((0, 1, 2), (3, 4), (5, 6)), 1)


def make_catalog():
    def track(genre_id, position):
        return {"position": position, "track_id": f"private-track-{genre_id}-{position}",
                "preview_url": f"https://private.invalid/{genre_id}/{position}",
                "source_url": "private-source"}

    return SimpleNamespace(
        genres=[{"id": i, "name": f"genre {i}", "color": "#123456",
                 "x": i, "y": 0, "preview_url": "private-metadata"} for i in range(7)],
        paths=[f"engenremap-canonical-{i}.html" for i in range(7)],
        tracks=lambda i: [track(i, position) for position in (1, 2)],
        samples=lambda i: [track(i, position) for position in range(1, 6)],
    )


class FakeSpace:
    clusters = RACE_CLUSTERS

    def distance(self, left, right):
        return abs(left - right)

    def reverse_clusters(self, member):
        return tuple(i for i, cluster in enumerate(self.clusters) if member in cluster)


class FakeProvider:
    def __init__(self):
        self.space = FakeSpace()
        self.requests = []

    def get(self, settings):
        self.requests.append(dict(settings))
        return self.space


class MultiplayerTests(unittest.TestCase):
    def setUp(self):
        self.catalog = make_catalog()
        self.provider = FakeProvider()
        self.game = GameService(self.catalog, self.provider)
        self.race = RaceService(self.catalog, self.provider)
        self.service = MultiplayerService(self.game, self.race)
        for name, kwargs in (("engine.game.sample", {"return_value": SAMPLE}),
                             ("engine.game.secrets.randbelow", {"return_value": 0})):
            mocked = patch(name, **kwargs)
            mocked.start()
            self.addCleanup(mocked.stop)

    def create(self, mode="guessr", rounds=1, **extra):
        return self.service.create({"mode": mode, "name": "Host", "rounds": rounds,
                                    "settings": {"count": 3, "cluster_size": 5},
                                    "start_id": 0, "goal_id": 6, **extra})

    def join(self, host, name="Guest"):
        return self.service.join(host["room"]["id"], {"name": name})

    def get(self, player):
        return self.service.get(player["room"]["id"], player["token"])

    def action(self, player, action, **request):
        return self.service.action(player["room"]["id"], player["token"], action, request)

    def start(self, mode="guessr", rounds=1, players=2, **extra):
        host = self.create(mode, rounds, **extra)
        party = [host] + [self.join(host, f"Guest {i}") for i in range(1, players)]
        room = self.action(host, "start")
        return party, room

    @staticmethod
    def correct_cluster(room):
        return next(c for c in room["game"]["clusters"] if any(g["id"] == 0 for g in c["genres"]))

    @staticmethod
    def player(room, identity):
        return next(p for p in room["players"] if p["id"] == identity["player_id"])

    def enter_genre(self, party, room):
        cluster_id = self.correct_cluster(room)["id"]
        for player in party:
            room = self.action(player, "cluster", cluster_id=cluster_id,
                               round_number=room["round_number"])
        self.assertEqual(room["stage"], "genre")
        return room

    def finish_round(self, party, room, guesses=None):
        room = self.enter_genre(party, room)
        for player, genre_id in zip(party, guesses or [0] * len(party)):
            room = self.action(player, "genre", genre_id=genre_id,
                               round_number=room["round_number"])
        self.assertEqual(room["stage"], "round_result")
        return room

    def test_creation_refresh_public_preview_and_credentials_are_isolated(self):
        host = self.create(rounds=3)
        guest = self.join(host)
        self.assertNotEqual(host["token"], guest["token"])
        self.assertNotEqual(host["player_id"], guest["player_id"])
        room = self.get(host)
        self.assertEqual(room["stage"], "lobby")
        self.assertEqual(room["total_rounds"], 3)
        self.assertEqual(room["host_id"], host["player_id"])
        self.assertEqual(room["self_id"], host["player_id"])
        self.assertEqual(self.get(guest)["self_id"], guest["player_id"])
        self.assertEqual(self.get(host), room)
        public = self.service.get(room["id"], None)
        encoded = json.dumps(public)
        for secret in (host["token"], guest["token"], "private", "track_id", "source_url"):
            self.assertNotIn(secret, encoded)
        self.assertNotIn("game", public)
        self.assertNotIn("race", public)
        for token in ("not-a-member", "", None):
            with self.subTest(token=token), self.assertRaises(GameError) as denied:
                self.service.action(room["id"], token, "start", {})
            self.assertIn(denied.exception.status, (401, 403))

    def test_host_controls_start_and_joining_closes_when_started(self):
        host = self.create()
        guest = self.join(host)
        with self.assertRaises(GameError) as denied:
            self.action(guest, "start")
        self.assertEqual(denied.exception.status, 403)
        room = self.action(host, "start")
        self.assertEqual(room["stage"], "cluster")
        with self.assertRaises(GameError):
            self.join(host, "Too late")
        with self.assertRaises(GameError):
            self.action(host, "start")
        self.assertEqual(self.get(host), room)

    def test_players_share_target_and_clusters_without_answer_or_source_metadata(self):
        party, host_room = self.start()
        guest_room = self.get(party[1])
        self.assertEqual(host_room["game"]["clusters"], guest_room["game"]["clusters"])
        self.assertEqual(host_room["round_number"], 1)
        for room in (host_room, guest_room):
            encoded = json.dumps(room)
            for secret in ('"target"', '"center"', "private", "track_id", "source_url", "everynoise.com"):
                self.assertNotIn(secret, encoded)
        first = self.service.audio_source(host_room["id"], party[0]["token"], 1, "clue1")
        second = self.service.audio_source(host_room["id"], party[1]["token"], 1, "clue1")
        self.assertEqual(first, second)

    def test_cluster_barrier_blocks_early_second_clue_and_wrong_players_cannot_listen(self):
        party, room = self.start(players=3)
        correct = self.correct_cluster(room)["id"]
        wrong = next(c["id"] for c in room["game"]["clusters"] if c["id"] != correct)
        room = self.action(party[0], "cluster", cluster_id=correct, round_number=1)
        self.assertEqual(room["stage"], "cluster")
        self.assertTrue(self.player(room, party[0])["submitted"])
        self.assertTrue(all(p["eligible"] is None for p in room["players"]))
        with self.assertRaises(GameError):
            self.service.audio_source(room["id"], party[0]["token"], 1, "clue2")
        self.action(party[1], "cluster", cluster_id=wrong, round_number=1)
        room = self.action(party[2], "cluster", cluster_id=correct, round_number=1)
        self.assertEqual(room["stage"], "genre")
        self.assertFalse(self.player(room, party[1])["eligible"])
        self.assertEqual(self.service.audio_source(room["id"], party[0]["token"], 1, "clue2")["position"], 2)
        for kind, genre_id in (("clue2", None), ("candidate", 0)):
            with self.subTest(kind=kind), self.assertRaises(GameError):
                self.service.audio_source(room["id"], party[1]["token"], 1, kind, genre_id)
        with self.assertRaises(GameError):
            self.action(party[1], "genre", genre_id=0, round_number=1)
        room = self.action(party[0], "genre", genre_id=1, round_number=1)
        self.assertEqual(room["stage"], "genre")
        self.assertNotIn("result", room)
        room = self.action(party[2], "genre", genre_id=0, round_number=1)
        results = {p["id"]: p for p in room["result"]["players"]}
        self.assertEqual(room["stage"], "round_result")
        self.assertEqual(room["result"]["target"]["id"], 0)
        self.assertEqual([results[p["player_id"]]["round_score"] for p in party], [500, 0, 1000])
        self.assertEqual([self.player(room, p)["score"] for p in party], [500, 0, 1000])

    def test_farthest_valid_guess_scores_zero_and_exact_target_scores_one_thousand(self):
        party, room = self.start()
        result = self.finish_round(party, room, [2, 0])
        scores = {p["id"]: p["round_score"] for p in result["result"]["players"]}
        self.assertEqual(scores, {party[0]["player_id"]: 0, party[1]["player_id"]: 1000})

    def test_all_wrong_clusters_finish_without_waiting_for_genre_submissions(self):
        party, room = self.start()
        correct = self.correct_cluster(room)["id"]
        wrong = next(c["id"] for c in room["game"]["clusters"] if c["id"] != correct)
        for player in party:
            room = self.action(player, "cluster", cluster_id=wrong, round_number=1)
        self.assertEqual(room["stage"], "round_result")
        self.assertTrue(all(p["round_score"] == 0 for p in room["result"]["players"]))

    def test_ready_barrier_advances_exactly_once_and_last_round_finishes(self):
        party, room = self.start(rounds=2)
        room = self.finish_round(party, room, [1, 0])
        room = self.action(party[0], "ready", round_number=1)
        self.assertEqual((room["stage"], room["round_number"]), ("round_result", 1))
        self.assertEqual(self.action(party[0], "ready", round_number=1), room)
        room = self.action(party[1], "ready", round_number=1)
        self.assertEqual((room["stage"], room["round_number"]), ("cluster", 2))
        with self.assertRaises(GameError):
            self.action(party[1], "cluster", cluster_id=self.correct_cluster(room)["id"], round_number=1)
        room = self.finish_round(party, room, [0, 2])
        self.assertEqual([self.player(room, p)["score"] for p in party], [1500, 1000])
        self.action(party[0], "ready", round_number=2)
        room = self.action(party[1], "ready", round_number=2)
        self.assertEqual(room["stage"], "finished")
        self.assertEqual(room["winner_ids"], [party[0]["player_id"]])
        self.assertEqual(self.get(party[1]), room)

    def test_invalid_and_duplicate_selections_never_overwrite_submitted_answers(self):
        party, room = self.start()
        for cluster_id in ("missing", [], True, 1):
            with self.subTest(cluster_id=cluster_id), self.assertRaises(GameError):
                self.action(party[0], "cluster", cluster_id=cluster_id, round_number=1)
        for number in (0, 2, True, "1", 1.0, None):
            with self.subTest(number=number), self.assertRaises(GameError):
                self.action(party[0], "cluster", cluster_id=self.correct_cluster(room)["id"], round_number=number)
        self.assertEqual(self.get(party[0]), room)
        cluster_id = self.correct_cluster(room)["id"]
        submitted = self.action(party[0], "cluster", cluster_id=cluster_id, round_number=1)
        self.assertEqual(self.action(party[0], "cluster", cluster_id=cluster_id, round_number=1), submitted)
        wrong = next(c["id"] for c in room["game"]["clusters"] if c["id"] != cluster_id)
        with self.assertRaises(GameError) as duplicate:
            self.action(party[0], "cluster", cluster_id=wrong, round_number=1)
        self.assertEqual(duplicate.exception.status, 409)
        self.action(party[1], "cluster", cluster_id=cluster_id, round_number=1)
        for genre_id in (3, True, "0", 0.0, None):
            with self.subTest(genre_id=genre_id), self.assertRaises(GameError):
                self.action(party[0], "genre", genre_id=genre_id, round_number=1)
        self.action(party[0], "genre", genre_id=1, round_number=1)
        with self.assertRaises(GameError):
            self.action(party[0], "genre", genre_id=0, round_number=1)
        room = self.action(party[1], "genre", genre_id=0, round_number=1)
        self.assertEqual(self.player(room, party[0])["score"], 500)

    def test_comparison_audio_excludes_clues_and_refresh_keeps_it_stable(self):
        party, room = self.start()
        room = self.enter_genre(party, room)
        for player in party:
            sample = self.service.audio_source(room["id"], player["token"], 1, "candidate", 0)
            self.assertNotIn(sample["position"], (1, 2))
            self.assertEqual(self.service.audio_source(room["id"], player["token"], 1, "candidate", 0), sample)
        for kind, genre_id in (("candidate", 3), ("candidate", True), ("clue2", None)):
            with self.subTest(kind=kind), self.assertRaises(GameError):
                self.service.audio_source(room["id"], "invalid-token", 1, kind, genre_id)
        with self.assertRaises(GameError):
            self.service.audio_source(room["id"], party[0]["token"], 2, "clue1")
        self.assertEqual(self.get(party[1]), room)

    def test_concurrent_duplicate_submission_is_recorded_once(self):
        party, room = self.start()
        cluster_id = self.correct_cluster(room)["id"]
        def submit(_):
            try:
                return self.action(party[0], "cluster", cluster_id=cluster_id, round_number=1)["stage"]
            except GameError as error:
                return error.status
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(submit, range(2)))
        self.assertEqual(outcomes, ["cluster", "cluster"])
        self.assertEqual(self.get(party[1])["stage"], "cluster")
        self.assertEqual(self.action(party[1], "cluster", cluster_id=cluster_id, round_number=1)["stage"], "genre")

    def test_leaving_removes_a_player_from_each_synchronization_barrier(self):
        party, room = self.start(players=3)
        cluster_id = self.correct_cluster(room)["id"]
        self.action(party[0], "cluster", cluster_id=cluster_id, round_number=1)
        self.action(party[1], "cluster", cluster_id=cluster_id, round_number=1)
        self.action(party[2], "leave")
        self.assertEqual(self.get(party[0])["stage"], "genre")
        self.action(party[0], "genre", genre_id=0, round_number=1)
        self.action(party[1], "leave")
        self.assertEqual(self.get(party[0])["stage"], "round_result")
        self.assertEqual(self.action(party[0], "ready", round_number=1)["stage"], "finished")

    def test_lobby_host_leave_transfers_start_authority(self):
        host = self.create()
        guest = self.join(host)
        self.join(host, "Another guest")
        self.action(host, "leave")
        self.assertEqual(self.get(guest)["host_id"], guest["player_id"])
        self.assertEqual(self.action(guest, "start")["stage"], "cluster")

    def test_host_removal_unblocks_barrier_but_guests_cannot_remove_others(self):
        party, room = self.start(players=3)
        cluster_id = self.correct_cluster(room)["id"]
        self.action(party[0], "cluster", cluster_id=cluster_id, round_number=1)
        self.action(party[1], "cluster", cluster_id=cluster_id, round_number=1)
        with self.assertRaises(GameError) as denied:
            self.action(party[1], "remove", player_id=party[0]["player_id"])
        self.assertEqual(denied.exception.status, 403)
        room = self.action(party[0], "remove", player_id=party[2]["player_id"])
        self.assertEqual(room["stage"], "genre")
        self.assertTrue(self.player(room, party[2])["left"])
        with self.assertRaises(GameError):
            self.action(party[2], "cluster", cluster_id=cluster_id, round_number=1)

    def test_race_common_start_goal_personal_progress_and_first_finish_freeze(self):
        party, room = self.start("race")
        other = self.get(party[1])
        self.assertEqual(room["race"], other["race"])
        self.assertEqual((room["race"]["current"]["id"], room["race"]["goal"]["id"]), (0, 6))
        self.action(party[1], "move", genre_id=2, revision=0)
        self.assertEqual(self.get(party[0])["race"]["current"]["id"], 0)
        for revision, genre_id in enumerate((1, 5, 6)):
            room = self.action(party[0], "move", genre_id=genre_id, revision=revision)
        self.assertEqual(room["stage"], "finished")
        self.assertEqual(room["winner_ids"], [party[0]["player_id"]])
        routes = {p["id"]: [g["id"] for g in p["route"]] for p in room["routes"]}
        self.assertEqual(routes, {party[0]["player_id"]: [0, 1, 5, 6], party[1]["player_id"]: [0, 2]})
        frozen = self.get(party[1])
        with self.assertRaises(GameError):
            self.action(party[1], "move", genre_id=1, revision=1)
        self.assertEqual(self.get(party[1]), frozen)

    def test_concurrent_race_finishes_have_one_winner_and_one_frozen_route(self):
        party, _ = self.start("race")
        for player in party:
            self.action(player, "move", genre_id=1, revision=0)
            self.action(player, "move", genre_id=5, revision=1)
        def finish(player):
            try:
                return self.action(player, "move", genre_id=6, revision=2)
            except GameError as error:
                return error.status
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(finish, party))
        self.assertEqual(sum(isinstance(result, dict) for result in outcomes), 1)
        self.assertIn(409, outcomes)
        room = self.get(party[0])
        self.assertEqual(len(room["winner_ids"]), 1)
        self.assertCountEqual([len(p["route"]) for p in room["routes"]], [3, 4])

    def test_race_revision_checks_are_per_player_and_forged_fields_are_ignored(self):
        party, _ = self.start("race")
        room = self.action(party[0], "move", genre_id=1, revision=0,
                           player_id=party[1]["player_id"], goal_id=1,
                           route=[0, 6], stage="finished", score=999999)
        self.assertEqual(room["stage"], "race")
        self.assertEqual(room["race"]["goal"]["id"], 6)
        self.assertEqual(room["race"]["revision"], 1)
        self.assertEqual(self.get(party[1])["race"]["revision"], 0)
        with self.assertRaises(GameError) as stale:
            self.action(party[0], "move", genre_id=5, revision=0)
        self.assertEqual(stale.exception.status, 409)
        self.assertEqual(self.get(party[0]), room)

    def test_race_equal_start_goal_finishes_with_zero_move_routes(self):
        party, room = self.start("race", start_id=3, goal_id=3)
        self.assertEqual(room["stage"], "finished")
        self.assertCountEqual(room["winner_ids"], [p["player_id"] for p in party])
        self.assertTrue(all([g["id"] for g in p["route"]] == [3] for p in room["routes"]))

    def test_other_room_credentials_cannot_read_or_act_as_a_member(self):
        first = self.create()
        other = self.create()
        for operation in (lambda: self.service.get(first["room"]["id"], other["token"]),
                          lambda: self.service.action(first["room"]["id"], other["token"], "start", {})):
            with self.assertRaises(GameError) as denied:
                operation()
            self.assertIn(denied.exception.status, (401, 403))

    def test_invalid_settings_and_round_counts_are_rejected_before_start(self):
        for rounds in (0, 21, True, "3", 1.5, None):
            with self.subTest(rounds=rounds), self.assertRaises(GameError):
                self.create(rounds=rounds)
        for settings in (None, [], {"count": 2}, {"alpha": float("nan")}, {"cluster_size": True}):
            with self.subTest(settings=settings), self.assertRaises(GameError):
                self.create(settings=settings)
        for mode in ("unknown", True, None):
            with self.subTest(mode=mode), self.assertRaises(GameError):
                self.create(mode=mode)

    def test_failed_preparation_retries_same_target_without_exposing_private_game_credential(self):
        host = self.create()
        self.join(host)
        with patch("engine.game.sample", side_effect=SamplingError("private target detail", "exhausted")):
            with self.assertRaises(GameError) as failure:
                self.action(host, "start")
        self.assertTrue(failure.exception.payload["retryable"])
        private_game = next(iter(self.game._sessions.values()))
        room = self.get(host)
        self.assertEqual(room["stage"], "lobby")
        self.assertEqual(private_game.target, 0)
        for payload in (failure.exception.payload, room,
                        self.service.get(host["room"]["id"], None)):
            encoded = json.dumps(payload)
            self.assertNotIn(private_game.id, encoded)
            self.assertNotIn("private target detail", encoded)
        with patch("engine.game.secrets.randbelow") as draw:
            self.action(host, "configure", settings={"count": 3, "alpha": .4}, rounds=2)
            retried = self.action(host, "start")
            draw.assert_not_called()
        self.assertEqual(retried["stage"], "cluster")
        self.assertEqual(retried["settings"]["alpha"], .4)
        self.assertEqual(retried["total_rounds"], 2)
        self.assertEqual(len(self.game._sessions), 1)

    def test_next_round_failure_preserves_scores_and_can_retry_without_drawing_again(self):
        party, room = self.start(rounds=2)
        self.finish_round(party, room, [1, 0])
        self.action(party[0], "ready", round_number=1)
        with patch("engine.game.sample", side_effect=SamplingError("unavailable", "exhausted")):
            with self.assertRaises(GameError):
                self.action(party[1], "ready", round_number=1)
        room = self.get(party[0])
        self.assertEqual((room["stage"], room["round_number"]), ("round_result", 1))
        self.assertEqual([self.player(room, p)["score"] for p in party], [500, 1000])
        with patch("engine.game.secrets.randbelow") as draw:
            room = self.action(party[1], "ready", round_number=1)
            draw.assert_not_called()
        self.assertEqual((room["stage"], room["round_number"]), ("cluster", 2))
        self.assertEqual([self.player(room, p)["score"] for p in party], [500, 1000])
        self.assertEqual(len(self.game._sessions), 1)

    def test_infeasible_next_round_can_change_settings_without_resetting_target_scores_or_match_length(self):
        party, room = self.start(rounds=2)
        room = self.finish_round(party, room, [1, 0])
        with self.assertRaises(GameError) as premature:
            self.action(party[0], "configure", settings={"count": 3, "alpha": .4})
        self.assertEqual(premature.exception.status, 409)
        self.action(party[0], "ready", round_number=1)
        with patch("engine.game.sample", side_effect=SamplingError("no valid cluster set", "infeasible")):
            with self.assertRaises(GameError):
                self.action(party[1], "ready", round_number=1)
            private_room = self.service._rooms[room["id"]]
            pending_id = private_room.pending_game_id
            pending_target = self.game._sessions[pending_id].target
            before = self.get(party[0])
            with self.assertRaises(GameError) as forbidden:
                self.action(party[1], "configure", settings={"count": 3, "alpha": .4})
            self.assertEqual(forbidden.exception.status, 403)
            with self.assertRaises(GameError) as changed_length:
                self.action(party[0], "configure", settings={"count": 3, "alpha": .4}, rounds=3)
            self.assertEqual((changed_length.exception.status, changed_length.exception.code), (400, "invalid_rounds"))
            self.assertEqual(self.get(party[0]), before)
            with self.assertRaises(GameError) as still_infeasible:
                self.action(party[0], "configure", settings={"count": 3, "alpha": .4})
            self.assertEqual(still_infeasible.exception.code, "infeasible")
            self.assertEqual(private_room.pending_game_id, pending_id)
            self.assertEqual(self.game._sessions[pending_id].target, pending_target)
        with patch("engine.game.secrets.randbelow") as draw:
            room = self.action(party[0], "configure", settings={"count": 3, "alpha": .6}, rounds=2)
            draw.assert_not_called()
        self.assertEqual((room["stage"], room["round_number"], room["total_rounds"]), ("cluster", 2, 2))
        self.assertEqual(room["settings"]["alpha"], .6)
        self.assertEqual([self.player(room, p)["score"] for p in party], [500, 1000])
        self.assertEqual(private_room.game.id, pending_id)
        self.assertEqual(private_room.game.target, pending_target)
        self.assertNotIn(pending_id, json.dumps(room))
        self.assertNotIn("error", room)
        self.assertTrue(all(not p["submitted"] and not p["ready"] for p in room["players"]))

    def test_degenerate_and_disconnected_distance_scores_remain_finite(self):
        for values, expected in (((0, 0, 0), [1000, 1000]),
                                 ((0, 1, float("inf")), [0, 0])):
            with self.subTest(values=values), patch.object(
                    self.provider.space, "distance", side_effect=lambda left, right: values[right]):
                party, room = self.start()
                room = self.finish_round(party, room, [1, 2])
            self.assertEqual([self.player(room, p)["score"] for p in party], expected)
            # Strict JSON encoding forbids NaN and Infinity even when graph distances are infinite.
            json.dumps(room, allow_nan=False)

    def test_room_roster_capacity_and_expiry_are_bounded_without_evicting_active_rooms(self):
        self.service.max_rooms = 1
        self.service.max_players = 2
        host = self.create()
        guest = self.join(host)
        with self.assertRaises(GameError) as capacity:
            self.create()
        self.assertEqual(capacity.exception.status, 503)
        with self.assertRaises(GameError) as full:
            self.join(host, "Third")
        self.assertEqual(full.exception.status, 409)
        self.action(guest, "leave")
        with self.assertRaises(GameError):
            self.join(host, "Still bounded")
        self.service._rooms[host["room"]["id"]].expires = 0
        with self.assertRaises(GameError) as expired:
            self.get(host)
        self.assertEqual(expired.exception.status, 404)
        self.assertEqual(self.create()["room"]["stage"], "lobby")

    def test_member_refresh_extends_room_and_media_lifetime_but_invite_preview_does_not(self):
        party, room = self.start()
        private_room = self.service._rooms[room["id"]]
        initial_expiry = private_room.expires
        with patch("engine.multiplayer.time.monotonic", return_value=initial_expiry - 1):
            self.service.get(room["id"], None)
            self.assertEqual(private_room.expires, initial_expiry)
            self.get(party[0])
        self.assertGreater(private_room.expires, initial_expiry)
        self.assertEqual(private_room.game.expires, private_room.expires)

    def test_unreachable_race_start_keeps_lobby_and_never_inspects_audio(self):
        self.provider.space.clusters = tuple((i,) for i in range(7))
        host = self.create("race")
        self.join(host)
        with patch.object(self.catalog, "tracks", side_effect=AssertionError("Race must not inspect audio")):
            with self.assertRaises(GameError) as unreachable:
                self.action(host, "start")
        self.assertEqual((unreachable.exception.status, unreachable.exception.code), (422, "unreachable_goal"))
        self.assertEqual(self.get(host)["stage"], "lobby")
        self.assertEqual(self.game._sessions, {})
        changed = self.action(host, "configure", start_id=6, goal_id=6)
        self.assertEqual((changed["race"]["start"]["id"], changed["race"]["goal"]["id"]), (6, 6))
        self.assertEqual(self.action(host, "start")["stage"], "finished")

    def test_lobby_configuration_is_host_only_atomic_and_frozen_after_start(self):
        host = self.create(rounds=3)
        guest = self.join(host)
        initial = self.get(host)
        with self.assertRaises(GameError) as denied:
            self.action(guest, "configure", rounds=5)
        self.assertEqual(denied.exception.status, 403)
        for change in ({"settings": {"count": 5}, "rounds": 0},
                       {"settings": {"alpha": 0}, "rounds": 5}):
            with self.subTest(change=change), self.assertRaises(GameError):
                self.action(host, "configure", **change)
            self.assertEqual(self.get(host), initial)
        changed = self.action(host, "configure", rounds=20)
        self.assertEqual(changed["total_rounds"], 20)
        self.assertEqual(changed["settings"], initial["settings"])
        self.assertEqual(self.get(guest)["total_rounds"], 20)
        self.action(host, "start")
        with self.assertRaises(GameError) as active:
            self.action(host, "configure", rounds=1)
        self.assertEqual(active.exception.status, 409)

    def test_invalid_player_names_do_not_change_the_roster(self):
        host = self.create()
        for name in (None, [], "", "   ", "x" * 33, "line\nbreak", "\x00hidden"):
            with self.subTest(name=name), self.assertRaises(GameError):
                self.join(host, name)
        self.assertEqual(len(self.get(host)["players"]), 1)


if __name__ == "__main__":
    unittest.main()
