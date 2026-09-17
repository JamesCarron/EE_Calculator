"""Verify every formula proposed for the EE Calculator additions.

Written 2026-09-10 while planning the Saturn-inspired feature additions. Each
block computes a validation vector by hand-checkable arithmetic and, where a
published reference value exists (AWG resistance, standard attenuator pads,
copper skin depth), asserts against it. The numbers printed here are the ones
quoted in Implementation_Plan.md, so this file is the plan's evidence.
"""

import math

RHO20 = 1.724e-8          # copper resistivity at 20 C, ohm-metre
ALPHA = 0.00393           # copper temperature coefficient, per K
MU0 = 4e-7 * math.pi
MIL = 0.0254              # mm per mil

ok = True


def check(label, got, want, tol_pc, unit=""):
    global ok
    good = abs(got - want) <= abs(want) * tol_pc / 100
    ok = ok and good
    flag = "ok  " if good else "FAIL"
    print(f"  {flag} {label}: {got:.6g}{unit} (ref {want:g}{unit})")


print("=" * 68)
print("1. JUNCTION TEMPERATURE")
print("=" * 68)
P, tjc, tcs, tsa, Ta, Tjmax = 5.0, 1.5, 0.5, 8.0, 25.0, 150.0
th = tjc + tcs + tsa
dT = P * th
Tj = Ta + dT
Tc = Tj - P * tjc
Ts = Ta + P * tsa
Pmax = (Tjmax - Ta) / th
tsa_req = (125 - Ta) / P - tjc - tcs
print(f"  theta_total = {th} C/W, rise = {dT} K")
check("Tj", Tj, 75, 1e-9, " C")
check("Tcase", Tc, 67.5, 1e-9, " C")
check("Tsink", Ts, 65, 1e-9, " C")
# consistency: Tj must also equal Tsink + P*(theta_jc+theta_cs)
check("Tj via sink path", Ts + P * (tjc + tcs), 75, 1e-9, " C")
check("headroom to Tjmax", Tjmax - Tj, 75, 1e-9, " K")
check("P max for Tjmax", Pmax, 12.5, 1e-9, " W")
check("theta_sa needed for Tj=125", tsa_req, 18, 1e-9, " C/W")

print()
print("=" * 68)
print("2. WIRE VOLTAGE DROP  (AWG card extension)")
print("=" * 68)


def awg_d_mm(n):
    return 0.127 * 92 ** ((36 - n) / 39)


for n, ref_r in ((18, 20.9e-3), (12, 5.21e-3), (10, 3.28e-3)):
    d = awg_d_mm(n)
    a = math.pi / 4 * d * d          # mm^2
    r_per_m = RHO20 / (a * 1e-6)
    check(f"AWG{n} diameter", d, {18: 1.024, 12: 2.053, 10: 2.588}[n], 0.3, " mm")
    check(f"AWG{n} ohms/m at 20C", r_per_m, ref_r, 2.0, " ohm/m")

# worked example: 12 AWG, 0.5 m run, round trip, 40 A
d = awg_d_mm(12)
a = math.pi / 4 * d * d
r_per_m = RHO20 / (a * 1e-6)
L, I, trips = 0.5, 40.0, 2
Rtot = r_per_m * L * trips
print(f"  12 AWG, {L} m run, round trip, {I} A:")
check("loop resistance", Rtot, 5.211e-3, 2.0, " ohm")
check("voltage drop", I * Rtot, 0.2084, 2.0, " V")
check("power lost", I * I * Rtot, 8.34, 2.0, " W")
# same at 85 C
r85 = r_per_m * (1 + ALPHA * (85 - 20))
check("ohms/m at 85C", r85, 6.542e-3, 2.0, " ohm/m")
print(f"  drop at 85 C = {I * r85 * L * trips:.4g} V "
      f"({(r85 / r_per_m - 1) * 100:.1f}% worse than at 20 C)")

print()
print("=" * 68)
print("3. C AND L SERIES / PARALLEL")
print("=" * 68)
vals = [10e3, 4.7e3, 1e3]
ser = sum(vals)
par = 1 / sum(1 / v for v in vals)
check("R series 10k+4k7+1k", ser, 15.7e3, 1e-9, " ohm")
check("R parallel", par, 761.66, 0.1, " ohm")
caps = [10e-9, 10e-9]
check("C parallel (adds)", sum(caps), 20e-9, 1e-9, " F")
check("C series (reciprocal)", 1 / sum(1 / c for c in caps), 5e-9, 1e-9, " F")
inds = [10e-6, 22e-6]
check("L series (adds)", sum(inds), 32e-6, 1e-9, " H")
check("L parallel", 1 / sum(1 / x for x in inds), 6.875e-6, 0.1, " H")
# per-element current/power with an applied voltage, series case
V = 12.0
Iser = V / ser
print(f"  series string at {V} V draws {Iser * 1e3:.4g} mA")
for v in vals:
    print(f"    {v:g} ohm -> {Iser * v:.4g} V, {Iser * Iser * v * 1e3:.4g} mW")
check("sum of element voltages", sum(Iser * v for v in vals), V, 1e-9, " V")

print()
print("=" * 68)
print("4. VIA: IMPEDANCE, RESONANCE, ASPECT RATIO")
print("=" * 68)
d_mm, tp_um, h_mm, er = 0.3, 25.0, 1.6, 4.3
pad_mm, anti_mm = 0.6, 1.0
tp = tp_um / 1000
A = math.pi * tp * (d_mm + tp)                 # mm^2 barrel cross-section
R = RHO20 * (h_mm / 1000) / (A * 1e-6)
L_nH = 5.08 * (h_mm / 25.4) * (math.log(4 * h_mm / d_mm) + 1)
C_pF = 1.41 * er * (h_mm / 25.4) * (pad_mm / 25.4) / ((anti_mm - pad_mm) / 25.4)
check("barrel area", A, 0.02553, 0.5, " mm2")
check("DC resistance", R * 1e3, 1.081, 1.0, " mohm")
check("inductance", L_nH, 1.299, 1.0, " nH")
check("capacitance", C_pF, 0.5734, 1.0, " pF")
Z = math.sqrt((L_nH * 1e-9) / (C_pF * 1e-12))
f_res = 1 / (2 * math.pi * math.sqrt(L_nH * 1e-9 * C_pF * 1e-12))
AR = h_mm / d_mm
check("via impedance sqrt(L/C)", Z, 47.6, 1.0, " ohm")
check("resonant frequency", f_res / 1e9, 5.83, 1.0, " GHz")
check("aspect ratio", AR, 5.333, 0.1, ":1")
theta = (h_mm / 1000) / (390 * A * 1e-6)
check("thermal resistance, 1 via", theta, 160.7, 1.0, " K/W")
check("thermal resistance, 10 vias", theta / 10, 16.07, 1.0, " K/W")
Ivia = 3.0
print(f"  at {Ivia} A: drop = {Ivia * R * 1e3:.4g} mV, "
      f"dissipation = {Ivia * Ivia * R * 1e3:.4g} mW")
# Saturn states via_zo = sqrt(via_l / (via_c * 0.001)) with L in nH, C in pF
check("Saturn's nH/pF form agrees",
      math.sqrt(L_nH / (C_pF * 0.001)), Z, 0.01, " ohm")

print()
print("=" * 68)
print("5. SKIN DEPTH AND CURRENT DENSITY")
print("=" * 68)
for f, ref in ((1e6, 66.1e-6), (10e6, 20.9e-6), (100e6, 6.61e-6)):
    delta = math.sqrt(RHO20 / (math.pi * f * MU0))
    check(f"skin depth at {f / 1e6:g} MHz", delta * 1e6, ref * 1e6, 2.0, " um")
t_cu = 35e-6
delta = math.sqrt(RHO20 / (math.pi * 1e6 * MU0))
check("depth as % of 1 oz copper", delta / t_cu * 100, 188.9, 1.0, " %")
w, t = 1.0e-3, 35e-6
check("current density, 3 A in 1 mm x 35 um",
      3.0 / (w * t) / 1e6, 85.71, 0.5, " A/mm2")

print()
print("=" * 68)
print("6. ETCH FACTOR (trapezoidal cross-section)")
print("=" * 68)
w_mm, t_mm = 1.0, 0.035
rect = w_mm * t_mm
ef11 = t_mm * (w_mm - t_mm)          # 1:1, each side etched by t
ef21 = t_mm * (w_mm - t_mm / 2)      # 2:1, each side etched by t/2
check("rectangular area", rect, 0.035, 1e-9, " mm2")
check("1:1 etch area", ef11, 0.033775, 0.01, " mm2")
check("2:1 etch area", ef21, 0.0343875, 0.01, " mm2")
print(f"  1:1 etch removes {(1 - ef11 / rect) * 100:.2f}% of the cross-section")
# effect on IPC-2221 ampacity, external, dT=10
k, dT_ = 0.048, 10.0
for label, area_mm2 in (("rect", rect), ("1:1 etch", ef11)):
    a_mil2 = area_mm2 / (MIL * MIL)
    i = k * dT_ ** 0.44 * a_mil2 ** 0.725
    print(f"  {label:9s}: {a_mil2:6.2f} mil2 -> {i:.4g} A")

print()
print("=" * 68)
print("7. IMPEDANCE STRUCTURES (IPC-2141)")
print("=" * 68)
er, t = 4.3, 0.035


def microstrip(w, h, er, t):
    return 87 / math.sqrt(er + 1.41) * math.log(5.98 * h / (0.8 * w + t))


def embedded_microstrip(w, h, er, t, b):
    """b = total dielectric thickness above the conductor."""
    er_eff = er * (1 - math.exp(-1.55 * b / h))
    return 87 / math.sqrt(er_eff + 1.41) * math.log(5.98 * h / (0.8 * w + t))


def stripline(w, b, er, t):
    return 60 / math.sqrt(er) * math.log(1.9 * b / (0.8 * w + t))


def asym_stripline(w, h, c, er, t):
    """h = distance to nearer plane, c = distance to farther plane."""
    z = 80 / math.sqrt(er) * math.log(1.9 * (2 * h + t) / (0.8 * w + t))
    return z * (1 - h / (4 * (h + c + t)))


def kk_ratio(k):
    """K(k)/K(k') by Hilberg's approximation; accurate to about 1e-5."""
    kp = math.sqrt(max(0.0, 1 - k * k))
    if k <= 1 / math.sqrt(2):
        return math.pi / math.log(2 * (1 + math.sqrt(kp)) / (1 - math.sqrt(kp)))
    return math.log(2 * (1 + math.sqrt(k)) / (1 - math.sqrt(k))) / math.pi


def cpw_grounded(w, s, h, er):
    """Coplanar waveguide over ground: w = track, s = gap, h = dielectric."""
    k = w / (w + 2 * s)
    k3 = math.tanh(math.pi * w / (4 * h)) / math.tanh(math.pi * (w + 2 * s) / (4 * h))
    r1, r3 = kk_ratio(k), kk_ratio(k3)
    er_eff = (1 + er * (r3 / r1)) / (1 + (r3 / r1))
    return 60 * math.pi / (math.sqrt(er_eff) * (r1 + r3)), er_eff


print(f"  microstrip  w=0.30 h=0.20 : {microstrip(0.30, 0.20, er, t):6.2f} ohm")
print(f"  microstrip  w=0.35 h=0.20 : {microstrip(0.35, 0.20, er, t):6.2f} ohm")
print(f"  embedded    w=0.30 h=0.20 b=0.30 : {embedded_microstrip(0.30, 0.20, er, t, 0.30):6.2f} ohm")
print(f"  stripline   w=0.20 b=1.00 : {stripline(0.20, 1.00, er, t):6.2f} ohm")
print(f"  asym strip  w=0.20 h=0.25 c=0.75 : {asym_stripline(0.20, 0.25, 0.75, er, t):6.2f} ohm")
z_cpw, ee_cpw = cpw_grounded(0.30, 0.20, 0.20, er)
print(f"  cpw+gnd     w=0.30 s=0.20 h=0.20 : {z_cpw:6.2f} ohm (er_eff {ee_cpw:.3f})")
# IPC-2141's embedded formula does NOT agree with its own surface formula at
# the common boundary b/h = 1 (58.39 vs 53.52 ohm here) and asymptotes to the
# surface value as b grows, so used raw it reports a buried trace as HIGHER
# impedance than a surface one, which is backwards. Apply it as a ratio
# against its own b/h = 1 case instead: the boundary is then exact and the
# covering effect carries the right sign and magnitude.
def covered_microstrip(w, h, er, t, b):
    """Solder-mask / prepreg covered microstrip, normalised to the bare case."""
    bare = embedded_microstrip(w, h, er, t, h)
    return microstrip(w, h, er, t) * embedded_microstrip(w, h, er, t, b) / bare

z_bare = microstrip(0.30, 0.20, er, t)
z_mask = covered_microstrip(0.30, 0.20, er, t, 0.20 + 0.025)   # 25 um mask
z_deep = covered_microstrip(0.30, 0.20, er, t, 0.30)
check("covered at b=h reproduces bare exactly",
      covered_microstrip(0.30, 0.20, er, t, 0.20), z_bare, 1e-9, " ohm")
print(f"  bare {z_bare:.2f} -> 25 um mask {z_mask:.2f} "
      f"(drop {z_bare - z_mask:.2f} ohm), 0.1 mm cover {z_deep:.2f}")
assert z_mask < z_bare and z_deep < z_mask
print("  ok   covering lowers Zo, by a few ohms, as fabs report")
# sanity: Hilberg ratio is self-consistent, K(k)/K(k') * K(k')/K(k) == 1
kt = 0.6
assert abs(kk_ratio(kt) * kk_ratio(math.sqrt(1 - kt * kt)) - 1) < 1e-4
print("  ok   Hilberg elliptic ratio is self-consistent")

print()
print("=" * 68)
print("8. ATTENUATOR PADS  (planned, not yet selected)")
print("=" * 68)
for A_db in (3.0, 6.0, 10.0, 20.0):
    Z0 = 50.0
    K = 10 ** (A_db / 20)
    pi_sh = Z0 * (K + 1) / (K - 1)
    pi_se = Z0 * (K * K - 1) / (2 * K)
    t_se = Z0 * (K - 1) / (K + 1)
    t_sh = Z0 * 2 * K / (K * K - 1)
    print(f"  {A_db:4.1f} dB in 50 ohm: PI shunt {pi_sh:7.2f}, series {pi_se:6.2f} | "
          f"T series {t_se:6.2f}, shunt {t_sh:7.2f}")
# published 6 dB 50 ohm values
K = 10 ** (6 / 20)
check("6 dB PI shunt", 50 * (K + 1) / (K - 1), 150.5, 0.5, " ohm")
check("6 dB PI series", 50 * (K * K - 1) / (2 * K), 37.35, 0.5, " ohm")
check("6 dB T series", 50 * (K - 1) / (K + 1), 16.61, 0.5, " ohm")
check("6 dB T shunt", 50 * 2 * K / (K * K - 1), 66.93, 0.5, " ohm")

print()
print("=" * 68)
print("9. PLANE CAPACITANCE AND PDN TARGET")
print("=" * 68)
EPS0 = 8.854e-12
area_mm2, sep_mm, er_pdn = 100 * 100, 0.1, 4.3
C = EPS0 * er_pdn * (area_mm2 * 1e-6) / (sep_mm * 1e-3)
check("100x100 mm planes, 0.1 mm apart", C * 1e9, 3.807, 1.0, " nF")
Xc = 1 / (2 * math.pi * 1e6 * C)
check("Xc at 1 MHz", Xc, 41.80, 1.0, " ohm")
Vrail, Imax, transient_pc, ripple_pc = 1.2, 20.0, 50.0, 2.0
Ztarget = (Vrail * ripple_pc / 100) / (Imax * transient_pc / 100)
check("PDN target impedance", Ztarget * 1e3, 2.4, 1e-6, " mohm")

print()
print("=" * 68)
print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
print("=" * 68)
