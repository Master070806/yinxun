"""Genrerace walks the selected metric's neighborhoods on the complete catalog."""

from collections import deque
from dataclasses import dataclass, field
import secrets
from threading import Lock
import time
from types import MappingProxyType

from .game import GameError, validate_settings
from .metrics import MetricProvider


def validate_race_settings(settings):
    if not isinstance(settings, dict):
        raise GameError("Choose a metric and its parameters.", code="invalid_settings")
    # Reuse the metric validation without importing Genreguessr's sampling controls.
    selected = {key: settings[key] for key in
                ("metric", "cluster_size", "alpha", "opposition", "regularization")
                if key in settings}
    selected.setdefault("cluster_size", 12)
    normalized = validate_settings({**selected, "count": 3, "separation": 0})
    del normalized["count"]
    del normalized["separation"]
    return normalized


@dataclass
class _Race:
    id: str
    goal: int
    settings: object
    clusters: tuple
    reaching_goal: frozenset
    route: list
    expires: float
    lock: object = field(default_factory=Lock)


class RaceService:
    """Expiring server-owned routes with immutable neighborhoods and revision checks."""

    def __init__(self, catalog, provider=None, ttl_seconds=7200, max_sessions=128):
        self.catalog = catalog
        if (not catalog.genres or any(
                isinstance(genre.get("id"), bool) or not isinstance(genre.get("id"), int) or
                genre["id"] != index for index, genre in enumerate(catalog.genres))):
            raise ValueError("The full catalog must use contiguous IDs in catalog order.")
        self._genres = tuple({key: genre[key] for key in ("id", "name", "color")}
                             for genre in catalog.genres)
        self.provider = provider if provider is not None else MetricProvider(catalog, cache_size=2)
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions
        self._sessions = {}
        self._sessions_lock = Lock()

    def _valid_id(self, genre_id):
        return (isinstance(genre_id, int) and not isinstance(genre_id, bool) and
                0 <= genre_id < len(self._genres))

    def _genre(self, genre_id):
        return dict(self._genres[genre_id])

    def _snapshot(self, race):
        current = race.route[-1]
        won = current == race.goal
        return {
            "id": race.id,
            "stage": "win" if won else "race",
            "current": self._genre(current),
            "goal": self._genre(race.goal),
            "cluster": {"center_id": current,
                        "genres": [] if won else [self._genre(i) for i in race.clusters[current]]},
            "route": [self._genre(i) for i in race.route],
            "moves": len(race.route) - 1,
            "revision": len(race.route) - 1,
            "goal_reachable": current in race.reaching_goal,
            "catalog_size": len(self._genres),
            "settings": dict(race.settings),
        }

    def _session(self, race_id):
        with self._sessions_lock:
            race = self._sessions.get(race_id) if isinstance(race_id, str) else None
            if race is None or race.expires <= time.monotonic():
                if race is not None:
                    del self._sessions[race_id]
                raise GameError("Race not found or expired.", status=404, code="race_not_found")
            return race

    def _geometry(self, settings, goal_id):
        try:
            space = self.provider.get(settings)
            clusters = tuple(tuple(row) for row in space.clusters)
            if len(clusters) != len(self._genres):
                raise ValueError("The metric must cover every genre in the catalog.")
            for center, members in enumerate(clusters):
                if (center not in members or len(set(members)) != len(members) or
                        any(not self._valid_id(member) for member in members)):
                    raise ValueError("Invalid full-catalog neighborhood.")
            reaching_goal = {goal_id}
            pending = deque([goal_id])
            while pending:
                destination = pending.popleft()
                # Nearest-k membership is directed even though its underlying distance is symmetric.
                for source in space.reverse_clusters(destination):
                    if not self._valid_id(source) or destination not in clusters[source]:
                        raise ValueError("Invalid reverse neighborhood.")
                    if source not in reaching_goal:
                        reaching_goal.add(source)
                        pending.append(source)
            # Only sparse immutable rows survive this method; do not pin a dense metric matrix.
            return clusters, frozenset(reaching_goal)
        except Exception as error:
            raise GameError("The selected metric could not be prepared. Please check its parameters.",
                            status=503, code="geometry_unavailable") from error

    def start(self, start_id, goal_id, settings):
        if not self._valid_id(start_id) or not self._valid_id(goal_id):
            raise GameError("Choose valid starting and destination genres.", code="invalid_genre")
        settings = validate_race_settings(settings)
        clusters, reaching_goal = self._geometry(settings, goal_id)
        if start_id not in reaching_goal:
            raise GameError("The destination cannot be reached from this starting genre with these settings.",
                            status=422, code="unreachable_goal")
        now = time.monotonic()
        with self._sessions_lock:
            self._sessions = {key: race for key, race in self._sessions.items() if race.expires > now}
            if len(self._sessions) >= self.max_sessions:
                finished = [race for race in self._sessions.values() if race.route[-1] == race.goal]
                if finished:
                    del self._sessions[min(finished, key=lambda race: race.expires).id]
                else:
                    raise GameError("Too many races are open. Please try again later.",
                                    status=503, code="session_limit")
            race_id = secrets.token_urlsafe(24)
            race = _Race(race_id, goal_id, MappingProxyType(dict(settings)), clusters,
                         reaching_goal, [start_id], now + self.ttl_seconds)
            self._sessions[race_id] = race
        return self._snapshot(race)

    def get(self, race_id):
        race = self._session(race_id)
        with race.lock:
            return self._snapshot(race)

    def move(self, race_id, genre_id, revision):
        race = self._session(race_id)
        with race.lock:
            if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
                raise GameError("Send the current race revision.", code="invalid_revision")
            if revision != len(race.route) - 1:
                error = GameError("The race has advanced. Continue from its current neighborhood.",
                                  status=409, code="stale_move")
                error.payload["race"] = self._snapshot(race)
                raise error
            current = race.route[-1]
            if current == race.goal:
                raise GameError("This race has finished.", status=409, code="invalid_stage")
            if (not self._valid_id(genre_id) or genre_id == current or
                    genre_id not in race.clusters[current]):
                raise GameError("Choose another genre in the current neighborhood.", code="invalid_move")
            race.route.append(genre_id)
            race.expires = time.monotonic() + self.ttl_seconds
            return self._snapshot(race)
