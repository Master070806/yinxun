"""The three agreed genre geometries, computed on the complete catalog.

All distances and nearest-neighbor decisions use float64. Graph distances retain
infinity across components: an isolated genre is not silently removed.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
import math
import re
import threading

import numpy as np
from scipy.linalg import cho_factor
from scipy.linalg.lapack import dpotri
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path
from scipy.spatial.distance import cdist


def _rgb(value):
    if isinstance(value, (tuple, list)) and len(value) == 3:
        return tuple(float(channel) for channel in value)
    value = str(value).strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return tuple(int(value[index:index + 2], 16) for index in (1, 3, 5))
    if re.fullmatch(r"#[0-9a-fA-F]{3}", value):
        return tuple(int(channel * 2, 16) for channel in value[1:])
    match = re.fullmatch(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", value)
    if match:
        return tuple(int(channel) for channel in match.groups())
    raise ValueError(f"Invalid genre color: {value!r}")


def _pair_rms_squared(points):
    """Mean squared distance over uniform distinct pairs, without n² storage."""
    count = len(points)
    if count < 2:
        return 1.0
    centered = points - np.mean(points, axis=0)
    value = float(2 * np.sum(centered * centered) / (count - 1))
    # A constant block contributes zero; the scale has no effect in that case.
    return value if value > 0 else 1.0


def _nearest_clusters(distances, size=20):
    count = len(distances)
    size = min(size, count)
    clusters = []
    for center, row in enumerate(distances):
        if size == 1:
            clusters.append((center,))
            continue
        # Include the center explicitly, even if distinct genres share a vector.
        candidates = row.copy()
        candidates[center] = np.inf
        cutoff = np.partition(candidates, size - 2)[size - 2]
        closer = np.flatnonzero(candidates < cutoff)
        tied = np.flatnonzero(candidates == cutoff)
        neighbors = np.concatenate((closer, tied[:size - 1 - len(closer)]))
        members = np.concatenate((np.array([center]), neighbors))
        order = np.lexsort((members, row[members]))
        clusters.append(tuple(int(member) for member in members[order]))
    return tuple(clusters)


@dataclass
class MetricSpace:
    kind: str
    distances: np.ndarray
    clusters: tuple[tuple[int, ...], ...]
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.distances.setflags(write=False)
        reverse = [[] for _ in self.clusters]
        for center, members in enumerate(self.clusters):
            for member in members:
                reverse[member].append(center)
        self._reverse = tuple(tuple(centers) for centers in reverse)

    def reverse_clusters(self, target):
        return self._reverse[target]

    def distance(self, left, right):
        return float(self.distances[left, right])

    def separation(self, left, right):
        if self.kind != "graph":
            return self.distance(left, right)
        if left == right:
            return 0.0
        if not math.isfinite(self.distance(left, right)):
            return math.inf
        between = self.distances[np.ix_(self.clusters[left], self.clusters[right])]
        return float(max(np.min(between, axis=0).max(), np.min(between, axis=1).max()))

    def compatible(self, left, right, threshold):
        if self.kind != "graph":
            return self.distance(left, right) >= threshold
        distance = self.distance(left, right)
        # For closed unit balls, max(q-1, 0) <= H <= q.
        if distance < threshold:
            return False
        if distance - 1 >= threshold or threshold <= 0:
            return True
        return self.separation(left, right) >= threshold

    def compatibility_mask(self, anchor, threshold):
        distances = self.distances[anchor]
        if self.kind != "graph":
            return distances >= threshold
        mask = distances >= threshold
        ambiguous = np.flatnonzero(mask & (distances - 1 < threshold))
        for other in ambiguous:
            mask[other] = self.separation(anchor, int(other)) >= threshold
        return mask


class MetricProvider:
    """Bounded geometry cache with small nearest-k views sharing each matrix."""

    def __init__(self, catalog, cache_size=2):
        self.catalog = catalog
        self.cache_size = max(1, cache_size)
        self._cache = OrderedDict()
        self._lock = threading.RLock()
        self._near_matrix = None
        self._opposite_matrix = None
        self._graph_space = None
        self._positions = np.array([[genre["x"], genre["y"]] for genre in catalog.genres], dtype=np.float64)
        self._colors = np.array([_rgb(genre["color"]) for genre in catalog.genres], dtype=np.float64)
        if not len(self._positions) or not np.isfinite(self._positions).all() or not np.isfinite(self._colors).all():
            raise ValueError("The genre catalog must have finite coordinates and colors.")
        self._position_scale_squared = _pair_rms_squared(self._positions)
        self._color_scale_squared = _pair_rms_squared(self._colors)

    def get(self, settings):
        kind = settings.get("metric", "xyrgb")
        if kind == "xyrgb":
            alpha = float(settings.get("alpha", 0.8))
            if not math.isfinite(alpha) or not 0 < alpha < 1:
                raise ValueError("Position weight must be strictly between 0 and 1.")
            key = (kind, alpha)
        elif kind == "kernel":
            opposition = float(settings.get("opposition", 1.0))
            regularization = float(settings.get("regularization", 1.0))
            if not all(math.isfinite(value) and value > 0 for value in (opposition, regularization)):
                raise ValueError("Kernel opposition and regularization must be positive.")
            key = (kind, opposition, regularization)
        elif kind == "graph":
            key = (kind,)
        else:
            raise ValueError("Unknown genre metric.")
        if kind != "graph":
            cluster_size = settings.get("cluster_size", 20)
            if (isinstance(cluster_size, bool) or not isinstance(cluster_size, int)
                    or not 5 <= cluster_size <= 25):
                raise ValueError("Genres per cluster must be an integer between 5 and 25.")

        with self._lock:
            if kind == "graph":
                if self._graph_space is None:
                    self._graph_space = self._graph()
                return self._graph_space
            if key in self._cache:
                self._cache.move_to_end(key)
                views = self._cache[key]
                if cluster_size not in views:
                    base = next(iter(views.values()))
                    views[cluster_size] = MetricSpace(
                        kind, base.distances, _nearest_clusters(base.distances, cluster_size),
                        {**base.metadata, "cluster_size": cluster_size},
                    )
                    # Size changes share the expensive geometry and only retain
                    # three neighborhood/reverse-membership views per geometry.
                    if len(views) > 3:
                        views.popitem(last=False)
                views.move_to_end(cluster_size)
                return views[cluster_size]
            # Evict before building to keep peak dense storage bounded.
            while len(self._cache) >= self.cache_size:
                self._cache.popitem(last=False)
            if kind == "xyrgb":
                space = self._xyrgb(alpha, cluster_size)
            else:
                space = self._kernel(opposition, regularization, cluster_size)
            self._cache[key] = OrderedDict([(cluster_size, space)])
            return space

    def _adjacency(self, layer):
        attribute = f"_{layer}_matrix"
        cached = getattr(self, attribute)
        if cached is not None:
            return cached
        adjacency = getattr(self.catalog, layer)
        rows, columns = [], []
        for center, neighbors in enumerate(adjacency):
            for neighbor in neighbors:
                if neighbor != center:
                    rows.append(center)
                    columns.append(neighbor)
        count = len(self.catalog.genres)
        matrix = csr_matrix((np.ones(len(rows)), (rows, columns)), shape=(count, count))
        # OR-symmetrize each layer independently; overlapping signs stay present.
        matrix = matrix.maximum(matrix.T)
        matrix.data.fill(1.0)
        setattr(self, attribute, matrix)
        return matrix

    def _xyrgb(self, alpha, cluster_size=20):
        count = len(self._positions)
        squared = np.empty((count, count), dtype=np.float64)
        for start in range(0, count, 128):
            end = min(start + 128, count)
            block = cdist(self._positions[start:end], self._positions, "sqeuclidean")
            block *= alpha / self._position_scale_squared
            colors = cdist(self._colors[start:end], self._colors, "sqeuclidean")
            colors *= (1 - alpha) / self._color_scale_squared
            block += colors
            squared[start:end] = block
        np.sqrt(squared, out=squared)
        np.fill_diagonal(squared, 0.0)
        return MetricSpace("xyrgb", squared, _nearest_clusters(squared, cluster_size), {
            "alpha": alpha,
            "cluster_size": cluster_size,
            "position_scale": math.sqrt(self._position_scale_squared),
            "color_scale": math.sqrt(self._color_scale_squared),
        })

    def _graph(self):
        adjacency = self._adjacency("near")
        distances = shortest_path(adjacency, method="D", directed=False, unweighted=True)
        clusters = tuple(tuple(sorted({center, *(int(neighbor) for neighbor in adjacency.indices[adjacency.indptr[center]:adjacency.indptr[center + 1]])}))
                         for center in range(len(self.catalog.genres)))
        return MetricSpace("graph", distances, clusters)

    def _kernel(self, opposition, regularization, cluster_size=20):
        near = self._adjacency("near")
        opposite = self._adjacency("opposite")
        # Ls = Dn - An + lambda(Do + Ao). Do not combine overlapping edges
        # before computing degrees: that would change the agreed signed energy.
        matrix = (-near + opposition * opposite).toarray(order="F")
        diagonal = np.arange(len(matrix))
        matrix[diagonal, diagonal] += (
            np.asarray(near.sum(axis=1)).ravel()
            + opposition * np.asarray(opposite.sum(axis=1)).ravel()
            + regularization
        )
        factor, lower = cho_factor(matrix, lower=True, overwrite_a=True, check_finite=False)
        kernel, info = dpotri(factor, lower=int(lower), overwrite_c=True)
        if info != 0:
            raise ArithmeticError(f"Signed-kernel inversion failed (LAPACK info={info}).")
        if not np.isfinite(kernel).all() or np.any(np.diag(kernel) <= 0):
            raise ArithmeticError("These kernel parameters exceed numerical precision; increase regularization.")
        norm = np.sqrt(np.diag(kernel).copy())
        # potri fills one triangle. Mirror rowwise without a second dense matrix.
        for row in range(len(kernel)):
            kernel[row, row + 1:] = kernel[row + 1:, row]
        kernel /= norm[:, None]
        kernel /= norm[None, :]
        np.clip(kernel, -1.0, 1.0, out=kernel)
        kernel *= -2
        kernel += 2
        np.maximum(kernel, 0, out=kernel)
        np.sqrt(kernel, out=kernel)
        np.fill_diagonal(kernel, 0.0)
        # Enforce exact stored symmetry despite the two division roundings.
        for row in range(len(kernel)):
            kernel[row, row + 1:] = kernel[row + 1:, row]
        return MetricSpace("kernel", kernel, _nearest_clusters(kernel, cluster_size), {
            "opposition": opposition, "regularization": regularization,
            "cluster_size": cluster_size,
        })
