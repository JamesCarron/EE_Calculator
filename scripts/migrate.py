"""One-off: move a pre-2026-09-17 clone's user_data/ to its new homes. `pixi run migrate`.

Written 2026-09-17 for the house-layout refactor (docs/private/Refactor_Plan.md). Until that
refactor the openEMS runtime and the generated EM models lived in user_data/ inside the
repository, which is Google-Drive synced; they now live under %LOCALAPPDATA% and Documents.
This script does the move for any other clone and then deletes the folder. It is safe to
run when there is nothing to move, and it never overwrites anything already at the target.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from eecalc import paths

REPO = Path(__file__).resolve().parents[1]
MOVES = [("openems", lambda: paths.cache_dir() / "openems"),
         ("em_models", lambda: paths.documents_dir() / "em_models")]


def main() -> int:
    ud = REPO / "user_data"
    if not ud.exists():
        print("nothing to migrate: no user_data/ in this checkout")
        return 0
    for name, target in MOVES:
        src = ud / name
        if not src.exists():
            continue
        dst = target()
        if dst.exists() and any(dst.iterdir()):
            print(f"{name:12} {dst} already has content - left in place, not merged")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            dst.rmdir()
        shutil.move(str(src), str(dst))
        print(f"{name:12} -> {dst}")
    leftover = [p.name for p in ud.iterdir()] if ud.exists() else []
    if leftover:
        print("left behind (nothing in the standard describes these): " + ", ".join(leftover))
        return 1
    shutil.rmtree(ud, ignore_errors=True)
    print("user_data/ removed; `pixi run where` prints where everything is now")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
