"""Build an openEMS model for a pad over one or more reference planes.

Written 2026-09-15 for C:\\Auterion\\Tools\\EE_Calculator.

The question this answers is the one no closed form covers: what is a pad's
capacitance to each reference plane below it, and how much does voiding a plane
under the pad actually reduce it. A parallel-plate estimate handles the full
plane case and nothing else; the interior of the problem - a void comparable in
size to the pad - is three-dimensional, which is why it gets simulated.

Method. Build the stack in CSXCAD, drive a lumped port in z between the pad and
the plane of interest, run FDTD, and read the input impedance. Below the first
resonance a pad over a plane is a capacitor, so

    Z11 = 1/(j*omega*C)   ->   C = -1 / (omega * Im(Z11))

evaluated well below resonance and checked for flatness across a decade, since
a C read at a single frequency on a structure that is not actually capacitive
there is the classic way to get a confident wrong answer.

A void is cut by CSXCAD's priority model: the plane is PEC at one priority and
the void is the substrate material at a higher one, so the higher-priority
region wins inside the cylinder.

This module only *generates* the script. It does not import openEMS, so it is
testable without the solver installed - which is the whole point, because the
solver is a 48 MB native dependency and the model is the part with the physics
in it.

Verified by eecalc_em_model_tests.py.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path

# where `pixi run setup-em` puts the Windows runtime
DEFAULT_RUNTIME = str(Path(__file__).resolve().parents[2] / "user_data" / "openems" / "openEMS")

C0 = 299792458.0
EPS0 = 8.8541878128e-12


@dataclass
class Plane:
    """A reference plane below the pad.

    depth_um   how far below the pad's underside this plane sits
    void_d_um  diameter of a circular void centred under the pad; 0 for none
    name       what the results call it
    """
    depth_um: float
    void_d_um: float = 0.0
    name: str = "plane"


@dataclass
class PadModel:
    """A rectangular pad over a stack of reference planes."""
    pad_w_um: float = 500.0
    pad_l_um: float = 600.0
    er: float = 4.3
    tand: float = 0.02
    planes: list = field(default_factory=lambda: [Plane(100.0, 0.0, "L2")])
    f_max_hz: float = 10e9
    # which plane the port is driven against; the others are left floating so
    # each one's contribution can be read separately
    port_plane: int = 0
    end_criteria: float = 1e-5

    def validate(self) -> list:
        """Problems that would make the model meaningless, as plain sentences."""
        bad = []
        if self.pad_w_um <= 0 or self.pad_l_um <= 0:
            bad.append("The pad must have a positive width and length.")
        if self.er < 1:
            bad.append("Relative permittivity cannot be below 1.")
        if not self.planes:
            bad.append("There must be at least one reference plane to measure against.")
        for i, p in enumerate(self.planes):
            if p.depth_um <= 0:
                bad.append("Plane %d sits at or above the pad; depth must be positive." % (i + 1))
            if p.void_d_um < 0:
                bad.append("Plane %d has a negative void diameter." % (i + 1))
        depths = [p.depth_um for p in self.planes]
        if len(set(depths)) != len(depths):
            bad.append("Two planes are at the same depth.")
        if not 0 <= self.port_plane < len(self.planes):
            bad.append("The port plane index is outside the stack.")
        return bad

    # ---------------------------------------------------------------- estimates

    def parallel_plate_pF(self, index: int) -> float:
        """The floor: plate area over depth, no fringe, no void. Used to sanity
        check the simulated answer, not to replace it."""
        p = self.planes[index]
        area = self.pad_w_um * self.pad_l_um * 1e-12
        return EPS0 * self.er * area / (p.depth_um * 1e-6) * 1e12

    def wavelength_resolution_um(self) -> float:
        """Lambda/50 in the substrate at f_max, the usual FDTD starting point."""
        return C0 / (self.f_max_hz * math.sqrt(self.er)) / 1e-6 / 50

    def mesh_resolution_um(self) -> float:
        """The cell size, which is the *smaller* of the wavelength criterion and
        what the geometry needs.

        This distinction matters more than it looks. A pad over 100 um of
        prepreg has a wavelength criterion of nearly 300 um at 10 GHz, which
        would put less than one cell across the dielectric and return a
        confident, wrong capacitance. Capacitance is set by the near field
        between two close surfaces, so the thinnest gap has to be resolved
        whatever the wavelength says.
        """
        thinnest_gap = min(self._gaps())
        geometric = min(thinnest_gap / 8.0,          # across the dielectric
                        min(self.pad_w_um, self.pad_l_um) / 10.0)
        voids = [p.void_d_um for p in self.planes if p.void_d_um > 0]
        if voids:
            geometric = min(geometric, min(voids) / 10.0)
        return min(self.wavelength_resolution_um(), geometric)

    def _gaps(self) -> list:
        """Dielectric thicknesses between the pad and each successive plane."""
        depths = sorted(p.depth_um for p in self.planes)
        gaps, prev = [], 0.0
        for d in depths:
            gaps.append(d - prev)
            prev = d
        return gaps

    def cell_estimate(self) -> dict:
        """Roughly how big the run is, so a card can warn before starting one.

        The mesh is graded: fine over the structure, coarsening out to the
        wavelength cell at the domain walls. Counting the whole domain at the
        coarse cell makes the estimate insensitive to the very thing that
        drives the cost, so the fine region is counted separately.

        FDTD cost is cells times timesteps, and the timestep is bounded by the
        *smallest* cell, so halving the cell size costs roughly sixteen times,
        not two. `relative_cost` carries that, normalised to a plain 0402 pad
        over 100 um, because "4.2 million cells" means nothing to most readers
        and "about 30 times a basic run" means something.
        """
        res = self.mesh_resolution_um()
        coarse = max(res, self.wavelength_resolution_um() / 4)
        deepest = max(p.depth_um for p in self.planes)
        pad_span = max(self.pad_w_um, self.pad_l_um)
        lateral = max(4 * deepest, 2 * pad_span)
        air = max(4 * deepest, 2 * pad_span)

        # Mirror what build_script actually lays down, or the estimate is
        # fiction. Fine band over the pad plus two dielectric heights either
        # side; beyond it SmoothMeshLines grades by at most 1.4x per step until
        # it reaches the coarse cell, then runs coarse to the wall.
        fine_span = max(pad_span, max((p.void_d_um for p in self.planes), default=0)) + 4 * deepest
        fine_span = min(fine_span, 2 * lateral)
        n_fine = fine_span / res
        n_grade = 2 * math.ceil(math.log(max(coarse / res, 1.0001), 1.4))
        n_coarse = max(0.0, 2 * lateral - fine_span) / coarse
        nx = ny = int(n_fine + n_grade + n_coarse) + 1
        # z: at least nine lines across every gap, then graded through the air
        nz = int(sum(max(9, g / res) for g in self._gaps())
                 + math.ceil(math.log(max(coarse / res, 1.0001), 1.4))
                 + air / coarse) + 1
        cells = nx * ny * nz

        raw = cells / res                   # cells x timesteps, to a constant
        return {"cell_um": res, "nx": nx, "ny": ny, "nz": nz, "cells": cells,
                "raw_cost": raw, "relative_cost": raw / _reference_raw_cost(),
                "heavy": cells > 5e6 or raw / _reference_raw_cost() > 20}

    def extract_f_hz(self) -> float:
        """Where to read the capacitance: two decades below f_max, which is well
        below any resonance of a structure this small."""
        return self.f_max_hz / 100.0


_REF_RAW = None


def _reference_raw_cost() -> float:
    """The cost of a plain 0402 pad over 100 um, which `relative_cost` is
    measured against. Derived from the model itself rather than a hand-typed
    constant, so it cannot drift out of step with the meshing rules."""
    global _REF_RAW
    if _REF_RAW is None:
        _REF_RAW = 1.0                      # break the recursion for this call
        _REF_RAW = PadModel(pad_w_um=500.0, pad_l_um=600.0,
                            planes=[Plane(100.0)]).cell_estimate()["raw_cost"]
    return _REF_RAW


def _fmt(x) -> str:
    return repr(round(float(x), 6))


def build_script(m: PadModel, sim_dir: str = None, runtime_dir: str = None) -> str:
    """Emit a standalone openEMS Python script for this model."""
    bad = m.validate()
    if bad:
        raise ValueError("; ".join(bad))

    deepest = max(p.depth_um for p in m.planes)
    # lateral padding: enough substrate around the pad that the sidewalls do not
    # load it, and enough air above that the boundary does not either
    pad_span = max(m.pad_w_um, m.pad_l_um)
    lateral = max(4 * deepest, 2 * pad_span)
    air = max(4 * deepest, 2 * pad_span)
    res = m.mesh_resolution_um()
    port_depth = m.planes[m.port_plane].depth_um

    L = []
    A = L.append
    A('"""openEMS model generated by EE_Calculator - pad capacitance over planes.')
    A("")
    A("Do not edit by hand; regenerate from the pad card. The geometry is in")
    A("micrometres and the capacitance is read from Im(Z11) well below resonance.")
    A('"""')
    A("import os, sys, json")
    A("")
    A("# The Windows build ships its own Boost/HDF5/VTK DLLs beside openEMS.exe,")
    A("# and the Python extension cannot find them unless the directory is added")
    A("# explicitly - a plain import fails with an unhelpful 'DLL load failed'.")
    A("_home = os.environ.get('OPENEMS_HOME', %s)" % repr(runtime_dir or DEFAULT_RUNTIME))
    A("if os.path.isdir(_home):")
    A("    os.add_dll_directory(_home)")
    A("    os.environ['PATH'] = _home + os.pathsep + os.environ.get('PATH', '')")
    A("else:")
    A("    sys.exit('openEMS runtime not found at %s - set OPENEMS_HOME or run '")
    A("             '\"pixi run setup-em\"' % _home)")
    A("")
    A("import numpy as np")
    A("from CSXCAD import ContinuousStructure")
    A("from openEMS import openEMS")
    A("")
    A("unit = 1e-6                      # everything below is in micrometres")
    A("pad_w   = %s" % _fmt(m.pad_w_um))
    A("pad_l   = %s" % _fmt(m.pad_l_um))
    A("er      = %s" % _fmt(m.er))
    A("tand    = %s" % _fmt(m.tand))
    A("f_max   = %s" % _fmt(m.f_max_hz))
    A("f_read  = %s" % _fmt(m.extract_f_hz()))
    A("lateral = %s" % _fmt(lateral))
    A("air     = %s" % _fmt(air))
    A("res     = %s" % _fmt(res))
    A("planes  = %s" % json.dumps([asdict(p) for p in m.planes]))
    A("port_plane = %d" % m.port_plane)
    A("deepest = %s" % _fmt(deepest))
    # openEMS v0.0.36 asserts os.getcwd() == os.path.realpath(sim_path), and on
    # Windows getcwd keeps the 8.3 short form ("JAMESC~1") that realpath expands.
    # Resolving it here makes the two agree; without this Run() dies on an
    # assertion with no message.
    A("sim_path = os.path.realpath(%s)" % (repr(sim_dir) if sim_dir else
                                           "os.path.join(os.path.dirname(__file__), 'run')"))
    A("")
    A("FDTD = openEMS(EndCriteria=%s)" % _fmt(m.end_criteria))
    A("FDTD.SetGaussExcite(f_max / 2, f_max / 2)")
    A("# absorbing on all six faces: this is a local structure, not a resonator")
    A("FDTD.SetBoundaryCond(['MUR'] * 6)")
    A("")
    A("CSX = ContinuousStructure()")
    A("FDTD.SetCSX(CSX)")
    A("mesh = CSX.GetGrid()")
    A("mesh.SetDeltaUnit(unit)")
    A("")
    A("# --- mesh -------------------------------------------------------------")
    A("# Graded on purpose: the fine cell only spans the pad and the couple of")
    A("# dielectric heights around it where the fringing field lives, then")
    A("# SmoothMeshLines grades out to the coarse cell at the walls. Applying the")
    A("# fine cell across the whole domain is how this model first came to want")
    A("# 859 million cells instead of one.")
    A("coarse = max(res, %s)" % _fmt(m.wavelength_resolution_um() / 4))
    A("third = np.array([2.0 / 3.0, -1.0 / 3.0]) * (res / 2)")
    A("")
    A("for ax, half in (('x', pad_w / 2), ('y', pad_l / 2)):")
    A("    # thirds rule at the pad edge: a line just inside, two thirds outside")
    A("    mesh.AddLine(ax, [half + third[0], half + third[1],")
    A("                      -half - third[0], -half - third[1]])")
    A("    # a uniform fine band over the pad and its near field")
    A("    fine = half + 2 * deepest")
    A("    n = int(np.ceil(2 * fine / res)) + 1")
    A("    mesh.AddLine(ax, np.linspace(-fine, fine, n))")
    A("    mesh.AddLine(ax, [-lateral, lateral])")
    A("")
    A("# a void rim is a metal edge too, so it gets the thirds treatment")
    A("for p in planes:")
    A("    if p['void_d_um'] > 0:")
    A("        r = p['void_d_um'] / 2.0")
    A("        for ax in ('x', 'y'):")
    A("            mesh.AddLine(ax, [r + third[0], r + third[1],")
    A("                              -r - third[0], -r - third[1]])")
    A("")
    A("# z: enough lines across every dielectric gap to resolve the near field,")
    A("# then graded up through the air above")
    A("z_lines = [0.0]")
    A("prev = 0.0")
    A("for p in sorted(planes, key=lambda q: q['depth_um']):")
    A("    z = -p['depth_um']")
    A("    z_lines += list(np.linspace(prev, z, max(9, int(abs(z - prev) / res) + 1)))")
    A("    prev = z")
    A("z_lines += [-deepest - 2 * res, air]")
    A("mesh.AddLine('z', z_lines)")
    A("")
    A("for ax in ('x', 'y', 'z'):")
    A("    mesh.SmoothMeshLines(ax, coarse, 1.4)")
    A("")
    A("# --- materials --------------------------------------------------------")
    A("# loss tangent as a conductivity at the read frequency")
    A("kappa = 2 * np.pi * f_read * 8.8541878128e-12 * er * tand")
    A("sub = CSX.AddMaterial('substrate', epsilon=er, kappa=kappa)")
    A("sub.AddBox([-lateral, -lateral, -deepest - 4 * res], [lateral, lateral, 0], priority=1)")
    A("pec = CSX.AddMetal('pec')")
    A("")
    A("# the pad, sitting on the substrate surface")
    A("pec.AddBox([-pad_w / 2, -pad_l / 2, 0], [pad_w / 2, pad_l / 2, 0], priority=10)")
    A("")
    A("# planes, each optionally voided under the pad. CSXCAD resolves overlap by")
    A("# priority, so a substrate cylinder at a higher priority cuts the hole.")
    A("for i, p in enumerate(planes):")
    A("    z = -p['depth_um']")
    A("    pec.AddBox([-lateral, -lateral, z], [lateral, lateral, z], priority=10)")
    A("    if p['void_d_um'] > 0:")
    A("        cut = CSX.AddMaterial('void_%d' % i, epsilon=er, kappa=kappa)")
    A("        cut.AddCylinder([0, 0, z - res / 8], [0, 0, z + res / 8],")
    A("                        p['void_d_um'] / 2.0, priority=20)")
    A("")
    A("# --- port -------------------------------------------------------------")
    A("# Driven in z from the pad down to the plane being measured. A lumped port")
    A("# spanning the dielectric is the standard way to see the structure's Z11.")
    A("z_port = -planes[port_plane]['depth_um']")
    A("port = FDTD.AddLumpedPort(1, 50, [-pad_w / 2, -pad_l / 2, z_port],")
    A("                          [pad_w / 2, pad_l / 2, 0], 'z', excite=1, priority=5)")
    A("")
    A('if __name__ == "__main__":')
    A("    FDTD.Run(sim_path, cleanup=True, verbose=0)")
    A("    f = np.linspace(f_read / 10, f_read * 10, 201)")
    A("    port.CalcPort(sim_path, f)")
    A("    Z = port.uf_tot / port.if_tot")
    A("    # C from the reactive part; flatness across the decade is the check")
    A("    C = -1.0 / (2 * np.pi * f * np.imag(Z))")
    A("    mid = len(f) // 2")
    A("    spread = float(np.nanmax(C) - np.nanmin(C)) / float(C[mid])")
    A("    out = {'C_pF': float(C[mid]) * 1e12,")
    A("           'f_read_Hz': float(f[mid]),")
    A("           'flatness': spread,")
    A("           'capacitive': bool(np.imag(Z[mid]) < 0)}")
    A("    print('RESULT ' + json.dumps(out))")
    return "\n".join(L) + "\n"
