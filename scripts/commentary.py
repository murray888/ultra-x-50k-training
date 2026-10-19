"""Ask Claude for a short weekly coaching note per athlete (optional).

Needs the ANTHROPIC_API_KEY secret. Without it, the site simply shows no commentary.
Claude only describes what the rules engine already decided; it never changes the plan.
"""
import json
import os
import datetime as dt
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")

SYSTEM = (
    "You write a short weekly coaching note for an amateur runner preparing for a 50km trail race. "
    "Use UK spelling and a calm, practical tone. Maximum 110 words, plain sentences, no headings, "
    "no emoji. Use only the figures provided. Explain any plan adjustments in plain words. "
    "This is general guidance, not medical advice: if pain or an injury is mentioned, suggest seeing a physio."
)


def note_for(key, a):
    s = a["summary"]
    recent = [w for w in a["weeks"] if w["status"] in ("Done", "Partial", "Missed")][-4:]
    payload = {"athlete": a["name"], "weeks_to_race": s["weeks_to_race"], "current_week": s["current_week"],
               "next_long_run": s["next_long"], "flags": s["flags"], "suggestions": s["notes"],
               "last_four_weeks": [{"week": w["week"], "planned_km": w["planned_km"], "actual_km": w["actual_km"],
                                    "planned_long": w["planned_long"], "actual_long": w["actual_long"],
                                    "status": w["status"]} for w in recent],
               "easy_run_trend": a["metrics"][-4:]}
    r = requests.post("https://api.anthropic.com/v1/messages", timeout=60, headers={
        "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01",
        "content-type": "application/json"}, json={
        "model": MODEL, "max_tokens": 400, "system": SYSTEM,
        "messages": [{"role": "user", "content": "Write this week's note from this data:\n" + json.dumps(payload)}]})
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json()["content"]).strip()


def main():
    out = {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "notes": {}}
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set: skipping commentary")
    else:
        adjusted = json.loads((DATA / "adjusted.json").read_text())
        for key, a in adjusted["athletes"].items():
            if not a["summary"]["current_week"] and not any(w["status"] != "Upcoming" for w in a["weeks"]):
                continue  # nothing to comment on yet
            try:
                out["notes"][key] = note_for(key, a)
            except Exception as exc:  # a failed note must never break the site build
                print(f"commentary for {key} failed: {exc}")
    (DATA / "commentary.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
