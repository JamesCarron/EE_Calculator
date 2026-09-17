"""Verify Hammerstad-Jensen microstrip and Kirschning-Jansen dispersion.

Written 2026-09-10 after a review recommended retiring the IPC-2141 87-form in
favour of H-J, so that Zo, eps_eff, Tpd and per-unit-length L and C all come
from one model instead of two that disagree by ~8 %.

Checks are limit identities and bounds, not the formula against itself:
eps_eff must stay within [(eps_r+1)/2, eps_r) across the validity window and
rise monotonically with width, dispersion must vanish at DC and rise
monotonically with frequency, the thickness correction must lower Zo, and
sqrt(L/C) and sqrt(L*C) must recover Zo and Tpd exactly.
"""

import math

ETA0 = 376.730313
ok = True


def check(label, got, want, tol_pc, unit=""):
    global ok
    good = abs(got - want) <= abs(want) * tol_pc / 100
    ok = ok and good
    print(f"  {'ok  ' if good else 'FAIL'} {label}: {got:.6g}{unit} (ref {want:g}{unit})")


def hj_eeff(u, er):
    """Hammerstad-Jensen static effective permittivity. u = w/h."""
    a = (1 + math.log((u ** 4 + (u / 52) ** 2) / (u ** 4 + 0.432)) / 49
         + math.log1p((u / 18.1) ** 3) / 18.7)
    b = 0.564 * ((er - 0.9) / (er + 3)) ** 0.053
    return (er + 1) / 2 + (er - 1) / 2 * (1 + 10 / u) ** (-a * b)


def hj_z01(u):
    """Hammerstad-Jensen impedance of the same line in air."""
    f = 6 + (2 * math.pi - 6) * math.exp(-((30.666 / u) ** 0.7528))
    return ETA0 / (2 * math.pi) * math.log(f / u + math.sqrt(1 + (2 / u) ** 2))


def du_thickness(u, t_h):
    """Hammerstad thickness correction, returned as delta(w/h)."""
    if t_h <= 0:
        return 0.0
    return (t_h / math.pi) * (1 + math.log(2 / t_h))


def hj(w, h, er, t=0.0):
    u = w / h + du_thickness(w / h, t / h)
    ee = hj_eeff(u, er)
    return hj_z01(u) / math.sqrt(ee), ee, u


def kj_eeff(w, h, er, f_hz, t=0.0):
    """Kirschning-Jansen dispersion. h in mm, f in Hz."""
    u = w / h + du_thickness(w / h, t / h)
    ee0 = hj_eeff(u, er)
    fn = f_hz / 1e9 * h                      # GHz * mm
    if fn <= 0:
        return ee0
    p1 = (0.27488 + (0.6315 + 0.525 / (1 + 0.0157 * fn) ** 20) * u
          - 0.065683 * math.exp(-8.7513 * u))
    p2 = 0.33622 * (1 - math.exp(-0.03442 * er))
    p3 = 0.0363 * math.exp(-4.6 * u) * (1 - math.exp(-((fn / 38.7) ** 4.97)))
    p4 = 1 + 2.751 * (1 - math.exp(-((er / 15.916) ** 8)))
    p = p1 * p2 * ((0.1844 + p3 * p4) * fn) ** 1.5763
    return er - (er - ee0) / (1 + p)


print("=" * 68)
print("1. HAMMERSTAD-JENSEN vs the IPC-2141 87-form")
print("=" * 68)
er, w, h, t = 4.3, 0.30, 0.20, 0.035
ipc = 87 / math.sqrt(er + 1.41) * math.log(5.98 * h / (0.8 * w + t))
z_t0, ee_t0, _ = hj(w, h, er, 0.0)
z_t, ee_t, u_t = hj(w, h, er, t)
print(f"  IPC-2141 87-form                : {ipc:6.2f} ohm")
print(f"  H-J, zero thickness             : {z_t0:6.2f} ohm  (eps_eff {ee_t0:.4f})")
print(f"  H-J, 35 um copper               : {z_t:6.2f} ohm  (eps_eff {ee_t:.4f}, u_eff {u_t:.4f})")
print(f"  -> the ~8 % gap the review found is mostly the zero-thickness assumption;")
print(f"     with copper thickness included the two models agree to {abs(z_t/ipc-1)*100:.1f} %.")
assert z_t < z_t0, "thickness must lower Zo"
print("  ok   thickness correction lowers Zo, as it must")

print()
print("=" * 68)
print("2. eps_eff LIMIT IDENTITIES (these are what the tests should assert)")
print("=" * 68)
for u in (0.05, 0.5, 1.5, 10, 200):
    ee = hj_eeff(u, er)
    print(f"  w/h = {u:6.2f} -> eps_eff {ee:.4f}")
    assert 1 < ee < er, "eps_eff must lie strictly between 1 and eps_r"
# The narrow-trace asymptote is (er+1)/2, but H-J approaches it far too slowly
# to assert at any real width (w/h = 0.001 still gives 2.744 against 2.65), and
# below w/h ~ 1e-6 the log term in a(u) breaks down numerically and eps_eff
# explodes. So assert the BOUND, which holds everywhere physical, and guard the
# validity window rather than testing an unreachable limit.
HJ_U_MIN, HJ_U_MAX = 0.01, 100.0          # H-J's usual stated validity range
for u in (HJ_U_MIN, 0.05, 0.2, 1, 5, 50, HJ_U_MAX):
    assert (er + 1) / 2 <= hj_eeff(u, er) < er, f"bound violated at w/h={u}"
print(f"  ok   (er+1)/2 <= eps_eff < er across the whole validity window "
      f"{HJ_U_MIN}-{HJ_U_MAX}")
check("wide trace approaches er", hj_eeff(1000, er), er, 3.0)
blowup = hj_eeff(1e-12, er)
assert blowup > er, "expected the documented numerical breakdown below the window"
print(f"  ok   outside the window it misbehaves as expected (w/h=1e-12 gives "
      f"{blowup:.3g}) - the implementation must clamp and flag, not compute")
# monotonic in u
vals = [hj_eeff(u, er) for u in (0.1, 0.3, 1, 3, 10, 30)]
assert all(x < y for x, y in zip(vals, vals[1:])), "eps_eff must rise with width"
print("  ok   eps_eff rises monotonically with trace width")

print()
print("=" * 68)
print("3. KIRSCHNING-JANSEN DISPERSION")
print("=" * 68)
ee_dc = kj_eeff(w, h, er, 0.0, t)
check("f -> 0 reproduces the static value", ee_dc, ee_t, 0.001)
prev = ee_dc
for f in (1e8, 5e8, 1e9, 5e9, 10e9, 40e9):
    ee = kj_eeff(w, h, er, f, t)
    z = hj_z01(w / h + du_thickness(w / h, t / h)) / math.sqrt(ee)
    print(f"  {f/1e9:5.1f} GHz -> eps_eff {ee:.4f}, Zo {z:5.2f} ohm")
    assert ee >= prev - 1e-12, "dispersion must be monotonic in frequency"
    prev = ee
assert prev < er, "eps_eff must stay below er at every frequency"
print("  ok   dispersion is monotonic and stays below er")
print(f"  at 500 MHz the shift is {(kj_eeff(w,h,er,5e8,t)/ee_t-1)*100:.3f} % "
      f"- negligible, which is why a static model is fine below ~1 GHz on FR4")

print()
print("=" * 68)
print("4. PER-UNIT-LENGTH L AND C, now self-consistent")
print("=" * 68)
c0 = 299792458.0
tpd = math.sqrt(ee_t) / c0                     # s per metre
L = z_t * tpd
C = tpd / z_t
print(f"  Zo {z_t:.2f} ohm, eps_eff {ee_t:.4f}")
print(f"  Tpd {tpd*1e12:.2f} ps/m  ({tpd*1e12*0.0254:.2f} ps/in)")
print(f"  L   {L*1e9:.3f} nH/m   ({L*1e9*0.0254:.3f} nH/in)")
print(f"  C   {C*1e12:.3f} pF/m   ({C*1e12*0.0254:.3f} pF/in)")
check("Zo recovered from sqrt(L/C)", math.sqrt(L / C), z_t, 1e-6, " ohm")
check("Tpd recovered from sqrt(L*C)", math.sqrt(L * C) * 1e12, tpd * 1e12, 1e-6, " ps/m")
print("  -> L and C now agree with Zo and Tpd by construction; under the old")
print("     mixed models they would have been inconsistent by about 8 %.")

print()
print("=" * 68)
print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
print("=" * 68)
