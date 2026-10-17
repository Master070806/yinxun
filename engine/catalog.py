"""Read one consistent EveryNoise snapshot without exposing its answers to clients.

The genre universe and XYRGB values come from the cached main map. Near and
opposite links are independently OR-symmetrized, preserving overlaps between
the two edge systems. The original HTML stays in EVERYNOISE_DATA_DIR.

Audio positions refer to item1 and item2 on each genre's *map*: the first two
ordered sample entries. They are not the separate research.html artist list
or the Spotify playlist. Source URLs and this distinction are retained below.
Missing previews remain missing; neither entries nor genres are substituted.
"""

from __future__ import annotations

import gzip
import hashlib
from collections import OrderedDict
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import tempfile
from threading import Lock
from urllib.parse import urlencode, urlsplit
import zlib


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://everynoise.com/"
CACHE_VERSION = 1
_ENTRY = re.compile(r'<div\s+id=[\"\']?(?:item\d+|mirroritem\d+)[\"\']?\s[^>]*>.*?</div>', re.S)
_PAGE_ENTRY = re.compile(r'<div\s+id=[\"\']?(?:item[12]|mirroritem\d+)[\"\']?\s[^>]*>.*?</div>', re.S)
_SAMPLE_ENTRY = re.compile(r'<div\s+id=[\"\']?item\d+[\"\']?\s[^>]*>.*?</div>', re.S)
_ITEM_ID = re.compile(r"item\d+\Z")
_TRACK_ID = re.compile(r"playx\(\s*['\"]([A-Za-z0-9]{22})['\"]")


class CatalogError(RuntimeError):
    """The source snapshot is incomplete or internally inconsistent."""


class _EntryParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.attrs = {}
        self.links = []
        self.name = ""
        self._in_anchor = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "div":
            self.attrs = attrs
        elif tag == "a":
            self._in_anchor = True
            if "href" in attrs:
                self.links.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag == "a":
            self._in_anchor = False

    def handle_data(self, data):
        if not self._in_anchor:
            self.name += data


def _entry(html):
    entry = _EntryParser()
    entry.feed(html)
    entry.name = entry.name.strip()
    return entry


def _genre_path(entry):
    links = [urlsplit(link).path.lstrip("/") for link in entry.links]
    links = [path for path in links if path.startswith("engenremap-") and path.endswith(".html")]
    if len(links) != 1:
        raise CatalogError(f"Expected one genre link in {entry.attrs.get('id')}")
    return links[0]


def safe_preview_url(url):
    """Only accept the audio CDN used by the audited source, never arbitrary URLs."""
    if not url:
        return None
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname != "p.scdn.co"
            or parsed.port not in (None, 443) or parsed.username or parsed.password
            or not parsed.path.startswith("/mp3-preview/")):
        raise CatalogError("Unsupported sample URL in the EveryNoise snapshot")
    return url


def _symmetric(adjacency):
    result = [set(row) for row in adjacency]
    for u, row in enumerate(adjacency):
        result[u].discard(u)
        for v in row:
            if v != u:
                result[v].add(u)
    return [sorted(row) for row in result]


def _sample_record(attrs, path, position):
    track = _TRACK_ID.search(attrs.get("onclick", ""))
    return {
        "position": position,
        "preview_url": safe_preview_url(attrs.get("preview_url")),
        "track_id": track.group(1) if track else None,
        "source_url": BASE_URL + path,
        "source_element": f"item{position}",
        "source_kind": "genre-map-sample",
    }


class Catalog:
    """All genres in source order; IDs index genres, near, and opposite.

    ``tracks(i)`` returns two private dictionaries with ``preview_url``
    (possibly None), ``track_id``, ``source_url``, and one-based ``position``.
    ``samples(i)`` lazily reads every numbered sample on that same genre map,
    preserving missing samples and numeric source order. It returns independent
    copies from a bounded in-memory cache. Do not serialize these dictionaries
    into an active round response.
    """

    def __init__(self, data_dir=None, cache_dir=None, *, samples_cache_size=32):
        if (isinstance(samples_cache_size, bool) or not isinstance(samples_cache_size, int)
                or samples_cache_size < 1):
            raise ValueError("The sample cache must hold at least one genre")
        self.data_dir = Path(data_dir or os.environ.get("EVERYNOISE_DATA_DIR")
                             or ROOT.parent / "data" / "everynoise").resolve()
        self.cache_dir = Path(cache_dir or ROOT / ".cache" / "genreguessr")
        required = ("index.html", "genres.json", "neighborhoods.json")
        missing = [name for name in required if not (self.data_dir / name).is_file()]
        if missing:
            raise CatalogError("EveryNoise data missing: " + ", ".join(missing)
                               + ". Set EVERYNOISE_DATA_DIR to the cached crawl directory.")
        source_bytes = {name: (self.data_dir / name).read_bytes() for name in required}
        source_genres = json.loads(source_bytes["genres.json"])
        self.fingerprint = self._fingerprint(source_bytes, source_genres)
        cache_path = self.cache_dir / "catalog.json"
        payload = None
        if cache_path.is_file():
            try:
                candidate = json.loads(cache_path.read_text())
                if (candidate.get("version") == CACHE_VERSION
                        and candidate.get("fingerprint") == self.fingerprint):
                    payload = candidate
            except (OSError, ValueError):
                pass
        if payload is None:
            payload = self._build(source_bytes, source_genres)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                             dir=self.cache_dir, delete=False) as handle:
                json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
                temporary = Path(handle.name)
            temporary.replace(cache_path)
        self.genres = payload["genres"]
        self.paths = payload["paths"]
        self.by_name = {genre["name"]: genre["id"] for genre in self.genres}
        self.near = [frozenset(row) for row in payload["near"]]
        self.opposite = [frozenset(row) for row in payload["opposite"]]
        self._tracks = payload["tracks"]
        self.provenance = payload["provenance"]
        self._page_hashes = {row["path"]: row["sha256"]
                             for row in json.loads(source_bytes["neighborhoods.json"])}
        self._samples_cache_size = samples_cache_size
        self._samples_cache = OrderedDict()
        self._samples_lock = Lock()

    def _fingerprint(self, source_bytes, source_genres):
        digest = hashlib.sha256()
        digest.update(f"catalog-v{CACHE_VERSION}".encode())
        for name, content in source_bytes.items():
            digest.update(name.encode())
            digest.update(content)
        for genre in source_genres:
            path = self.data_dir / "pages" / (genre["path"] + ".gz")
            try:
                stat = path.stat()
            except FileNotFoundError as error:
                raise CatalogError(f"Missing cached genre page: {genre['path']}") from error
            digest.update(f"{genre['path']}:{stat.st_size}:{stat.st_mtime_ns}".encode())
        return digest.hexdigest()

    def _build(self, source_bytes, source_genres):
        index_entries = [_entry(match.group()) for match in
                         _ENTRY.finditer(source_bytes["index.html"].decode("utf-8"))]
        index_entries = [entry for entry in index_entries
                         if _ITEM_ID.fullmatch(entry.attrs.get("id", ""))]
        mapped = {_genre_path(entry): entry for entry in index_entries}
        expected_paths = [genre["path"] for genre in source_genres]
        if len(mapped) != len(index_entries) or set(mapped) != set(expected_paths):
            raise CatalogError("Main map and genre index have different genre universes")
        if len(set(expected_paths)) != len(expected_paths):
            raise CatalogError("Duplicate genre paths")
        ids = {path: i for i, path in enumerate(expected_paths)}
        rows = json.loads(source_bytes["neighborhoods.json"])
        neighborhoods = {row["path"]: row for row in rows}
        if len(neighborhoods) != len(rows) or set(neighborhoods) != set(ids):
            raise CatalogError("Neighborhood records and main map have different genre universes")
        genres, near, opposite, tracks = [], [], [], []
        for i, genre in enumerate(source_genres):
            entry = mapped[genre["path"]]
            if entry.name != genre["name"]:
                raise CatalogError(f"Genre name mismatch: {genre['path']}")
            style = dict((key.strip(), value.strip()) for key, value in
                         (rule.split(":", 1) for rule in entry.attrs["style"].split(";") if ":" in rule))
            color = style.get("color", "").lower()
            if not re.fullmatch(r"#[0-9a-f]{6}", color):
                raise CatalogError(f"Invalid genre color: {genre['path']}")
            genres.append({"id": i, "name": genre["name"], "color": color,
                           "x": float(style["left"].removesuffix("px")),
                           "y": float(style["top"].removesuffix("px")),
                           "rgb": [int(color[k:k + 2], 16) for k in (1, 3, 5)]})
            row = neighborhoods[genre["path"]]
            if "error" in row:
                raise CatalogError(f"Failed source crawl: {genre['path']}")
            near.append([ids[neighbor["path"]] for neighbor in row["neighbors"]
                         if neighbor["path"] != genre["path"]])
            raw = gzip.decompress((self.data_dir / "pages" / (genre["path"] + ".gz")).read_bytes())
            if row.get("sha256") != hashlib.sha256(raw).hexdigest():
                raise CatalogError(f"Cached HTML does not match crawl provenance: {genre['path']}")
            page_entries = [_entry(match.group()) for match in _PAGE_ENTRY.finditer(raw.decode("utf-8"))]
            mirrors = [entry for entry in page_entries if entry.attrs["id"].startswith("mirroritem")]
            opposite.append([ids[_genre_path(entry)] for entry in mirrors])
            samples = {entry.attrs["id"]: entry for entry in page_entries
                       if entry.attrs["id"] in {"item1", "item2"}}
            page_tracks = []
            for position in (1, 2):
                sample = samples.get(f"item{position}")
                attrs = sample.attrs if sample else {}
                page_tracks.append(_sample_record(attrs, genre["path"], position))
            tracks.append(page_tracks)
        if len({genre["name"] for genre in genres}) != len(genres):
            raise CatalogError("Duplicate genre names")
        provenance = {
            "main_map_url": BASE_URL + "engenremap.html",
            "main_map_sha256": hashlib.sha256(source_bytes["index.html"]).hexdigest(),
            "neighborhoods_sha256": hashlib.sha256(source_bytes["neighborhoods.json"]).hexdigest(),
            "genre_count": len(genres),
            "first_crawl_check_utc": min(row["checked_at_utc"] for row in rows),
            "last_crawl_check_utc": max(row["checked_at_utc"] for row in rows),
            "near_directed_arcs": sum(map(len, near)),
            "opposite_directed_arcs": sum(map(len, opposite)),
            "audio_order": "genre map item1, item2; not research artist-list or Spotify playlist order",
            "missing_preview_by_position": [sum(not row[p]["preview_url"] for row in tracks) for p in (0, 1)],
        }
        return {"version": CACHE_VERSION, "fingerprint": self.fingerprint,
                "genres": genres, "paths": expected_paths, "near": _symmetric(near),
                "opposite": _symmetric(opposite), "tracks": tracks, "provenance": provenance}

    def tracks(self, index):
        """First and second original samples, including explicit missing previews."""
        if not isinstance(index, int) or not 0 <= index < len(self.genres):
            raise IndexError("Unknown genre")
        return [dict(track) for track in self._tracks[index]]

    def _read_samples(self, index):
        path = self.paths[index]
        try:
            raw = gzip.decompress((self.data_dir / "pages" / (path + ".gz")).read_bytes())
        except (OSError, EOFError, zlib.error) as error:
            raise CatalogError(f"Could not read cached genre page: {path}") from error
        if hashlib.sha256(raw).hexdigest() != self._page_hashes.get(path):
            raise CatalogError(f"Cached HTML does not match crawl provenance: {path}")
        try:
            html = raw.decode("utf-8")
        except UnicodeError as error:
            raise CatalogError(f"Invalid genre page encoding: {path}") from error
        samples = {}
        for match in _SAMPLE_ENTRY.finditer(html):
            attrs = _entry(match.group()).attrs
            position = int(attrs["id"][4:])
            if position < 1 or position in samples:
                raise CatalogError(f"Invalid or duplicate sample position: {path}")
            samples[position] = _sample_record(attrs, path, position)
        return tuple(samples[position] for position in sorted(samples))

    def samples(self, index):
        """All original numbered samples, including missing URLs, loaded lazily."""
        if (isinstance(index, bool) or not isinstance(index, int)
                or not 0 <= index < len(self.genres)):
            raise IndexError("Unknown genre")
        with self._samples_lock:
            if index not in self._samples_cache:
                samples = self._read_samples(index)
                self._samples_cache[index] = samples
                while len(self._samples_cache) > self._samples_cache_size:
                    self._samples_cache.popitem(last=False)
            self._samples_cache.move_to_end(index)
            return [dict(sample) for sample in self._samples_cache[index]]

    def music_list_url(self, index):
        """The separate artist-list source, retained for provenance only."""
        return BASE_URL + "research.html?" + urlencode({"mode": "genre", "name": self.genres[index]["name"]})
