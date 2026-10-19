"""Copy runs/<athlete>.json (committed, from Shortcut uploads) into data/ for the site and rules engine."""
import json
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
for key in ("murray", "rich"):
    src = ROOT / "runs" / f"{key}.json"
    runs = [dict(r, route=[]) for r in json.loads(src.read_text())] if src.exists() else []
    (DATA / f"activities_{key}.json").write_text(json.dumps(runs))
    print(f"{key}: {len(runs)} runs")
(DATA / "meta.json").write_text(json.dumps(
    {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "demo": False}))
