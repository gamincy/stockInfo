#!/usr/bin/env python3
"""Rebuild per-ticker trend data from data/PSE/csv/*.txt.

Reads every daily PSE data file and re-groups the rows by stock symbol,
writing one JSON file per ticker to data/PSE/tickers/<SYMBOL>.json plus a
data/PSE/tickers/manifest.json listing all known symbols. This lets the
web page fetch a single small file per ticker instead of scanning all
1800+ daily files to plot a trend.

Run this after adding new daily data files (in addition to
generate_manifest.py), before committing/pushing.
"""
import os
import re
import json
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(ROOT, "data", "PSE", "csv")
OUT_DIR = os.path.join(ROOT, "data", "PSE", "tickers")

FIELD_NAMES = [
    "prevClose", "close", "change", "pctChange",
    "open", "high", "low", "value", "trades", "volume",
]

FILENAME_RE = re.compile(r"^Data_(\d{4}-\d{2}-\d{2})\.txt$")


def parse_num(s):
    s = s.strip()
    if not s or "NO TRADE" in s or s.upper() == "NOTRADE":
        return None
    s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def main():
    tickers = defaultdict(list)
    files = sorted(f for f in os.listdir(CSV_DIR) if FILENAME_RE.match(f))

    for fname in files:
        date = FILENAME_RE.match(fname).group(1)
        path = os.path.join(CSV_DIR, fname)
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                fields = line.split(":")
                if len(fields) < 11:
                    continue  # bare symbol / no data that day
                symbol = fields[0].strip()
                if not symbol:
                    continue
                values = [parse_num(v) for v in fields[1:11]]
                close = values[1]
                if close is None:
                    continue  # no trade that day, skip the data point
                record = {"date": date}
                record.update(dict(zip(FIELD_NAMES, values)))
                tickers[symbol].append(record)

    os.makedirs(OUT_DIR, exist_ok=True)
    # Clear stale per-ticker files from a previous run (e.g. delisted symbols)
    for f in os.listdir(OUT_DIR):
        if f.endswith(".json") and f != "manifest.json":
            os.remove(os.path.join(OUT_DIR, f))

    for symbol, history in tickers.items():
        out_path = os.path.join(OUT_DIR, f"{symbol}.json")
        with open(out_path, "w") as f:
            json.dump({"symbol": symbol, "history": history}, f, separators=(",", ":"))

    manifest = {
        "symbols": sorted(tickers.keys()),
        "count": len(tickers),
        "generated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    with open(os.path.join(OUT_DIR, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Wrote {len(tickers)} ticker files to {OUT_DIR}")


if __name__ == "__main__":
    main()
