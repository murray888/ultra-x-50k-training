"""Assemble the static site into dist/ (site files + data + plan)."""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
if DIST.exists():
    shutil.rmtree(DIST)
shutil.copytree(ROOT / "site", DIST)
(DIST / "data").mkdir()
for name in ("adjusted.json", "commentary.json", "meta.json", "activities_murray.json", "activities_rich.json"):
    src = ROOT / "data" / name
    if src.exists():
        shutil.copy(src, DIST / "data" / name)
shutil.copy(ROOT / "config" / "plan.json", DIST / "data" / "plan.json")
(DIST / ".nojekyll").write_text("")
print("Site built in", DIST)
