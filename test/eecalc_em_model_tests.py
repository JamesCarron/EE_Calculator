"""Tests for the openEMS pad-capacitance model generator.

Written 2026-09-15 for C:\\Auterion\\Tools\\EE_Calculator. The model generator is
deliberately separate from the solver so it can be tested without a 48 MB
native dependency installed - the physics decisions live here, not in openEMS.

The check that matters most is the mesh one: a wavelength-only cell size puts
less than one cell across a 100 um dielectric and returns a confident wrong
capacitance, which is exactly the failure a test has to prevent because the
number looks perfectly reasonable.

Usage: python eecalc_em_model_tests.py
"""

import ast
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Auterion\Tools\EE_Calculator\src")
from em.model import PadModel, Plane, build_script, EPS0  # noqa: E402

fails = []
passes = []


def ok(label, cond):
    (passes if cond else fails).append(label)
    print(("  ok   " if cond else "  FAIL ") + label)


def near(label, got, want, tol_pct):
    ok("%s = %.4g" % (label, got), abs(got - want) <= abs(want) * tol_pct / 100)


print("\n== the model refuses geometry that cannot mean anything ==")
ok("a pad with no area is rejected", PadModel(pad_w_um=0).validate())
ok("a plane above the pad is rejected", PadModel(planes=[Plane(-10.0)]).validate())
ok("permittivity below 1 is rejected", PadModel(er=0.5).validate())
ok("no planes at all is rejected", PadModel(planes=[]).validate())
ok("two planes at the same depth are rejected",
   PadModel(planes=[Plane(100.0), Plane(100.0)]).validate())
ok("a port index off the end is rejected",
   PadModel(planes=[Plane(100.0)], port_plane=3).validate())
ok("a sane model has nothing to complain about", not PadModel().validate())

print("\n== the mesh is driven by the geometry, not only the wavelength ==")
m = PadModel(planes=[Plane(100.0)])
ok("the wavelength criterion alone would be far too coarse",
   m.wavelength_resolution_um() > 200)
ok("the cell actually used resolves the dielectric",
   m.mesh_resolution_um() <= 100.0 / 8 + 1e-9)
near("eight cells across a 100 um gap", 100.0 / m.mesh_resolution_um(), 8, 1)
ok("and it is never coarser than the wavelength criterion",
   m.mesh_resolution_um() <= m.wavelength_resolution_um())
thin = PadModel(planes=[Plane(50.0)])
ok("a thinner dielectric forces a finer cell",
   thin.mesh_resolution_um() < m.mesh_resolution_um())
# the pad criterion only governs once the pad is smaller than eight tenths of
# the dielectric thickness; at 200 um over 100 um the dielectric still wins
mid = PadModel(pad_w_um=200, pad_l_um=200, planes=[Plane(100.0)])
ok("a 200 um pad over 100 um is still dielectric-limited",
   abs(mid.mesh_resolution_um() - 100.0 / 8) < 1e-9)
tiny = PadModel(pad_w_um=50, pad_l_um=50, planes=[Plane(100.0)])
ok("a pad small enough to govern does force a finer cell",
   tiny.mesh_resolution_um() < m.mesh_resolution_um())
voided = PadModel(planes=[Plane(100.0, void_d_um=60.0)])
ok("a small void forces a finer cell as well",
   voided.mesh_resolution_um() < m.mesh_resolution_um())

print("\n== the run cost is estimated before anyone waits for it ==")
est = PadModel().cell_estimate()
ok("a cell count is reported", est["cells"] > 0)
ok("an ordinary pad is not flagged heavy", not est["heavy"])
big = PadModel(pad_w_um=20000, pad_l_um=20000, planes=[Plane(100.0)]).cell_estimate()
ok("a large structure on a thin dielectric is flagged heavy", big["heavy"])
# cost, not raw cell count, is the thing to compare: a finer mesh costs more
# per cell too, because the timestep shrinks with it
ok("a thinner dielectric costs more to solve",
   PadModel(planes=[Plane(50.0)]).cell_estimate()["relative_cost"] >
   PadModel(planes=[Plane(100.0)]).cell_estimate()["relative_cost"])
ok("the reference pad sits near a relative cost of 1",
   0.3 < PadModel(planes=[Plane(100.0)]).cell_estimate()["relative_cost"] < 3)
ok("a big structure on thin dielectric is much dearer",
   PadModel(pad_w_um=20000, pad_l_um=20000,
            planes=[Plane(100.0)]).cell_estimate()["relative_cost"] > 20)

print("\n== the parallel-plate floor is right, and it is only a floor ==")
m = PadModel(pad_w_um=500, pad_l_um=600, er=4.3, planes=[Plane(100.0)])
hand = EPS0 * 4.3 * (500e-6 * 600e-6) / 100e-6 * 1e12
near("0402 pad over 100 um of FR-4", m.parallel_plate_pF(0), hand, 0.01)
near("and that is about 0.114 pF", m.parallel_plate_pF(0), 0.1142, 1)
ok("twice the depth is half the capacitance",
   abs(PadModel(planes=[Plane(200.0)]).parallel_plate_pF(0) * 2
       - PadModel(planes=[Plane(100.0)]).parallel_plate_pF(0)) < 1e-9)

print("\n== the generated script is valid and says what it should ==")
m = PadModel(planes=[Plane(100.0, 0.0, "L2"), Plane(400.0, 900.0, "L3")])
src = build_script(m)
try:
    ast.parse(src)
    ok("it parses as Python", True)
except SyntaxError as e:
    ok("it parses as Python (%s)" % e, False)
ok("it imports the solver", "from openEMS import openEMS" in src)
ok("it builds a CSXCAD structure", "ContinuousStructure()" in src)
ok("it drives a lumped port", "AddLumpedPort" in src)
ok("it reads the impedance, not just S11", "uf_tot / port.if_tot" in src)
ok("it derives C from the reactive part", "-1.0 / (2 * np.pi * f * np.imag(Z))" in src)
ok("it checks the answer is actually capacitive", "'capacitive'" in src)
ok("it checks flatness across a decade rather than trusting one point",
   "flatness" in src)
ok("it prints a machine-readable result", "print('RESULT ' + json.dumps(out))" in src)
ok("no placeholder survived", "{}" not in src and "TODO" not in src)

print("\n== voids appear only when asked ==")
plain = build_script(PadModel(planes=[Plane(100.0, 0.0)]))
cut = build_script(PadModel(planes=[Plane(100.0, 900.0)]))
ok("a full plane has no void geometry", '"void_d_um": 0.0' in plain)
ok("a voided plane carries its diameter", '"void_d_um": 900.0' in cut)
ok("the void is cut by priority, not by subtraction", "priority=20" in cut)
ok("the cutting region is the substrate, so it is a hole not a conductor",
   "AddCylinder" in cut)

print("\n== the port goes where it was asked to ==")
two = PadModel(planes=[Plane(100.0, 0.0, "L2"), Plane(400.0, 0.0, "L3")], port_plane=1)
ok("a port against the second plane references it", "port_plane = 1" in build_script(two))
ok("the port spans from that plane up to the pad",
   "z_port = -planes[port_plane]['depth_um']" in build_script(two))

print("\n== the domain is big enough not to load the structure ==")
src = build_script(PadModel(planes=[Plane(100.0)]))
lateral = float([l for l in src.splitlines() if l.startswith("lateral")][0].split("=")[1])
air = float([l for l in src.splitlines() if l.startswith("air ")][0].split("=")[1])
ok("laterally at least three pad widths clear", lateral >= 3 * 600)
ok("and the air above clears the structure", air >= 10 * 100)

print("\n== a broken model refuses to generate rather than emitting nonsense ==")
try:
    build_script(PadModel(pad_w_um=-1))
    ok("invalid geometry raises", False)
except ValueError:
    ok("invalid geometry raises", True)

print("\n%d passed, %d failed" % (len(passes), len(fails)))
sys.exit(1 if fails else 0)
