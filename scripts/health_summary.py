"""Make a small, shareable summary from an Apple Health export (run this on YOUR computer).

  1. iPhone: Health app > profile picture > Export All Health Data. Unzip it.
  2. python scripts/health_summary.py path/to/apple_health_export/export.xml rich_health_summary.csv
  3. Send the small CSV (a few KB) instead of the huge export. It holds only daily resting heart rate,
     daily average HRV (SDNN) and your runs (date, distance, duration, average and maximum HR).

Nothing leaves your computer until you send the file. Do not commit it to a public repository.
"""
import csv
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date

if len(sys.argv) != 3:
    sys.exit(__doc__)
src, out = sys.argv[1], sys.argv[2]
since = date(2025, 10, 1).isoformat()
rhr, hrv, rows = defaultdict(list), defaultdict(list), []
for _, el in ET.iterparse(src, events=("end",)):
    if el.tag == "Record":
        t, d = el.get("type"), (el.get("startDate") or "")[:10]
        if d >= since and t == "HKQuantityTypeIdentifierRestingHeartRate":
            rhr[d].append(float(el.get("value")))
        elif d >= since and t == "HKQuantityTypeIdentifierHeartRateVariabilitySDNN":
            hrv[d].append(float(el.get("value")))
        el.clear()
    elif el.tag == "Workout":
        d = (el.get("startDate") or "")[:10]
        if d >= since and el.get("workoutActivityType") == "HKWorkoutActivityTypeRunning":
            avg = mx = ""
            for c in el.findall("WorkoutStatistics"):
                if c.get("type") == "HKQuantityTypeIdentifierHeartRate":
                    avg, mx = c.get("average", ""), c.get("maximum", "")
            dist = el.get("totalDistance") or ""
            rows.append((d, dist, el.get("duration", ""), avg, mx))
        el.clear()
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["kind", "date", "value1", "value2", "value3", "value4"])
    for d in sorted(rhr):
        w.writerow(["resting_hr", d, round(sum(rhr[d]) / len(rhr[d]), 1)])
    for d in sorted(hrv):
        w.writerow(["hrv_sdnn_mean", d, round(sum(hrv[d]) / len(hrv[d]), 1)])
    for r in sorted(rows):
        w.writerow(["run_distance_duration_avghr_maxhr", *r])
print(f"Wrote {out}: {len(rhr)} resting HR days, {len(hrv)} HRV days, {len(rows)} runs")
