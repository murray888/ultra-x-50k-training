"""Merge an iPhone Shortcut upload into runs/<athlete>.json.

The Shortcut sends a GitHub repository_dispatch (event "runs-upload") whose payload is
  {"athlete": "murray", "runs": [{"start": "2026-10-25T08:30:00", "distance_km": 12.3,
                                  "moving_s": 4300, "avg_hr": 141, "max_hr": 160, "elev_m": 0}, ...]}
The workflow passes it in the PAYLOAD environment variable. Runs are merged by start time,
so sending the last 14 days every week is safe. Also usable for a one-off backfill:
  PAYLOAD="$(cat backfill.json)" python scripts/ingest.py
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATHLETES = {"murray", "rich"}


def num(v, lo, hi):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if lo <= v <= hi else None


def clean(r):
    start = str(r.get("start", ""))[:19]
    if len(start) < 10 or not start[:4].isdigit():
        return None
    km, secs = num(r.get("distance_km"), 0.5, 200), num(r.get("moving_s"), 60, 86400)
    if km is None or secs is None:
        return None
    hr, mx = num(r.get("avg_hr"), 40, 230), num(r.get("max_hr"), 40, 230)
    return {"id": start, "name": "Run", "date": start[:10], "start": start,
            "distance_km": round(km, 2), "moving_s": int(secs),
            "elev_m": round(num(r.get("elev_m"), 0, 5000) or 0),
            "avg_hr": round(hr, 1) if hr else None, "max_hr": round(mx, 1) if mx else None}


def main():
    payload = json.loads(os.environ.get("PAYLOAD") or "{}")
    ath = payload.get("athlete")
    if ath not in ATHLETES:
        sys.exit(f"unknown athlete {ath!r}")
    path = ROOT / "runs" / f"{ath}.json"
    have = {r["start"]: r for r in json.loads(path.read_text())} if path.exists() else {}
    new = [c for c in map(clean, payload.get("runs") or []) if c]
    for c in new:
        have[c["start"]] = c
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(sorted(have.values(), key=lambda r: r["start"]), indent=1))
    print(f"{ath}: received {len(new)} runs, {len(have)} stored")


if __name__ == "__main__":
    main()
