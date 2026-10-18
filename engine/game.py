"""Server-owned Genreguessr rounds; answers and source tracks stay private."""

from dataclasses import dataclass, field
import math
from random import SystemRandom
import secrets
from threading import Lock
import time
from urllib.parse import urlsplit

from .metrics import MetricProvider
from .sampling import SamplingError, sample


class GameError(Exception):
    """An error whose deliberately limited payload is safe to send to a player."""

    def __init__(self, message, status=400, code="invalid_request", game_id=None,
                 retryable=False):
        super().__init__(message)
        self.status = status
        self.code = code
        self.payload = {"error": message, "code": code, "retryable": retryable}
        if game_id is not None:
            self.payload["id"] = game_id


@dataclass
class _Session:
    id: str
    target: int
    settings: dict
    expires: float
    stage: str = "preparing"
    cluster_response: dict = field(default_factory=dict)
    result: dict = field(default_factory=dict)
    chosen_genre: int = None
    tracks: tuple = ()
    answer_distances: dict = field(default_factory=dict)
    clusters: dict = field(default_factory=dict)
    correct_cluster: str = None
    chosen_cluster: str = None
    unlocked_round: int = 0
    comparison_tracks: dict = field(default_factory=dict)
    lock: object = field(default_factory=Lock)


def _preview_identity(track):
    """Compare preview resources independently of CDN query tokens and fragments."""
    url = track.get("preview_url")
    if not isinstance(url, str) or not url:
        return None
    parts = urlsplit(url)
    return (parts.scheme.lower(), parts.hostname, parts.port or (443 if parts.scheme == "https" else 80),
            parts.path)


def _number(settings, key, default, minimum, maximum, *, strict_min=False):
    value = settings.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GameError(f"{key} must be a number.", code="invalid_settings")
    try:
        value = float(value)
    except (ValueError, OverflowError):
        raise GameError(f"{key} is outside its permitted range.", code="invalid_settings") from None
    if (not math.isfinite(value) or value > maximum or
            (value <= minimum if strict_min else value < minimum)):
        raise GameError(f"{key} is outside its permitted range.", code="invalid_settings")
    return value


def validate_settings(settings):
    """Validate without rounding, clamping, or changing an active parameter."""
    if not isinstance(settings, dict):
        raise GameError("Choose a metric and its parameters.", code="invalid_settings")
    metric = settings.get("metric", "xyrgb")
    if metric not in ("xyrgb", "graph", "kernel"):
        raise GameError("Choose a supported metric.", code="invalid_settings")
    count = settings.get("count", 4)
    if isinstance(count, bool) or not isinstance(count, int) or not 3 <= count <= 10:
        raise GameError("Choose between 3 and 10 clusters.", code="invalid_settings")
    result = {"metric": metric, "count": count}
    if metric != "graph":
        cluster_size = settings.get("cluster_size", 20)
        if (isinstance(cluster_size, bool) or not isinstance(cluster_size, int) or
                not 5 <= cluster_size <= 25):
            raise GameError("Choose between 5 and 25 genres per cluster.", code="invalid_settings")
        result["cluster_size"] = cluster_size
    result["separation"] = _number(
        settings, "separation", 3 if metric == "graph" else .65,
        0, 2 if metric == "kernel" else 10,
    )
    if metric == "graph" and not result["separation"].is_integer():
        raise GameError("Graph separation must be a whole number.", code="invalid_settings")
    if metric == "xyrgb":
        result["alpha"] = _number(settings, "alpha", .8, 0, 1, strict_min=True)
        if result["alpha"] == 1:
            raise GameError("Position weight must be strictly between 0 and 1.", code="invalid_settings")
    if metric == "kernel":
        result["opposition"] = _number(settings, "opposition", 1, 0, 1e6, strict_min=True)
        result["regularization"] = _number(settings, "regularization", .1, 0, 1e6, strict_min=True)
    return result


class GameService:
    """Bounded, expiring sessions with one-way, independently locked state."""

    def __init__(self, catalog, provider=None, *, ttl_seconds=7200,
                 max_sessions=256, max_attempts=5000):
        self.catalog = catalog
        self.provider = provider if provider is not None else MetricProvider(catalog, cache_size=2)
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions
        self.max_attempts = max_attempts
        self._sessions = {}
        self._sessions_lock = Lock()
        self._random = SystemRandom()
        self._genres = {genre["id"]: genre for genre in catalog.genres}
        if not self._genres or len(self._genres) != len(catalog.genres):
            raise ValueError("The genre catalog must have unique IDs and cannot be empty.")

    def _new_session(self, settings):
        now = time.monotonic()
        with self._sessions_lock:
            self._sessions = {
                key: session for key, session in self._sessions.items()
                if session.expires > now
            }
            if len(self._sessions) >= self.max_sessions:
                finished = [s for s in self._sessions.values() if s.stage == "finished"]
                if finished:
                    del self._sessions[min(finished, key=lambda s: s.expires).id]
                else:
                    raise GameError("Too many games are open. Please try again later.",
                                    status=503, code="session_limit")
            game_id = secrets.token_urlsafe(24)
            # Draw from the full catalog before inspecting media or metric feasibility.
            target = self.catalog.genres[secrets.randbelow(len(self.catalog.genres))]["id"]
            session = _Session(game_id, target, settings, now + self.ttl_seconds)
            self._sessions[game_id] = session
            return session

    def _session(self, game_id):
        if not isinstance(game_id, str):
            raise GameError("Game not found or expired.", status=404, code="game_not_found")
        with self._sessions_lock:
            session = self._sessions.get(game_id)
            if session is None or session.expires <= time.monotonic():
                if session is not None:
                    del self._sessions[game_id]
                raise GameError("Game not found or expired.", status=404, code="game_not_found")
            return session

    def _genre(self, genre_id):
        genre = self._genres[genre_id]
        return {"id": genre["id"], "name": genre["name"], "color": genre["color"]}

    def _revealed_genre(self, genre_id):
        return {**self._genre(genre_id),
                "url": "https://everynoise.com/" + self.catalog.paths[genre_id]}

    def _cluster(self, session, cluster_id):
        return {"id": cluster_id,
                "genres": [self._genre(i) for i in session.clusters[cluster_id]]}

    @staticmethod
    def _audio_available(session, round_number):
        track = session.tracks[round_number - 1]
        return bool(track.get("preview_url") or track.get("track_id"))

    @staticmethod
    def _fail(session, message, *, code, status=422):
        session.stage = "failed"
        return GameError(message, status=status, code=code, game_id=session.id, retryable=True)

    def start(self, settings, retry_id=None):
        settings = validate_settings(settings)
        session = self._new_session(settings) if retry_id is None else self._session(retry_id)
        # Preparation is expensive, so it owns only this session's lock, never the registry lock.
        if not session.lock.acquire(blocking=False):
            raise GameError("This game is still being prepared.", status=409, code="game_busy",
                            game_id=session.id)
        try:
            if retry_id is not None and session.stage != "failed":
                raise GameError("Only a game that failed to start can be retried.",
                                status=409, code="invalid_stage", game_id=session.id)
            session.stage = "preparing"
            session.settings = settings
            session.expires = time.monotonic() + self.ttl_seconds
            try:
                tracks = tuple(self.catalog.tracks(session.target))[:2]
                if len(tracks) != 2:
                    raise self._fail(session, "This genre does not have two available samples. "
                                     "Your target has been kept for retry.", code="missing_samples")
                # A track ID can be resolved by the media layer if its cached preview URL is absent.
                session.tracks = tracks
                space = self.provider.get(settings)
                result = sample(space, session.target, settings["count"],
                                settings["separation"], rng=self._random,
                                max_attempts=self.max_attempts)
                members = [list(cluster) for cluster in result.clusters]
                if (len(members) != settings["count"] or
                        sum(session.target in cluster for cluster in members) != 1 or
                        any(not cluster or len(set(cluster)) != len(cluster) or
                            any(i not in self._genres for i in cluster) for cluster in members)):
                    raise RuntimeError("Sampler returned an invalid game.")
                self._random.shuffle(members)
                session.clusters = {}
                for cluster in members:
                    # Nearest-neighbor order reveals a center, so do not publish it.
                    self._random.shuffle(cluster)
                    cluster_id = secrets.token_urlsafe(12)
                    session.clusters[cluster_id] = tuple(cluster)
                    if session.target in cluster:
                        session.correct_cluster = cluster_id
                        # Keep just the possible answer distances, not a dense matrix per session.
                        session.answer_distances = {
                            genre_id: float(space.distance(session.target, genre_id))
                            for genre_id in cluster
                        }
                session.unlocked_round = 1
                session.stage = "round-one"
                return {"id": session.id, "stage": session.stage,
                        "clusters": [self._cluster(session, i) for i in session.clusters],
                        "audio": f"/api/games/{session.id}/audio/1",
                        "audio_available": self._audio_available(session, 1)}
            except SamplingError as error:
                code = error.code
                message = ("No valid cluster set exists for this target and arrangement."
                           if code == "infeasible" else
                           "A valid cluster set was not found within the attempt limit.")
                raise self._fail(session, message + " Retry keeps the same target.", code=code) from error
            except GameError:
                raise
            except Exception as error:
                raise self._fail(session, "The game could not be prepared. "
                                 "Your target has been kept for retry.",
                                 code="preparation_failed", status=503) from error
        finally:
            session.lock.release()

    def choose_cluster(self, game_id, cluster_id):
        session = self._session(game_id)
        with session.lock:
            if isinstance(cluster_id, str) and cluster_id == session.chosen_cluster and session.cluster_response:
                return session.cluster_response
            if session.stage != "round-one":
                raise GameError("This round is no longer accepting a selection.",
                                status=409, code="invalid_stage")
            if not isinstance(cluster_id, str) or cluster_id not in session.clusters:
                raise GameError("Choose one of this game's clusters.", code="invalid_selection")
            if cluster_id != session.correct_cluster:
                response = {"id": session.id, "stage": "finished", "correct": False,
                            "target": self._revealed_genre(session.target)}
            else:
                response = {"id": session.id, "stage": "final",
                    "cluster": self._cluster(session, cluster_id),
                    "audio": f"/api/games/{session.id}/audio/2",
                    "audio_available": self._audio_available(session, 2)}
            session.chosen_cluster = cluster_id
            session.stage = response["stage"]
            session.cluster_response = response
            session.expires = time.monotonic() + self.ttl_seconds
            if session.stage == "final":
                session.unlocked_round = 2
            else:
                session.result = response
            return response

    def choose_genre(self, game_id, genre_id):
        session = self._session(game_id)
        with session.lock:
            if type(genre_id) is int and genre_id == session.chosen_genre and session.result:
                return session.result
            if session.stage != "final":
                raise GameError("This round is not accepting an answer.",
                                status=409, code="invalid_stage")
            if (isinstance(genre_id, bool) or not isinstance(genre_id, int) or
                    genre_id not in session.clusters[session.chosen_cluster]):
                raise GameError("Choose a genre in the selected cluster.", code="invalid_selection")
            distance = session.answer_distances[genre_id]
            result = {"id": session.id, "stage": "finished",
                    "correct": genre_id == session.target, "target": self._revealed_genre(session.target),
                    "distance": distance if math.isfinite(distance) else None}
            session.stage = "finished"
            session.chosen_genre = genre_id
            session.result = result
            session.expires = time.monotonic() + self.ttl_seconds
            return result

    def get(self, game_id):
        """Recover a lost response without accepting a second answer or leaking a target."""
        session = self._session(game_id)
        with session.lock:
            return session.result or session.cluster_response or {"id": session.id, "stage": session.stage}

    def audio_source(self, game_id, round_number):
        """Return private track metadata for the server's media proxy, never its JSON API."""
        session = self._session(game_id)
        with session.lock:
            if (isinstance(round_number, bool) or not isinstance(round_number, int) or
                    round_number not in (1, 2)):
                raise GameError("Unknown sample.", status=404, code="sample_not_found")
            if session.stage in ("failed", "preparing") or round_number > session.unlocked_round:
                raise GameError("This sample is not unlocked.", status=409, code="invalid_stage")
            return session.tracks[round_number - 1]

    def candidate_audio_source(self, game_id, genre_id):
        """Choose one private comparison sample per final-round candidate, excluding both clues."""
        session = self._session(game_id)
        with session.lock:
            if session.stage != "final":
                raise GameError("Comparison samples are only available during the final round.",
                                status=409, code="invalid_stage")
            if (isinstance(genre_id, bool) or not isinstance(genre_id, int) or
                    genre_id not in session.clusters[session.chosen_cluster]):
                raise GameError("Choose a genre in the selected cluster.", code="invalid_selection")
            if genre_id not in session.comparison_tracks:
                clue_ids = {track["track_id"] for track in session.tracks if track.get("track_id")}
                clue_previews = {identity for track in session.tracks
                                 if (identity := _preview_identity(track)) is not None}
                try:
                    # Catalog supplies validated source records, including candidates' own first two.
                    eligible = [track for track in self.catalog.samples(genre_id)
                                if (track.get("preview_url") or track.get("track_id"))
                                and track.get("track_id") not in clue_ids
                                and _preview_identity(track) not in clue_previews]
                except Exception as error:
                    raise GameError("This comparison sample is currently unavailable.", status=502,
                                    code="audio_unavailable") from error
                session.comparison_tracks[genre_id] = dict(self._random.choice(eligible)) if eligible else None
            track = session.comparison_tracks[genre_id]
            if track is None:
                raise GameError("No comparison sample is available for this genre.", status=502,
                                code="audio_unavailable")
            session.expires = time.monotonic() + self.ttl_seconds
            return dict(track)
