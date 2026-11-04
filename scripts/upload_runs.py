"""Send your recent runs from an Apple Health export to the training site (run on YOUR computer).

  1. iPhone: Health app > profile picture > Export All Health Data. Unzip it.
  2. export GITHUB_TOKEN=github_pat_...      (the token stays on your computer; never paste it in chat)
     python3 scripts/upload_runs.py path/to/apple_health_export/export.xml --athlete murray
     Add --dry-run to print what would be sent. --days N sets how far back to look (default 21).

Only dates, distances, durations, elevation and average/maximum heart rate of runs are sent. No routes.
Sending the same run twice is harmless: the site merges runs by start time.
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

REPO = "murray888/ultra-x-50k-training"
RUN = "HKWorkoutActivityTypeRunning"


def km(value, unit):
    v = float(value)
    return v * 1.609344 if unit == "mi" else v / 1000 if unit == "m" else v


def runs_from(path, since):
    out = []
    for _, el in ET.iterparse(path, events=("end",)):
        if el.tag == "Workout" and el.get("workoutActivityType") == RUN:
            start = (el.get("startDate") or "")[:19].replace(" ", "T")
            if start[:10] >= since:
                dist = el.get("totalDistance") and km(el.get("totalDistance"), el.get("totalDistanceUnit", "km"))
                avg = mx = None
                for s in el.findall("WorkoutStatistics"):
                    t = s.get("type")
                    if t == "HKQuantityTypeIdentifierDistanceWalkingRunning" and s.get("sum"):
                        dist = km(s.get("sum"), s.get("unit", "km"))
                    elif t == "HKQuantityTypeIdentifierHeartRate":
                        avg, mx = s.get("average"), s.get("maximum")
                elev = 0
                for m in el.findall("MetadataEntry"):
                    if m.get("key") == "HKElevationAscended":
                        v, _, u = (m.get("value") or "0 cm").partition(" ")
                        elev = float(v) / 100 if u == "cm" else float(v)
                dur = float(el.get("duration", 0)) * (60 if el.get("durationUnit") == "min" else 1)
                if dist and dist > 0.5 and dur > 60:
                    out.append({"start": start, "distance_km": round(dist, 2), "moving_s": round(dur),
                                "avg_hr": float(avg) if avg else None, "max_hr": float(mx) if mx else None,
                                "elev_m": round(elev)})
        if el.tag in ("Workout", "Record"):
            el.clear()
    return sorted(out, key=lambda r: r["start"])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("export"), ap.add_argument("--athlete", default="murray", choices=["murray", "rich"])
    ap.add_argument("--days", type=int, default=21), ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    since = (dt.date.today() - dt.timedelta(days=a.days)).isoformat()
    runs = runs_from(a.export, since)
    for r in runs:
        print(f"{r['start'][:16]}  {r['distance_km']:>6} km  {r['moving_s'] // 60:>4} min  HR {r['avg_hr'] or '-'}")
    print(f"{len(runs)} runs since {since}")
    if a.dry_run or not runs:
        return
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GITHUB_TOKEN first (export GITHUB_TOKEN=...)")
    body = json.dumps({"event_type": "runs-upload", "client_payload": {"athlete": a.athlete, "runs": runs}}).encode()
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/dispatches", data=body, method="POST", headers={
        "Authorization": "Bearer " + token, "Accept": "application/vnd.github+json", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("Sent. GitHub replied", r.status, "(204 = success). The site updates within a couple of minutes.")
    except urllib.error.HTTPError as e:
        sys.exit(f"GitHub replied {e.code}: {e.read().decode()[:200]}")


if __name__ == "__main__":
    main()
