#!/usr/bin/env python3
"""Build data/PSE/screener.json: a historical momentum ranking.

For each of four lookback windows (daily/weekly/monthly/quarterly), ranks
currently-active, reasonably liquid PSE tickers by closing-price % change
over that window and keeps the top 5 gainers with the numbers behind each
pick (start/end price, avg daily turnover).

This is a plain backward-looking momentum ranking computed from the data
already in this repo. It is NOT a prediction, recommendation, or
financial advice - index.html renders it with that disclaimer attached.

Run after build_ticker_data.py, before committing/pushing.
"""
import os
import json
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TICKERS_DIR = os.path.join(ROOT, "data", "PSE", "tickers")
OUT_PATH = os.path.join(ROOT, "data", "PSE", "screener.json")

PERIODS = {
    "daily": {"label": "Daily", "days": 1, "useLastTradingDay": True, "maxGapDays": 4},
    "weekly": {"label": "Weekly", "days": 7, "maxGapDays": 10},
    "monthly": {"label": "Monthly", "days": 30, "maxGapDays": 40},
    "quarterly": {"label": "Quarterly", "days": 91, "maxGapDays": 110},
}

LIQUIDITY_LOOKBACK = 21       # trading days used to estimate avg turnover
LIQUIDITY_PERCENTILE = 0.5    # require top half of universe by avg turnover
TOP_N = 5


def load_tickers():
    data = {}
    for fname in os.listdir(TICKERS_DIR):
        if not fname.endswith(".json") or fname in ("manifest.json",):
            continue
        with open(os.path.join(TICKERS_DIR, fname)) as f:
            d = json.load(f)
        if d.get("history"):
            data[d["symbol"]] = d["history"]
    return data


def avg_value(history, n):
    recent = history[-n:]
    vals = [r["value"] for r in recent if r.get("value") is not None]
    return sum(vals) / len(vals) if vals else 0


def find_at_or_before(history, target_date):
    for rec in reversed(history):
        if rec["date"] <= target_date:
            return rec
    return None


def main():
    tickers = load_tickers()
    last_date = max(h[-1]["date"] for h in tickers.values())
    last_dt = datetime.strptime(last_date, "%Y-%m-%d")

    # "Currently active" = actually traded on the latest date in the dataset,
    # so every pick reflects today's session rather than a stale, gappy one.
    active_symbols = {s for s, h in tickers.items() if h[-1]["date"] == last_date}

    liquidity = {s: avg_value(tickers[s], LIQUIDITY_LOOKBACK) for s in active_symbols}
    ranked = sorted(liquidity.values())
    cutoff_idx = int(len(ranked) * LIQUIDITY_PERCENTILE)
    liquidity_cutoff = ranked[cutoff_idx] if ranked else 0
    universe = {s for s in active_symbols if liquidity[s] >= liquidity_cutoff and liquidity[s] > 0}

    result = {
        "generated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "asOfDate": last_date,
        "universeSize": len(universe),
        "methodology": (
            f"Ranks the {len(universe)} most liquid PSE tickers that traded on the "
            f"latest session ({last_date}) (top {int((1 - LIQUIDITY_PERCENTILE) * 100)}% "
            f"by {LIQUIDITY_LOOKBACK}-trading-day average peso value traded) by "
            "closing-price % change over each lookback window. A ticker is skipped "
            "for a window if its nearest prior trade is too stale to represent that "
            "window meaningfully. This is a historical momentum ranking only - not "
            "a prediction, recommendation, or financial advice. Past performance "
            "does not indicate future results."
        ),
        "periods": {},
    }

    for key, cfg in PERIODS.items():
        target_date = (last_dt - timedelta(days=cfg["days"])).strftime("%Y-%m-%d")
        picks = []
        for sym in universe:
            history = tickers[sym]
            end = history[-1]
            if cfg.get("useLastTradingDay") and len(history) >= 2:
                start = history[-2]
            else:
                start = find_at_or_before(history, target_date)
            if not start or start is end:
                continue
            if not start.get("close"):
                continue
            gap_days = (datetime.strptime(end["date"], "%Y-%m-%d")
                        - datetime.strptime(start["date"], "%Y-%m-%d")).days
            if gap_days > cfg["maxGapDays"]:
                continue  # comparison point too stale/gappy to be meaningful for this window
            pct = (end["close"] - start["close"]) / start["close"] * 100
            picks.append({
                "symbol": sym,
                "pctChange": round(pct, 2),
                "startDate": start["date"],
                "startPrice": start["close"],
                "endDate": end["date"],
                "endPrice": end["close"],
                "avgDailyValue": round(liquidity[sym]),
            })
        picks.sort(key=lambda p: p["pctChange"], reverse=True)
        top = picks[:TOP_N]
        for p in top:
            direction = "gained" if p["pctChange"] >= 0 else "fell"
            p["reason"] = (
                f"{direction.capitalize()} {abs(p['pctChange']):.2f}% from "
                f"₱{p['startPrice']:.2f} ({p['startDate']}) to "
                f"₱{p['endPrice']:.2f} ({p['endDate']}), average daily turnover "
                f"₱{p['avgDailyValue']:,.0f} — the top {cfg['label'].lower()} "
                "mover among liquid, active PSE names over this window."
            )
        result["periods"][key] = {"label": cfg["label"], "picks": top}

    with open(OUT_PATH, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    total = sum(len(p["picks"]) for p in result["periods"].values())
    print(f"Wrote {total} picks across {len(PERIODS)} periods to {OUT_PATH}")


if __name__ == "__main__":
    main()
