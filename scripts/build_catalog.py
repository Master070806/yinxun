#!/usr/bin/env python3
"""Validate the cached EveryNoise crawl and build the private engine catalog."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.catalog import Catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path)
    args = parser.parse_args()
    catalog = Catalog(data_dir=args.data_dir)
    summary = dict(catalog.provenance)
    summary.update({"near_undirected_edges": sum(map(len, catalog.near)) // 2,
                    "opposite_undirected_edges": sum(map(len, catalog.opposite)) // 2,
                    "cache_directory": str(catalog.cache_dir)})
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
