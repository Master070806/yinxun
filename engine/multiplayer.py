"""Authoritative invite rooms with private answers and synchronized barriers.

A room identifier is an invitation, not a player credential. Every mutation and
audio request also requires the separately issued player token. A single room
lock linearizes submissions, departures, and race finishes; slow preparation
never holds the room registry lock.
"""

from dataclasses import dataclass, field
import math
import secrets
from threading import Lock
import time

from .game import GameError, validate_settings
from .race import validate_race_settings


@dataclass
class _Player:
    id: str
    name: str
    token: str
    score: int = 0
    cluster_id: str = None
    genre_id: int = None
    ready: bool = False
    left: bool = False
    route: list = field(default_factory=list)


@dataclass
class _Room:
    id: str
    mode: str
    settings: dict
    total_rounds: int
    host_id: str
    expires: float
    players: dict = field(default_factory=dict)
    stage: str = "lobby"
    round_number: int = 0
    game: object = None
    pending_game_id: str = None
    result: object = None
    error: object = None
    start_id: int = None
    goal_id: int = None
    clusters: tuple = ()
    reaching_goal: frozenset = frozenset()
    winner_ids: list = field(default_factory=list)
    lock: object = field(default_factory=Lock)


class MultiplayerService:
    """Bounded in-memory rooms. Refresh reconnects with the original token."""

    def __init__(self, game_service, race_service, *, ttl_seconds=7200,
                 max_rooms=128, max_players=16):
        if game_service.catalog is not race_service.catalog:
            raise ValueError("Multiplayer modes must share the same catalog.")
        self.game_service = game_service
        self.race_service = race_service
        self.catalog = game_service.catalog
        self.provider = game_service.provider
        self.ttl_seconds = ttl_seconds
        self.max_rooms = max_rooms
        self.max_players = max_players
        self._rooms = {}
        self._rooms_lock = Lock()

    @staticmethod
    def _request(request):
        if not isinstance(request, dict):
            raise GameError("Send a request object.")
        return request

    @staticmethod
    def _name(value):
        if not isinstance(value, str):
            raise GameError("Enter a player name of 1 to 32 characters.", code="invalid_name")
        name = value.strip()
        if not 1 <= len(name) <= 32 or any(ord(char) < 32 or ord(char) == 127 for char in name):
            raise GameError("Enter a player name of 1 to 32 characters.", code="invalid_name")
        return name

    def _room(self, room_id):
        with self._rooms_lock:
            room = self._rooms.get(room_id) if isinstance(room_id, str) else None
            if room is None or room.expires <= time.monotonic():
                if room is not None:
                    del self._rooms[room_id]
                raise GameError("Room not found or expired. Create a new invitation.",
                                status=404, code="room_not_found")
            return room

    @staticmethod
    def _player(room, token):
        if isinstance(token, str) and token and token.isascii():
            for player in room.players.values():
                if secrets.compare_digest(player.token, token):
                    return player
        raise GameError("This player credential is not valid for the room.",
                        status=403, code="invalid_token")

    def _touch(self, room):
        room.expires = time.monotonic() + self.ttl_seconds
        # Private sessions must remain available for as long as their room does.
        with self.game_service._sessions_lock:
            for game_id in (room.game.id if room.game else None, room.pending_game_id):
                session = self.game_service._sessions.get(game_id)
                if session is not None:
                    session.expires = room.expires

    @staticmethod
    def _active(room):
        return [player for player in room.players.values() if not player.left]

    @staticmethod
    def _eligible(room, player):
        return room.game is not None and player.cluster_id == room.game.correct_cluster

    def create(self, request):
        request = self._request(request)
        mode = request.get("mode")
        if mode not in ("guessr", "race"):
            raise GameError("Choose multiplayer Genreguessr or Genrerace.", code="invalid_mode")
        name = self._name(request.get("name"))
        settings = (validate_settings(request.get("settings", {})) if mode == "guessr"
                    else validate_race_settings(request.get("settings", {})))
        rounds = request.get("rounds", 5) if mode == "guessr" else 1
        if isinstance(rounds, bool) or not isinstance(rounds, int) or not 1 <= rounds <= 20:
            raise GameError("Choose between 1 and 20 rounds.", code="invalid_rounds")
        start_id, goal_id = request.get("start_id"), request.get("goal_id")
        if mode == "race" and (not self.race_service._valid_id(start_id) or
                               not self.race_service._valid_id(goal_id)):
            raise GameError("Choose valid starting and destination genres.", code="invalid_genre")
        player = _Player(secrets.token_urlsafe(12), name, secrets.token_urlsafe(32))
        room = _Room(secrets.token_urlsafe(18), mode, settings, rounds,
                     player.id, time.monotonic() + self.ttl_seconds,
                     players={player.id: player}, start_id=start_id, goal_id=goal_id)
        with self._rooms_lock:
            now = time.monotonic()
            self._rooms = {key: value for key, value in self._rooms.items() if value.expires > now}
            if len(self._rooms) >= self.max_rooms:
                finished = [value for value in self._rooms.values() if value.stage == "finished"]
                if finished:
                    del self._rooms[min(finished, key=lambda value: value.expires).id]
                else:
                    raise GameError("Too many rooms are open. Please try again later.",
                                    status=503, code="room_limit")
            self._rooms[room.id] = room
        return {"room": self._snapshot(room, player), "player_id": player.id, "token": player.token}

    def join(self, room_id, request):
        request = self._request(request)
        name = self._name(request.get("name"))
        room = self._room(room_id)
        with room.lock:
            if room.stage != "lobby":
                raise GameError("This game has already started. Ask for a new invitation.",
                                status=409, code="room_started")
            # Bound the complete roster, including departures, not just active players.
            if len(room.players) >= self.max_players:
                raise GameError("This room is full.", status=409, code="room_full")
            player = _Player(secrets.token_urlsafe(12), name, secrets.token_urlsafe(32))
            room.players[player.id] = player
            self._touch(room)
            return {"room": self._snapshot(room, player), "player_id": player.id, "token": player.token}

    def get(self, room_id, token=None):
        room = self._room(room_id)
        with room.lock:
            player = self._player(room, token) if token is not None else None
            if player is not None and not player.left:
                self._touch(room)
            return self._snapshot(room, player)

    @staticmethod
    def _require_stage(room, stage):
        if room.stage != stage:
            raise GameError("The room has moved on. Refresh its current state.",
                            status=409, code="invalid_stage")

    @staticmethod
    def _require_round(room, request):
        number = request.get("round_number")
        if isinstance(number, bool) or not isinstance(number, int) or number != room.round_number:
            raise GameError("This selection belongs to another round. Refresh the room.",
                            status=409, code="stale_round")

    @staticmethod
    def _host(room, player):
        if player.id != room.host_id:
            raise GameError("Only the room host can do that.", status=403, code="host_required")

    def action(self, room_id, token, action, request):
        request = self._request(request)
        room = self._room(room_id)
        with room.lock:
            player = self._player(room, token)
            if player.left:
                raise GameError("You have left this room.", status=403, code="player_left")
            self._touch(room)
            if action == "configure":
                self._host(room, player)
                if room.stage == "lobby":
                    self._configure(room, request)
                elif (room.mode == "guessr" and room.stage == "round_result" and
                      room.error is not None and room.pending_game_id is not None):
                    self._configure_failed_round(room, request)
                else:
                    raise GameError("Settings are locked during an active game.",
                                    status=409, code="invalid_stage")
            elif action == "start":
                self._host(room, player)
                self._require_stage(room, "lobby")
                if len(self._active(room)) < 2:
                    raise GameError("Invite at least one other player before starting.",
                                    status=409, code="players_required")
                if room.mode == "guessr":
                    self._prepare_round(room)
                else:
                    self._prepare_race(room)
            elif action in ("cluster", "genre", "ready"):
                if room.mode != "guessr":
                    raise GameError("This action is only available in Genreguessr.",
                                    status=409, code="invalid_stage")
                self._require_round(room, request)
                if action == "cluster":
                    self._choose_cluster(room, player, request.get("cluster_id"))
                elif action == "genre":
                    self._choose_genre(room, player, request.get("genre_id"))
                else:
                    self._require_stage(room, "round_result")
                    player.ready = True
                    self._advance(room)
            elif action == "move":
                self._move(room, player, request)
            elif action in ("leave", "remove"):
                departing = player
                if action == "remove":
                    self._host(room, player)
                    player_id = request.get("player_id")
                    departing = room.players.get(player_id) if isinstance(player_id, str) else None
                    if departing is None:
                        raise GameError("Choose a player in this room.", code="invalid_player")
                departing.left = True
                active = self._active(room)
                if room.host_id == departing.id:
                    room.host_id = active[0].id if active else None
                self._advance(room)
            else:
                raise GameError("Unknown room action.", code="invalid_action")
            return self._snapshot(room, player)

    def _configure(self, room, request):
        """Validate a complete lobby update before applying any of its fields."""
        settings = request.get("settings", room.settings)
        settings = (validate_settings(settings) if room.mode == "guessr"
                    else validate_race_settings(settings))
        rounds = request.get("rounds", room.total_rounds) if room.mode == "guessr" else 1
        if isinstance(rounds, bool) or not isinstance(rounds, int) or not 1 <= rounds <= 20:
            raise GameError("Choose between 1 and 20 rounds.", code="invalid_rounds")
        start_id = request.get("start_id", room.start_id)
        goal_id = request.get("goal_id", room.goal_id)
        if room.mode == "race" and (not self.race_service._valid_id(start_id) or
                                   not self.race_service._valid_id(goal_id)):
            raise GameError("Choose valid starting and destination genres.", code="invalid_genre")
        room.settings = settings
        room.total_rounds = rounds
        room.start_id = start_id
        room.goal_id = goal_id
        room.error = None
        # Keep pending_game_id: a failed target is retried with the new settings.

    def _configure_failed_round(self, room, request):
        """Recover an unprepared next round without changing its target or scores."""
        settings = validate_settings(request.get("settings", room.settings))
        rounds = request.get("rounds", room.total_rounds)
        if (isinstance(rounds, bool) or not isinstance(rounds, int) or
                rounds != room.total_rounds):
            raise GameError("The number of rounds is fixed after the game starts.",
                            code="invalid_rounds")
        room.settings = settings
        # All players had already readied before next-round preparation failed.
        # Retry immediately so there is no intermediate ready-but-locked state.
        # _prepare_round preserves both the pending target and prior results on
        # failure, and resets readiness only after successful preparation.
        self._prepare_round(room)

    def _preparation_error(self, room, error):
        # GameService error IDs are bearer credentials for its single-player API.
        # Keep them only in the private room; never forward that payload.
        # Room preparation always stays at a retryable boundary. This also
        # covers transient service capacity errors whose single-player payload
        # does not carry a retry flag or a newly allocated private session.
        safe = GameError(str(error), status=error.status, code=error.code, retryable=True)
        room.error = dict(safe.payload)
        return safe

    def _prepare_round(self, room):
        try:
            prepared = self.game_service.start(room.settings, retry_id=room.pending_game_id)
        except GameError as error:
            game_id = error.payload.get("id")
            if game_id is not None:
                room.pending_game_id = game_id
            self._touch(room)
            raise self._preparation_error(room, error) from None
        session = self.game_service._session(prepared["id"])
        previous = room.game
        room.game = session
        room.pending_game_id = None
        room.round_number += 1
        room.stage = "cluster"
        room.result = None
        room.error = None
        for player in room.players.values():
            player.cluster_id = None
            player.genre_id = None
            player.ready = False
        # Completed rounds are summarized in scores and do not consume the
        # single-player registry's capacity throughout a twenty-round room.
        if previous is not None:
            with self.game_service._sessions_lock:
                self.game_service._sessions.pop(previous.id, None)
        self._touch(room)

    def _prepare_race(self, room):
        try:
            clusters, reaching_goal = self.race_service._geometry(room.settings, room.goal_id)
            if room.start_id not in reaching_goal:
                raise GameError("The destination cannot be reached from this starting genre "
                                "with these settings.", status=422, code="unreachable_goal")
        except GameError as error:
            raise self._preparation_error(room, error) from None
        room.clusters = clusters
        room.reaching_goal = reaching_goal
        room.round_number = 1
        room.error = None
        for player in self._active(room):
            player.route = [room.start_id]
        room.stage = "race"
        if room.start_id == room.goal_id:
            room.stage = "finished"
            room.winner_ids = [player.id for player in self._active(room)]

    def _choose_cluster(self, room, player, cluster_id):
        self._require_stage(room, "cluster")
        if not isinstance(cluster_id, str) or cluster_id not in room.game.clusters:
            raise GameError("Choose one of this round's clusters.", code="invalid_selection")
        if player.cluster_id is not None and player.cluster_id != cluster_id:
            raise GameError("Your selection has already been submitted.",
                            status=409, code="already_submitted")
        player.cluster_id = cluster_id
        self._advance(room)

    def _choose_genre(self, room, player, genre_id):
        self._require_stage(room, "genre")
        if not self._eligible(room, player):
            raise GameError("Wait for the next round after a missed cluster.",
                            status=403, code="not_eligible")
        if (isinstance(genre_id, bool) or not isinstance(genre_id, int) or
                genre_id not in room.game.clusters[room.game.correct_cluster]):
            raise GameError("Choose a genre in this round's cluster.", code="invalid_selection")
        if player.genre_id is not None and player.genre_id != genre_id:
            raise GameError("Your selection has already been submitted.",
                            status=409, code="already_submitted")
        player.genre_id = genre_id
        self._advance(room)

    def _advance(self, room):
        active = self._active(room)
        if not active:
            if room.mode == "guessr" and room.stage in ("cluster", "genre"):
                self._finish_round(room)
            room.stage = "finished"
            return
        if room.mode != "guessr":
            return
        if room.stage == "cluster" and all(player.cluster_id is not None for player in active):
            eligible = [player for player in active if self._eligible(room, player)]
            if eligible:
                self.game_service.choose_cluster(room.game.id, room.game.correct_cluster)
                room.stage = "genre"
            else:
                self._finish_round(room)
        if room.stage == "genre" and all(player.genre_id is not None for player in active
                                          if self._eligible(room, player)):
            self._finish_round(room)
        if room.stage == "round_result" and all(player.ready for player in active):
            if room.round_number == room.total_rounds:
                room.stage = "finished"
                best = max(player.score for player in active)
                room.winner_ids = [player.id for player in active if player.score == best]
            else:
                self._prepare_round(room)

    def _finish_round(self, room):
        session = room.game
        finite = [value for value in session.answer_distances.values() if math.isfinite(value)]
        diameter = max(finite, default=0)
        results = []
        for player in room.players.values():
            eligible = self._eligible(room, player)
            points = 0
            distance = None
            if eligible and player.genre_id is not None:
                distance = session.answer_distances[player.genre_id]
                if player.genre_id == session.target:
                    points = 1000
                elif math.isfinite(distance):
                    # Distinct genres can have zero metric distance.
                    points = (1000 if distance == 0 else
                              round(1000 * max(0, min(1, 1 - distance / diameter)))
                              if diameter > 0 else 0)
            player.score += points
            player.ready = False
            item = {"id": player.id, "name": player.name, "score": player.score,
                    "round_score": points, "cluster_correct": eligible, "left": player.left}
            if player.genre_id is not None:
                item["guess"] = self.game_service._genre(player.genre_id)
                item["distance"] = distance if distance is not None and math.isfinite(distance) else None
            results.append(item)
        room.result = {"target": self.game_service._revealed_genre(session.target),
                       "players": results}
        room.stage = "round_result"
        session.stage = "finished"

    def _move(self, room, player, request):
        self._require_stage(room, "race")
        revision = request.get("revision")
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
            raise GameError("Send the current route revision.", code="invalid_revision")
        if revision != len(player.route) - 1:
            raise GameError("Your route has advanced. Refresh the current neighborhood.",
                            status=409, code="stale_move")
        genre_id = request.get("genre_id")
        current = player.route[-1]
        if (not self.race_service._valid_id(genre_id) or genre_id == current or
                genre_id not in room.clusters[current]):
            raise GameError("Choose another genre in the current neighborhood.", code="invalid_move")
        player.route.append(genre_id)
        if genre_id == room.goal_id:
            room.winner_ids = [player.id]
            room.stage = "finished"

    def _snapshot(self, room, viewer):
        players = []
        for player in room.players.values():
            submitted = (player.cluster_id is not None if room.stage == "cluster" else
                         player.genre_id is not None if room.stage == "genre" else False)
            players.append({"id": player.id, "name": player.name, "score": player.score,
                            "submitted": submitted, "ready": player.ready, "left": player.left,
                            "eligible": (self._eligible(room, player) if room.mode == "guessr"
                                         and room.stage in ("genre", "round_result", "finished")
                                         else None)})
        snapshot = {"id": room.id, "mode": room.mode, "stage": room.stage,
                    "settings": dict(room.settings), "round_number": room.round_number,
                    "total_rounds": room.total_rounds, "host_id": room.host_id,
                    "self_id": viewer.id if viewer is not None else None, "players": players,
                    "winner_ids": list(room.winner_ids)}
        if room.error is not None:
            snapshot["error"] = dict(room.error)
        if room.mode == "race" and room.stage == "lobby":
            snapshot["race"] = {"start": self.race_service._genre(room.start_id),
                                "goal": self.race_service._genre(room.goal_id)}
        # An invitation alone reveals the lobby and participation, never live
        # neighborhoods, clue URLs, another player's route, or an answer.
        if viewer is None:
            return snapshot
        if room.mode == "guessr":
            if not viewer.left and room.stage == "cluster":
                snapshot["game"] = {
                    "clusters": [self.game_service._cluster(room.game, key)
                                 for key in room.game.clusters],
                    "audio": f"/api/rooms/{room.id}/audio/{room.round_number}/clue/1",
                    "audio_available": self.game_service._audio_available(room.game, 1)}
            elif not viewer.left and room.stage == "genre" and self._eligible(room, viewer):
                snapshot["game"] = {
                    "cluster": self.game_service._cluster(room.game, room.game.correct_cluster),
                    "audio": f"/api/rooms/{room.id}/audio/{room.round_number}/clue/2",
                    "audio_available": self.game_service._audio_available(room.game, 2)}
            if room.result is not None:
                snapshot["result"] = {"target": dict(room.result["target"]),
                                      "players": [{**item, **({"guess": dict(item["guess"])}
                                                   if "guess" in item else {})}
                                                  for item in room.result["players"]]}
        elif room.stage in ("race", "finished"):
            if viewer.route and not viewer.left:
                current = viewer.route[-1]
                snapshot["race"] = {
                    "current": self.race_service._genre(current),
                    "goal": self.race_service._genre(room.goal_id),
                    "cluster": {"center_id": current,
                                "genres": [self.race_service._genre(index)
                                           for index in room.clusters[current]]
                                if room.stage == "race" else []},
                    "route": [self.race_service._genre(index) for index in viewer.route],
                    "moves": len(viewer.route) - 1, "revision": len(viewer.route) - 1,
                    "goal_reachable": current in room.reaching_goal}
            if room.stage == "finished":
                snapshot["routes"] = [
                    {"id": player.id, "name": player.name, "left": player.left,
                     "route": [self.race_service._genre(index) for index in player.route],
                     "moves": max(0, len(player.route) - 1)}
                    for player in room.players.values()]
        return snapshot

    def audio_source(self, room_id, token, round_number, kind, genre_id=None):
        """Resolve private media only after checking the requesting player's stage."""
        room = self._room(room_id)
        with room.lock:
            player = self._player(room, token)
            if player.left:
                raise GameError("You have left this room.", status=403, code="player_left")
            if room.mode != "guessr" or room.game is None:
                raise GameError("No sample is available here.", status=404, code="sample_not_found")
            self._require_round(room, {"round_number": round_number})
            if room.stage not in ("cluster", "genre"):
                raise GameError("This round is no longer playing.", status=409, code="invalid_stage")
            if isinstance(kind, bool):
                raise GameError("Unknown sample.", status=404, code="sample_not_found")
            if kind in ("clue1", "1", 1):
                source = self.game_service.audio_source(room.game.id, 1)
            elif kind in ("clue2", "2", 2, "candidate"):
                if room.stage != "genre" or not self._eligible(room, player):
                    raise GameError("This sample is not unlocked for you.",
                                    status=403, code="not_eligible")
                if kind == "candidate":
                    source = self.game_service.candidate_audio_source(room.game.id, genre_id)
                else:
                    source = self.game_service.audio_source(room.game.id, 2)
            else:
                raise GameError("Unknown sample.", status=404, code="sample_not_found")
            self._touch(room)
            return dict(source)
