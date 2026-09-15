"""Run everything: rebuild the page, regenerate the node harness, then every
node suite and every structural checker.

Written 2026-09-15 for C:\\Auterion\\Tools\\EE_Calculator, when the project moved
onto a src/test/docs layout. Before this the suite was a shell loop that had to
be retyped from memory each time, which meant it was easy to run some of it and
believe you had run all of it.

Usage: pixi run test        (or: python test/run_all.py)
       python test/run_all.py -k atten     to run matching suites only
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WORK = HERE / ".work"

# structural checkers, in the order that fails most informatively: a page that
# does not load makes every other failure noise
CHECKERS = [
    ("page builds", [sys.executable, str(ROOT / "src" / "build_page.py")]),
    ("harness", [sys.executable, str(HERE / "eecalc_mkharness.py")]),
    ("script loads", [sys.executable, str(HERE / "eecalc_load_check.py")]),
    ("diagram geometry", [sys.executable, str(HERE / "eecalc_diagram_check.py")]),
    ("page structure", [sys.executable, str(HERE / "eecalc_check_page.py")]),
    ("EM model", [sys.executable, str(HERE / "eecalc_em_model_tests.py")]),
]


def node_suites():
    return sorted(p for p in HERE.glob("eecalc_*.js"))


def main():
    only = None
    if "-k" in sys.argv:
        only = sys.argv[sys.argv.index("-k") + 1]
    WORK.mkdir(exist_ok=True)

    failures = []
    for name, cmd in CHECKERS:
        if only and only not in name:
            continue
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        tail = (r.stdout or r.stderr or "").strip().splitlines()
        print("%-22s %s" % (name, tail[-1] if tail else "(no output)"))
        if r.returncode:
            failures.append(name)
            for line in (r.stdout or "").splitlines():
                if "FAIL" in line:
                    print("      " + line.strip())

    harness = WORK / "harness.js"
    if not harness.exists():
        print("\nharness missing - cannot run the node suites")
        sys.exit(1)
    run_js = WORK / "run.js"
    harness_src = harness.read_text(encoding="utf-8")

    for suite in node_suites():
        if only and only not in suite.name:
            continue
        run_js.write_text(harness_src + "\n" + suite.read_text(encoding="utf-8"),
                          encoding="utf-8")
        r = subprocess.run(["node", str(run_js)], capture_output=True, text=True,
                           encoding="utf-8")
        tail = (r.stdout or r.stderr or "").strip().splitlines()
        print("%-22s %s" % (suite.stem.replace("eecalc_", ""),
                            tail[-1] if tail else "(no output)"))
        if r.returncode:
            failures.append(suite.name)
            for line in (r.stdout or "").splitlines():
                if "FAIL" in line:
                    print("      " + line.strip())

    print()
    if failures:
        print("FAILED: " + ", ".join(failures))
        sys.exit(1)
    print("all green")


if __name__ == "__main__":
    main()
