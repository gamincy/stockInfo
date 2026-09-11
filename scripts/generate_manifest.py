#!/usr/bin/env python3
"""Regenerate data/PSE/manifest.json from the files in data/PSE/csv/.

Run this after adding new daily data files, before committing/pushing,
so the web page knows which dates are available without hitting the
GitHub API (which is rate-limited for unauthenticated requests).
"""
import os
import json
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(ROOT, "data", "PSE", "csv")
MANIFEST_PATH = os.path.join(ROOT, "data", "PSE", "manifest.json")


def main():
    files = sorted(os.listdir(CSV_DIR))
    dates = [f[5:-4] for f in files if f.startswith("Data_") and f.endswith(".txt")]
    manifest = {
        "dates": dates,
        "count": len(dates),
        "generated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote {len(dates)} dates to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
