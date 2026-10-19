"""Generate config/plan.json: the shared, distance-based 26-week plan for Murray and Rich.

Edit the tables below and re-run `python scripts/make_plan.py` to change the plan.
The weekly job (scripts/adapt.py) then adjusts the *upcoming* weeks from logged runs.
"""
import json
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEEK1_SATURDAY = dt.date(2026, 10, 24)
RACE_DATE = dt.date(2027, 4, 17)

# Shared Saturday long runs (km). Weeks 1-3 are individual because Murray is away.
SHARED_LONG = {4: 10, 5: 13, 6: 10, 7: 16, 8: 18, 9: 18, 10: 14, 11: 21, 12: 23, 13: 25,
               14: 27, 15: 28, 16: 18, 17: 29, 18: 32, 19: 30, 20: 20, 21: 30, 22: 27,
               23: 33, 24: 22, 25: 12, 26: 50}
CUTBACK = {6, 10, 16, 20}
NOTES = {
    1: "Murray: away, long run moved to Sun 25 Oct.",
    2: "Murray: travelling, long run moved to Fri 30 Oct.",
    3: "Murray: travelling, no long run this week. Midweek runs optional.",
    4: "First shared Saturday run. Murray lands back Wed 11 Nov, so keep it easy.",
    6: "Cutback week.", 10: "Cutback week (Boxing Day weekend).", 16: "Cutback week.",
    18: "Longest run so far. Hilly trail if possible.", 20: "Cutback week.",
    23: "Dress rehearsal: full race kit and about 900m+ of climbing.",
    24: "Taper begins.", 26: "RACE WEEK: Ultra X Spring Trail Series 50km, Sat 17 April, 9am start.",
}
PHASES = [(1, 8, "Base"), (9, 12, "Aerobic build"), (13, 20, "Specific build"),
          (21, 23, "Peak"), (24, 25, "Taper"), (26, 26, "Race")]

# Murray's weekday runs (km): Run A (quality), Run B (easy).
MURRAY_RUNS = {1: (5, 4), 2: (6, 5), 3: (6, 5), 4: (5, 4), 5: (6, 5), 6: (5, 4), 7: (7, 5),
               8: (7, 5), 9: (7, 6), 10: (6, 5), 11: (8, 6), 12: (8, 6), 13: (8, 6),
               14: (8, 6), 15: (9, 6), 16: (7, 5), 17: (9, 7), 18: (10, 7), 19: (10, 7),
               20: (8, 6), 21: (10, 7), 22: (9, 6), 23: (8, 6), 24: (6, 5), 25: (5, 4), 26: (5, 3)}
MURRAY_A = {w: "Easy + 6 x 20s strides" for w in range(1, 9)}
MURRAY_A.update({w: "Hill repeats (hard up, jog down)" for w in (9, 10, 11)})
MURRAY_A.update({w: "Steady 20-40 min at HR 155-165" for w in range(12, 24)})
MURRAY_A.update({24: "Short steady effort", 25: "3 x 5 min at race effort", 26: "Easy + strides"})
MURRAY_A.update({6: "Easy (cutback)", 10: "Easy (cutback)", 16: "Easy (cutback)", 20: "Easy (cutback)"})
MURRAY_LONG_OVERRIDE = {1: (12, "2026-10-25"), 2: (13, "2026-10-30"), 3: (0, None)}
MURRAY_OPTIONAL = {3}

# Rich's plan (from his own Ultra X Spring 50K plan): Tue / Thu sessions in minutes.
RICH_ROWS = [
    ("25 min easy", 25, "25 min easy", 25), ("30 min easy", 30, "30 min easy + 4 strides", 30),
    ("30 min easy", 30, "30 min easy + 4 strides", 30), ("30 min easy", 30, "30 min easy + 4 strides", 30),
    ("40 min easy", 40, "35 min easy + 6 strides", 35), ("30 min easy", 30, "30 min easy", 30),
    ("45 min easy", 45, "40 min easy + 6 strides", 40), ("45 min, last 10 steady", 45, "40 min easy + 6 strides", 40),
    ("50 min incl 3 x 8 min tempo", 50, "40 min incl 6 x 60s hills", 40), ("40 min easy", 40, "35 min easy", 35),
    ("55 min incl 20 min tempo", 55, "45 min incl 8 x 75s hills", 45),
    ("60 min incl 2 x 15 min tempo", 60, "50 min incl 8 x 90s hills", 50),
    ("60 min incl 30 min tempo", 60, "50 min incl 10 x 60s hills", 50), ("60 min steady", 60, "50 min incl 6 x 2 min hills", 50),
    ("65 min incl 3 x 10 min tempo", 65, "55 min incl 6 x 2 min hills", 55), ("45 min easy", 45, "40 min easy", 40),
    ("65 min incl 30 min tempo", 65, "55 min incl 8 x 2 min hills", 55), ("65 min steady", 65, "55 min incl 8 x 2 min hills", 55),
    ("65 min incl 2 x 15 min tempo", 65, "55 min incl 8 x 2 min hills", 55), ("45 min easy", 45, "40 min easy", 40),
    ("65 min incl 30 min tempo", 65, "55 min incl 8 x 2 min hills", 55), ("70 min steady", 70, "55 min incl 6 x 3 min hills", 55),
    ("60 min incl 20 min tempo", 60, "50 min easy", 50), ("55 min incl 15 min tempo", 55, "45 min easy", 45),
    ("45 min incl 3 x 5 min at race effort", 45, "40 min easy", 40), ("40 min easy + 4 strides", 40, "25 min easy shakeout", 25),
]
RICH_EASY_PACE = 6.5   # min/km, used only to turn Rich's minute-based weekday runs into km
RICH_LONG_OVERRIDE = {1: 5.4, 2: 6.9, 3: 7.7}  # his 35, 45 and 50 minute runs, in km


def apply_swaps():
    """Apply config/plan_edits.json: {"swaps": [[6, 7], ...]} swaps two weeks' shared long runs and cutback flags.

    Use `python scripts/make_plan.py --swap 6 7` to move a cutback from week 6 to week 7 (and vice versa).
    """
    f = ROOT / "config" / "plan_edits.json"
    swaps = json.loads(f.read_text()).get("swaps", []) if f.exists() else []
    for a, b in swaps:
        SHARED_LONG[a], SHARED_LONG[b] = SHARED_LONG[b], SHARED_LONG[a]
        ca, cb = a in CUTBACK, b in CUTBACK
        CUTBACK.discard(a); CUTBACK.discard(b)
        if ca: CUTBACK.add(b)
        if cb: CUTBACK.add(a)
        for week in (a, b):
            NOTES[week] = ("Cutback week." if week in CUTBACK else "").strip()


def phase(week):
    return next(name for lo, hi, name in PHASES if lo <= week <= hi)


def build():
    apply_swaps()
    weeks = []
    for w in range(1, 27):
        sat = WEEK1_SATURDAY + dt.timedelta(weeks=w - 1)
        a, b = MURRAY_RUNS[w]
        m_long, m_date = MURRAY_LONG_OVERRIDE.get(w, (SHARED_LONG.get(w), sat.isoformat()))
        r_long = RICH_LONG_OVERRIDE.get(w, SHARED_LONG.get(w))
        tue, tue_m, thu, thu_m = RICH_ROWS[w - 1]
        weeks.append({
            "week": w, "monday": (sat - dt.timedelta(days=5)).isoformat(), "saturday": sat.isoformat(),
            "sunday": (sat + dt.timedelta(days=1)).isoformat(), "phase": phase(w),
            "cutback": w in CUTBACK, "shared_long": w in SHARED_LONG, "note": NOTES.get(w, ""),
            "athletes": {
                "murray": {"long_km": m_long, "long_date": m_date, "optional": w in MURRAY_OPTIONAL,
                           "runs": [{"label": "Run A", "desc": MURRAY_A[w], "km": a},
                                    {"label": "Run B", "desc": "Easy, HR up to 150", "km": b}]},
                "rich": {"long_km": r_long, "long_date": sat.isoformat(), "optional": False,
                         "runs": [{"label": "Tue", "desc": tue, "km": round(tue_m / RICH_EASY_PACE, 1)},
                                  {"label": "Thu", "desc": thu, "km": round(thu_m / RICH_EASY_PACE, 1)}]},
            }})
    return {
        "race": {"name": "Ultra X Spring Trail Series 50km", "date": RACE_DATE.isoformat(), "distance_km": 50,
                 "start": "09:00", "location": "Cowdray Estate, Midhurst (confirm venue with the race pack)"},
        "athletes": {
            "murray": {"name": "Murray", "easy_hr_ceiling": 150, "colour_slot": 1},
            "rich": {"name": "Rich", "easy_hr_ceiling": None, "colour_slot": 2},
        },
        "weeks": weeks,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 4 and sys.argv[1] == "--swap":
        f = ROOT / "config" / "plan_edits.json"
        data = json.loads(f.read_text()) if f.exists() else {"swaps": []}
        data["swaps"].append([int(sys.argv[2]), int(sys.argv[3])])
        f.write_text(json.dumps(data))
    out = ROOT / "config" / "plan.json"
    out.write_text(json.dumps(build(), indent=1))
    print(f"Wrote {out}")
