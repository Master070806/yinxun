"""Lazy sample access against small, provenance-checked HTML snapshots."""

import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from engine.catalog import Catalog, CatalogError


def sample(position, preview=None, track_id=None, prefix="item", link=""):
    preview = preview if preview is not None else f"https://p.scdn.co/mp3-preview/sample{position}"
    track_id = track_id if track_id is not None else "A" * 22
    return (f'<div id="{prefix}{position}" preview_url="{preview}" '
            f'onclick="playx(&quot;{track_id}&quot;, &quot;Artist&quot;, this);">'
            f'Artist {position}{link}</div>')


class CatalogSampleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="catalog-samples-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.data = self.root / "source"
        (self.data / "pages").mkdir(parents=True)
        self.paths = [f"engenremap-genre{i}.html" for i in range(3)]
        self.pages = []
        for index, path in enumerate(self.paths):
            self.pages.append("".join([
                sample(10), sample(2, preview="", track_id=""), sample(1), sample(3),
                sample(1, prefix="nearbyitem"),
                sample(1, prefix="mirroritem", link=f'<a href="{self.paths[(index + 1) % 3]}">»</a>'),
                '<a href="https://open.spotify.com/playlist/example">playlist</a>',
            ]))
        self._write_source()

    def _write_source(self):
        rows, index_entries = [], []
        genres = [{"path": path, "name": f"genre {i}"} for i, path in enumerate(self.paths)]
        for i, genre in enumerate(genres):
            raw = self.pages[i].encode()
            (self.data / "pages" / (genre["path"] + ".gz")).write_bytes(gzip.compress(raw))
            rows.append({**genre, "sha256": hashlib.sha256(raw).hexdigest(),
                         "checked_at_utc": "2026-10-14T17:00:00+00:00", "neighbors": []})
            index_entries.append(f'<div id=item{i + 1} style="color:#123456;left:{i}px;top:{i}px">'
                                 f'{genre["name"]}<a href="{genre["path"]}">»</a></div>')
        (self.data / "index.html").write_text("".join(index_entries), encoding="utf-8")
        (self.data / "genres.json").write_text(json.dumps(genres))
        (self.data / "neighborhoods.json").write_text(json.dumps(rows))

    def catalog(self, **kwargs):
        return Catalog(self.data, self.root / "cache", **kwargs)

    def test_numeric_order_excludes_neighbor_mirror_and_header_links(self):
        catalog = self.catalog()
        samples = catalog.samples(0)
        self.assertEqual([row["position"] for row in samples], [1, 2, 3, 10])
        self.assertEqual([row["source_element"] for row in samples], ["item1", "item2", "item3", "item10"])
        self.assertEqual(samples[:2], catalog.tracks(0))
        self.assertIsNone(samples[1]["preview_url"])
        self.assertIsNone(samples[1]["track_id"])
        self.assertTrue(all(row["source_url"] == "https://everynoise.com/" + self.paths[0]
                            for row in samples))

    def test_results_are_independent_copies(self):
        catalog = self.catalog()
        original = catalog.samples(0)
        changed = catalog.samples(0)
        changed[0]["preview_url"] = "https://wrong.invalid/"
        changed.pop()
        self.assertEqual(catalog.samples(0), original)
        self.assertEqual(catalog.tracks(0), original[:2])

    def test_full_sample_cache_is_lazy_and_bounded_with_lru_eviction(self):
        with patch.object(Catalog, "_read_samples", autospec=True,
                          side_effect=Catalog._read_samples) as read:
            catalog = self.catalog(samples_cache_size=2)
            read.assert_not_called()
            catalog.samples(0)
            catalog.samples(1)
            catalog.samples(0)
            catalog.samples(2)
            catalog.samples(0)
            self.assertEqual(read.call_count, 3)
            catalog.samples(1)
            self.assertEqual([call.args[1] for call in read.call_args_list], [0, 1, 2, 1])
        payload = json.loads((self.root / "cache" / "catalog.json").read_text())
        self.assertNotIn("samples", payload)
        self.assertTrue(all(len(tracks) == 2 for tracks in payload["tracks"]))

    def test_warm_catalog_checks_page_provenance_on_lazy_read(self):
        self.catalog()
        catalog = self.catalog()
        path = self.data / "pages" / (self.paths[0] + ".gz")
        path.write_bytes(gzip.compress(b"modified source"))
        with self.assertRaisesRegex(CatalogError, "provenance"):
            catalog.samples(0)
        path.write_bytes(gzip.compress(self.pages[0].encode()))
        self.assertEqual(len(catalog.samples(0)), 4)

    def test_later_samples_use_the_same_preview_host_validation(self):
        self.pages[0] = self.pages[0].replace("https://p.scdn.co/mp3-preview/sample10", "https://wrong.invalid/sample10")
        self._write_source()
        catalog = self.catalog()
        with self.assertRaisesRegex(CatalogError, "Unsupported sample URL"):
            catalog.samples(0)

    def test_duplicate_sample_positions_are_rejected(self):
        self.pages[0] += sample(10)
        self._write_source()
        catalog = self.catalog()
        with self.assertRaisesRegex(CatalogError, "duplicate sample position"):
            catalog.samples(0)

    def test_unknown_genre_ids_are_rejected_without_loading_pages(self):
        catalog = self.catalog()
        with patch.object(catalog, "_read_samples") as read:
            for value in (-1, 3, 0.0, "0", True, None):
                with self.assertRaises(IndexError):
                    catalog.samples(value)
            read.assert_not_called()


if __name__ == "__main__":
    unittest.main()
