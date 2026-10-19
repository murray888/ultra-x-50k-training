"""Compare logged runs with the plan and adjust the upcoming long runs.

Writes data/adjusted.json. Rules (all visible in the site as "reasons"):
  1. Ramp cap: a long run never exceeds 12% above the longest of your last three completed
     long runs. Missing a long run therefore repeats distance until you have caught up.
  2. Two missed long runs in a row (under 70% of plan): the reference drops by 25%.
  3. Fatigue flag: two or more runs of 8 km+ in the last 14 days with average HR more than
     8 bpm above the easy ceiling: long runs for the next three weeks are cut by 10%.
  4. Volume shortfall: the last two completed weeks both under 60% of planned km:
     long runs for the next three weeks are cut by 15%.
  5. Niggle flag (config/overrides.json): long runs for the next three weeks are cut by 25%.
  6. Nothing is ever increased above the plan, and race week is never changed.
Manual overrides live in config/overrides.json.
"""
import json
import os
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def today():
    t = os.environ.get("TODAY")
    return dt.date.fromisoformat(t) if t else dt.date.today()


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def half(x):
    return round(x * 2) / 2


def planned_km(a):
    return (a["long_km"] or 0) + sum(r["km"] for r in a["runs"])


def week_runs(runs, w):
    return [r for r in runs if w["monday"] <= r["date"] <= w["sunday"]]


def adapt_athlete(plan, key, runs, overrides, now):
    ceiling = plan["athletes"][key]["easy_hr_ceiling"]
    metric_ceiling = ceiling or 150
    flags_manual = overrides.get("flags", {}).get(key, [])
    forced = overrides.get("weeks", {}).get(key, {})
    weeks = plan["weeks"]
    now_iso = now.isoformat()

    current = next((w["week"] for w in weeks if w["monday"] <= now_iso <= w["sunday"]), None)
    first_open = current or next((w["week"] for w in weeks if w["monday"] > now_iso), None)

    # Flags are evaluated once, as of today.
    flags = []
    recent = [r for r in runs if 0 <= (now - dt.date.fromisoformat(r["date"])).days <= 14]
    if ceiling:
        hot = [r for r in recent if r["distance_km"] >= 8 and r.get("avg_hr") and r["avg_hr"] > ceiling + 8]
        if len(hot) >= 2:
            flags.append(("fatigue", 0.90, f"{len(hot)} runs of 8 km+ in the last 14 days averaged more than "
                          f"8 bpm above the easy ceiling ({ceiling}). Long runs cut by 10% for three weeks."))
    done = [w for w in weeks if w["sunday"] < now_iso and not w["athletes"][key]["optional"]]
    last2 = done[-2:]
    if len(last2) == 2 and all(
            sum(r["distance_km"] for r in week_runs(runs, w)) < 0.6 * planned_km(w["athletes"][key]) for w in last2):
        flags.append(("shortfall", 0.85, "The last two completed weeks were under 60% of planned distance. "
                      "Long runs cut by 15% for three weeks."))
    if "niggle" in flags_manual:
        flags.append(("niggle", 0.75, "Niggle flagged in config/overrides.json. Long runs cut by 25% for three weeks."))
    mult = 1.0
    for _, m, _ in flags:
        mult *= m

    history, out = [], []
    for w in weeks:
        a = w["athletes"][key]
        wr = week_runs(runs, w)
        actual_km = round(sum(r["distance_km"] for r in wr), 1)
        actual_long = max((r["distance_km"] for r in wr), default=0)
        planned_long = a["long_km"] or 0
        completed = w["sunday"] < now_iso
        reasons = []
        adjusted = planned_long

        if not completed and planned_long and w["week"] != 26:
            tail = history[-3:]
            if tail:
                ref = max(h["actual"] for h in tail)
                misses = 0
                for h in reversed(tail):
                    if h["completion"] < 0.7:
                        misses += 1
                    else:
                        break
                if misses >= 2:
                    ref *= 0.75
                    reasons.append("Two long runs missed in a row: reference reduced by 25%.")
                cap = ref + max(1.0, 0.12 * ref)
                if cap < planned_long:
                    adjusted = cap
                    reasons.append(f"Ramp cap: no more than 12% above your recent longest run ({ref:.1f} km).")
            if first_open and first_open <= w["week"] <= first_open + 2 and flags:
                reduced = planned_long * mult
                if reduced < adjusted:
                    adjusted = reduced
                reasons += [f[2] for f in flags]
            adjusted = min(planned_long, half(adjusted))
            fo = forced.get(str(w["week"]))
            if fo:
                adjusted = fo["long_km"]
                reasons = [f"Manual override: {fo.get('reason', 'set in overrides.json')}"]

        if completed and planned_long and not w["athletes"][key]["optional"] and not w["cutback"]:
            history.append({"week": w["week"], "actual": actual_long, "completion": actual_long / planned_long})
        elif completed and planned_long and w["cutback"]:
            pass  # cutback weeks do not set the reference

        if completed:
            if not planned_long:
                status = "Skipped (planned)"
            else:
                c = actual_long / planned_long
                status = "Done" if c >= 0.9 else "Partial" if c >= 0.5 else "Missed"
        else:
            status = "This week" if w["week"] == current else "Upcoming"
        out.append({
            "week": w["week"], "planned_long": planned_long, "adjusted_long": adjusted,
            "planned_km": round(planned_km(a), 1), "actual_km": actual_km, "actual_long": actual_long,
            "runs": len(wr), "status": status, "reasons": reasons})

    # Weekly easy-effort trend
    metrics = []
    for w in weeks:
        wr = [r for r in week_runs(runs, w) if r.get("avg_hr") and r["avg_hr"] <= metric_ceiling and r["distance_km"] >= 3]
        if wr:
            dist = sum(r["distance_km"] for r in wr)
            metrics.append({"week": w["week"], "easy_hr": round(sum(r["avg_hr"] for r in wr) / len(wr)),
                            "easy_pace": round(sum(r["moving_s"] for r in wr) / 60 / dist, 2)})

    nxt = next((o for o in out if o["status"] in ("This week", "Upcoming") and o["planned_long"]), None)
    notes = []
    if any(f[0] == "fatigue" for f in flags):
        notes.append("Make your next quality run easy.")
    if any(f[0] == "shortfall" for f in flags):
        notes.append("If only one midweek run fits, keep the quality run and drop the easy one.")
    race = dt.date.fromisoformat(plan["race"]["date"])
    summary = {
        "current_week": current, "weeks_to_race": max(0, (race - now).days // 7),
        "days_to_race": (race - now).days,
        "next_long": nxt, "flags": [f[0] for f in flags], "notes": notes,
        "total_km_since_start": round(sum(o["actual_km"] for o in out), 1),
        "last_run": runs[-1] if runs else None,
    }
    if summary["last_run"]:
        summary["last_run"] = {k: summary["last_run"][k] for k in ("date", "name", "distance_km", "avg_hr")}
    return {"name": plan["athletes"][key]["name"], "summary": summary, "weeks": out, "metrics": metrics}


def main():
    plan = json.loads((ROOT / "config" / "plan.json").read_text())
    overrides = load(ROOT / "config" / "overrides.json", {})
    now = today()
    result = {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
              "today": now.isoformat(), "race": plan["race"], "athletes": {}}
    for key in plan["athletes"]:
        runs = load(DATA / f"activities_{key}.json", [])
        result["athletes"][key] = adapt_athlete(plan, key, runs, overrides, now)
    (DATA / "adjusted.json").write_text(json.dumps(result, indent=1))
    print("Wrote data/adjusted.json for", ", ".join(result["athletes"]))


if __name__ == "__main__":
    main()
