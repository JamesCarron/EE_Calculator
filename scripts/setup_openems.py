"""Fetch the openEMS runtime into the cache folder.

Written 2026-09-15 for C:\\Auterion\\Tools\\EE_Calculator.

Why a download rather than a build: openEMS needs CMake, a C++ toolchain, VTK,
CGAL, Boost and HDF5 to compile, and conda-forge has no package, so building
the submodule on a Windows workstation is a long and fragile detour. The source is
pinned by PINNED_SOURCE_COMMIT below rather than by a git submodule - 1017 files
that nothing imports is not how provenance is recorded; this script gets the
matching runtime.

The version is pinned deliberately. v0.0.36 is the current stable release and
its Windows wheels are built for Python 3.10 and 3.11, which is why pixi.toml
pins 3.11 - the newer v0.37.0-rc2 wheels are 3.13/3.14 and it is a release
candidate.

Everything lands in %LOCALAPPDATA%\\Auterion\\EE Calculator\\Cache\\openems, outside
the repository and outside the Drive-synced tree, so no 48 MB of binaries enter
the history and no download is uploaded to Drive. `pixi run where` prints it.

Usage: pixi run setup-em
"""

import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

from eecalc import paths

DEST = paths.cache_dir() / "openems"
RELEASE_API = "https://api.github.com/repos/thliebig/openEMS-Project/releases/tags/v0.0.36"
PINNED_TAG = "v0.0.36"
# The source tree the runtime was built from, kept for provenance now that the
# ext/openEMS-Project submodule is gone: https://github.com/thliebig/openEMS-Project
PINNED_SOURCE_COMMIT = "04e054d8c91e1d31e14161b3ac20cc6f3c32d50d"


def find_asset():
    """The Windows zip for the pinned release, and its size."""
    with urllib.request.urlopen(RELEASE_API, timeout=30) as r:
        data = json.load(r)
    for a in data.get("assets", []):
        if a["name"].lower().endswith(".zip"):
            return a["browser_download_url"], a["name"], a["size"]
    raise SystemExit("no zip asset on release %s" % PINNED_TAG)


def main():
    if DEST.exists() and any(DEST.iterdir()):
        print("openEMS already present at %s" % DEST)
        print("delete that folder to re-fetch.")
        return 0

    url, name, size = find_asset()
    print("openEMS %s" % PINNED_TAG)
    print("  %s  (%.1f MB)" % (name, size / 1e6))
    print("  from %s" % url)
    print("  into %s  (gitignored)" % DEST)
    if "--yes" not in sys.argv:
        try:
            reply = input("\nDownload? [y/N] ").strip().lower()
        except EOFError:
            # non-interactive: never download 50 MB without being asked to
            print("\nnot interactive; re-run with --yes to download.")
            return 1
        if reply not in ("y", "yes"):
            print("nothing downloaded.")
            return 1

    print("\ndownloading...")
    with urllib.request.urlopen(url, timeout=600) as r:
        blob = r.read()
    print("  %.1f MB, sha256 %s" % (len(blob) / 1e6, hashlib.sha256(blob).hexdigest()[:16]))

    DEST.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        z.extractall(DEST)
    print("  unpacked %d entries" % len(list(DEST.rglob("*"))))

    wheels = sorted(DEST.rglob("*.whl"))
    print("\nPython wheels in the archive:")
    for w in wheels:
        print("  %s" % w.relative_to(DEST))
    if wheels:
        print("\nInstall the ones matching this environment's Python with:")
        print("  pixi run python -m pip install <wheel>")
    print("\nThe backend finds the runtime by looking in %s." % DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
