"""Print every location EE Calculator uses. `pixi run where`.

The distributed layout (state under %LOCALAPPDATA%, outputs under Documents, credentials
in the OS store) costs discoverability; this is how it is paid, the way `pip cache dir`
and `uv cache dir` pay it.
"""

from __future__ import annotations

from eecalc import paths


def main() -> int:
    for key, value in paths.describe().items():
        print(f"{key:14} {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
