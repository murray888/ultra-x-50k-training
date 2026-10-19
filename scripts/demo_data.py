"""Create synthetic run data so the site can be previewed without real accounts.

  TODAY=2027-01-20 python scripts/demo_data.py && TODAY=2027-01-20 python scripts/adapt.py \
    && python scripts/commentary.py && python scripts/build_site.py
All numbers are invented. The site shows a "demo data" banner.
"""
import json
import os
import random
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
random.seed(7)
now = dt.date.fromisoformat(os.environ.get("TODAY", "2027-01-20"))
plan = json.loads((ROOT / "config" / "plan.json").read_text())


def run(day, km, hr, pace, name, elev, base):
    secs = int(km * pace * 60)
    route = [[round(base[0] + 0.004 * i / 20 * (1 if i % 2 else -0.6) + 0.002 * (i // 7), 4),
              round(base[1] + 0.006 * i / 20 + 0.0015 * ((i % 5) - 2), 4)] for i in range(40)]
    return {"id": random.randint(10**9, 10**10), "name": name, "date": day.isoformat(),
            "start": day.isoformat() + "T08:00:00Z", "distance_km": round(km, 2), "moving_s": secs,
            "elev_m": elev, "avg_hr": hr, "max_hr": hr + 18, "route": route}


for key, base, pace_adj, hr_adj in (("murray", (50.85, -1.25), 8.0, 0), ("rich", (51.0, -0.74), 6.7, 6)):
    runs = []
    for w in plan["weeks"]:
        if dt.date.fromisoformat(w["sunday"]) >= now:
            break
        a = w["athletes"][key]
        sat = dt.date.fromisoformat(a["long_date"]) if a["long_date"] else None
        miss = (key == "murray" and w["week"] in (12, 13)) or (key == "rich" and w["week"] == 9)
        if sat and a["long_km"] and not miss:
            f = random.uniform(0.92, 1.03)
            runs.append(run(sat, a["long_km"] * f, 142 + hr_adj + random.randint(-3, 5), pace_adj + 0.4,
                            "Saturday long run", int(a["long_km"] * 18), base))
        for i, r in enumerate(a["runs"]):
            if random.random() < 0.15:
                continue
            d = dt.date.fromisoformat(w["monday"]) + dt.timedelta(days=1 + 2 * i)
            hr = 147 + hr_adj + random.randint(-4, 8)
            runs.append(run(d, r["km"] * random.uniform(0.9, 1.05), hr, pace_adj - 0.5 + random.random() * 0.4,
                            f"{r['label']} run", int(r["km"] * 9), base))
    (DATA / f"activities_{key}.json").write_text(json.dumps(runs))
(DATA / "meta.json").write_text(json.dumps(
    {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "demo": True}))
print("Demo data written for", now)
