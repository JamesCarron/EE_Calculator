"""Worked example: does voiding the plane under an RF pad actually help?

The design question behind the pad card. An 0402 pad on layer 1, ground on
layer 2 at 100 um, a second ground at 400 um. Voiding L2 under the pad removes
the nearest plane - but L3 is still there, and the field simply reaches further
down, so the capacitance does not fall anything like as far as the parallel
plate figure suggests.

Run this to generate the three openEMS models that answer it:

    pixi run python examples/pad_over_voided_plane.py

It writes the scripts and prints what each one costs to solve. Running them
needs the runtime: pixi run setup-em.
"""

from pathlib import Path

from eecalc import paths
from eecalc.em.model import PadModel, Plane, build_script

ROOT = Path(__file__).resolve().parent.parent

OUT = paths.documents_dir() / "em_models"

CASES = {
    "01_full_plane": PadModel(
        pad_w_um=500, pad_l_um=600,
        planes=[Plane(100.0, 0.0, "L2 ground"), Plane(400.0, 0.0, "L3 ground")]),
    "02_void_900um": PadModel(
        pad_w_um=500, pad_l_um=600,
        planes=[Plane(100.0, 900.0, "L2 ground, voided"), Plane(400.0, 0.0, "L3 ground")]),
    "03_void_1500um": PadModel(
        pad_w_um=500, pad_l_um=600,
        planes=[Plane(100.0, 1500.0, "L2 ground, wide void"), Plane(400.0, 0.0, "L3 ground")]),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("%-18s %10s %10s %12s" % ("case", "cell um", "cells", "rel. cost"))
    for name, m in CASES.items():
        est = m.cell_estimate()
        (OUT / (name + ".py")).write_text(build_script(m), encoding="utf-8")
        print("%-18s %10.2f %9.2fM %11.1fx%s" % (
            name, est["cell_um"], est["cells"] / 1e6, est["relative_cost"],
            "  HEAVY" if est["heavy"] else ""))

    ref = CASES["01_full_plane"]
    print("\nParallel-plate floor to L2, ignoring fringe and any void: %.3f pF"
          % ref.parallel_plate_pF(0))
    print("Same pad referenced to L3 instead:                        %.3f pF"
          % ref.parallel_plate_pF(1))
    print("\nThose two are the bracket. A 900 um void does not take the pad to the")
    print("lower figure, because the field spreads rather than stopping - which is")
    print("the whole reason this gets simulated instead of interpolated.")
    print("\nModels written to %s" % OUT)


if __name__ == "__main__":
    main()
