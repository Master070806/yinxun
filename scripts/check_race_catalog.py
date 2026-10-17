#!/usr/bin/env python3
"""Optional offline Genrerace audit against the complete local Every Noise crawl.

Requires the source crawl and NumPy/SciPy, so this is deliberately separate from
the fixture-only CI suite. It makes no network requests and fetches no audio.
"""

import argparse
from collections import deque
import gc
import json
from pathlib import Path
import random
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def forward_paths(clusters, start):
    """Independent BFS on the directed neighborhood relation."""
    parents = {start: None}
    depths = {start: 0}
    pending = deque([start])
    while pending:
        current = pending.popleft()
        for neighbor in clusters[current]:
            if neighbor not in parents:
                parents[neighbor] = current
                depths[neighbor] = depths[current] + 1
                pending.append(neighbor)
    return parents, depths


def reverse_reachable(clusters, goal):
    """Rebuild reverse edges independently of MetricSpace.reverse_clusters."""
    incoming = [[] for _ in clusters]
    for source, neighbors in enumerate(clusters):
        for destination in neighbors:
            incoming[destination].append(source)
    seen, pending = {goal}, deque([goal])
    while pending:
        destination = pending.popleft()
        for source in incoming[destination]:
            if source not in seen:
                seen.add(source)
                pending.append(source)
    return seen


def choose_route(clusters):
    """Exercise IDs beyond the legacy 5,453-row map and at least three moves."""
    for start in range(len(clusters) - 1, 5452, -1):
        parents, depths = forward_paths(clusters, start)
        goals = [genre for genre, depth in depths.items() if genre >= 5453 and depth >= 3]
        if not goals:
            continue
        goal = min(goals, key=lambda genre: (depths[genre], genre))
        route = [goal]
        while route[-1] != start:
            route.append(parents[route[-1]])
        return list(reversed(route))
    raise AssertionError("No multi-hop route with two high catalog IDs was found.")


def check_neighborhood(space, center, size):
    """Compare nearest-k against a full independent stable sort, not a fixture."""
    count = len(space.clusters)
    others = sorted((genre for genre in range(count) if genre != center),
                    key=lambda genre: (space.distance(center, genre), genre))
    expected = {center, *others[:size - 1]}
    actual = space.clusters[center]
    assert len(actual) == size and set(actual) == expected, (space.kind, center)


def check_snapshot(snapshot, space, expected_route, goal, reaching_goal):
    current = expected_route[-1]
    assert snapshot["catalog_size"] == len(space.clusters)
    assert snapshot["current"]["id"] == current
    assert snapshot["goal"]["id"] == goal
    assert snapshot["cluster"]["center_id"] == current
    assert [genre["id"] for genre in snapshot["route"]] == expected_route
    assert snapshot["moves"] == snapshot["revision"] == len(expected_route) - 1
    assert snapshot["goal_reachable"] == (current in reaching_goal)
    members = [genre["id"] for genre in snapshot["cluster"]["genres"]]
    if current == goal:
        assert snapshot["stage"] == "win" and members == []
    else:
        assert snapshot["stage"] == "race"
        assert len(members) == len(set(members))
        assert set(members) == set(space.clusters[current]), "Neighborhood was truncated or augmented."


def audit_mode(catalog, provider, settings, sample_rows):
    import numpy as np

    from engine.game import GameError
    from engine.race import RaceService

    started = time.perf_counter()
    space = provider.get(settings)
    count = len(catalog.genres)
    assert space.kind == settings["metric"]
    assert space.distances.shape == (count, count) and space.distances.dtype == np.float64
    assert len(space.clusters) == count
    assert all(center in cluster and len(cluster) == len(set(cluster))
               and all(0 <= genre < count for genre in cluster)
               for center, cluster in enumerate(space.clusters))
    np.testing.assert_array_equal(np.diag(space.distances), np.zeros(count))

    if space.kind == "graph":
        # Check EVERY ball directly against source adjacency, including isolates.
        for center, neighbors in enumerate(catalog.near):
            assert set(space.clusters[center]) == {center, *neighbors}
        for center in sample_rows:
            _, depths = forward_paths(space.clusters, center)
            expected = np.array([depths.get(genre, np.inf) for genre in range(count)])
            np.testing.assert_array_equal(space.distances[center], expected)
    else:
        size = settings["cluster_size"]
        assert all(len(cluster) == size for cluster in space.clusters)
        assert np.isfinite(space.distances).all()
        for center in sample_rows:
            check_neighborhood(space, center, size)
            np.testing.assert_array_equal(space.distances[center], space.distances[:, center])
        if space.kind == "xyrgb":
            xy = np.array([[genre["x"], genre["y"]] for genre in catalog.genres], dtype=float)
            rgb = np.array([[int(genre["color"][index:index + 2], 16) for index in (1, 3, 5)]
                            for genre in catalog.genres], dtype=float)
            # Twice the unbiased block variance equals mean squared distinct-pair distance.
            spatial_scale = 2 * np.var(xy, axis=0, ddof=1).sum()
            color_scale = 2 * np.var(rgb, axis=0, ddof=1).sum()
            alpha = settings["alpha"]
            for center in sample_rows:
                expected = np.sqrt(alpha * ((xy - xy[center]) ** 2).sum(axis=1) / spatial_scale
                                   + (1 - alpha) * ((rgb - rgb[center]) ** 2).sum(axis=1) / color_scale)
                np.testing.assert_allclose(space.distances[center], expected, rtol=1e-12, atol=1e-12)
        else:
            # Formula correctness has independent small-matrix unit tests; here
            # verify the real full-universe normalized kernel distance and kNN.
            assert (space.distances >= 0).all() and (space.distances <= 2).all()

    route = choose_route(space.clusters)
    assert len(route) >= 4 and route[0] >= 5453 and route[-1] >= 5453
    start, goal = route[0], route[-1]
    reaching_goal = reverse_reachable(space.clusters, goal)
    service = RaceService(catalog, provider=provider)
    snapshot = service.start(start, goal, settings)
    check_snapshot(snapshot, space, route[:1], goal, reaching_goal)
    assert goal not in space.clusters[start], "Audit route must exercise multiple neighborhoods."
    try:
        service.move(snapshot["id"], goal, snapshot["revision"])
    except GameError as error:
        assert error.status == 400 and error.code == "invalid_move"
    else:
        raise AssertionError("The service allowed a jump to a non-neighbor destination.")
    for index, destination in enumerate(route[1:], 1):
        if space.kind != "graph":
            check_neighborhood(space, snapshot["current"]["id"], settings["cluster_size"])
        snapshot = service.move(snapshot["id"], destination, snapshot["revision"])
        check_snapshot(snapshot, space, route[:index + 1], goal, reaching_goal)
        check_snapshot(service.get(snapshot["id"]), space, route[:index + 1], goal, reaching_goal)

    unreachable_checked = False
    unreachable = next((genre for genre in range(count) if genre not in reaching_goal), None)
    if unreachable is not None:
        try:
            service.start(unreachable, goal, settings)
        except GameError as error:
            assert error.status == 422 and error.code == "unreachable_goal"
            unreachable_checked = True
        else:
            raise AssertionError("An unreachable initial destination was accepted.")

    # A directed kNN move may legally leave the goal's reverse-reachable set.
    trap = next(((source, destination) for source in sorted(reaching_goal) if source != goal
                 for destination in space.clusters[source] if destination not in reaching_goal), None)
    if trap is not None:
        before = service.start(trap[0], goal, settings)
        after = service.move(before["id"], trap[1], before["revision"])
        check_snapshot(after, space, list(trap), goal, reaching_goal)
        assert after["goal_reachable"] is False and after["stage"] == "race"

    return {"metric": space.kind, "genres": count, "matrix": list(space.distances.shape),
            "sampled_rows": len(sample_rows), "path_moves": len(route) - 1,
            "start_id": start, "goal_id": goal,
            "unreachable_initial_checked": unreachable_checked, "legal_trap_checked": trap is not None,
            "seconds": round(time.perf_counter() - started, 3)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, help="Cached crawl directory; uses EVERYNOISE_DATA_DIR by default.")
    parser.add_argument("--metric", action="append", choices=("xyrgb", "kernel", "graph"),
                        help="Audit only the selected mode(s); default is all three.")
    parser.add_argument("--rows", type=int, default=12, help="Deterministically sampled matrix rows, plus boundary IDs.")
    args = parser.parse_args()
    if not 1 <= args.rows <= 64:
        parser.error("--rows must be between 1 and 64")

    from engine.catalog import Catalog
    from engine.metrics import MetricProvider

    catalog = Catalog(data_dir=args.data_dir)
    count = len(catalog.genres)
    assert count == 6291, "This integration audit targets the documented 6,291-genre snapshot."
    assert [genre["id"] for genre in catalog.genres] == list(range(count))
    rows = sorted({0, 5453, count - 1, *random.Random(20261017).sample(range(count), args.rows)})
    provider = MetricProvider(catalog, cache_size=1)
    settings = {
        "xyrgb": {"metric": "xyrgb", "alpha": .8, "cluster_size": 12},
        "kernel": {"metric": "kernel", "opposition": 1., "regularization": .1, "cluster_size": 12},
        "graph": {"metric": "graph"},
    }
    # Each audit drops its service and matrix references before the next mode.
    # The shared provider keeps at most one continuous geometry, plus the graph.
    for metric in args.metric or ("xyrgb", "kernel", "graph"):
        result = audit_mode(catalog, provider, settings[metric], rows)
        print("PASS " + json.dumps(result, separators=(",", ":")), flush=True)
        gc.collect()


if __name__ == "__main__":
    main()
