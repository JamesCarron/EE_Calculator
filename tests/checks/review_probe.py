"""Numerical probes for the critical review of EE_Calculator/Implementation_Plan.md.

Written 2026-09-10 (EE_Calculator review). Checks four things the plan asserts
or relies on: (1) Hilberg's K/K' approximation against a real AGM elliptic
integral, (2) whether the 'ratio construction' for covered microstrip depends on
trace geometry at all, (3) what the embedded-microstrip formula gives with the
60/sqrt(er') coefficient IPC-2141 actually uses, (4) whether the IPC asymmetric
stripline formula reduces to the symmetric one at h = c. Stdlib only.
"""
import math

def K_agm(k):
    a, b = 1.0, math.sqrt(1 - k*k)
    for _ in range(60):
        a, b = (a+b)/2, math.sqrt(a*b)
    return math.pi/(2*a)

def kk_hilberg(k):
    kp = math.sqrt(max(0.0, 1-k*k))
    if k <= 1/math.sqrt(2):
        return math.pi/math.log(2*(1+math.sqrt(kp))/(1-math.sqrt(kp)))
    return math.log(2*(1+math.sqrt(k))/(1-math.sqrt(k)))/math.pi

print("1. Hilberg vs AGM  (rel err)")
worst = 0
for k in [0.01, 0.1, 0.3, 0.5, 0.7, 0.7071, 0.7072, 0.9, 0.99, 0.9999]:
    kp = math.sqrt(1-k*k)
    exact = K_agm(k)/K_agm(kp)
    h = kk_hilberg(k)
    e = abs(h/exact-1); worst = max(worst, e)
    print(f"   k={k:<7} exact {exact:.7f} hilberg {h:.7f} rel {e:.2e}")
print(f"   worst rel err {worst:.2e}")
# the plan's 'self-consistency' test is tautological: the two branches are
# reciprocals with k<->k' by construction, so r(k)*r(k')==1 tests nothing.
print(f"   tautology check r(0.6)*r(0.8) = {kk_hilberg(0.6)*kk_hilberg(0.8):.9f}")

er, t = 4.3, 0.035
def ms(w,h): return 87/math.sqrt(er+1.41)*math.log(5.98*h/(0.8*w+t))
def emb87(w,h,b):
    e = er*(1-math.exp(-1.55*b/h)); return 87/math.sqrt(e+1.41)*math.log(5.98*h/(0.8*w+t))
def emb60(w,h,b):
    e = er*(1-math.exp(-1.55*b/h)); return 60/math.sqrt(e)*math.log(5.98*h/(0.8*w+t))

print("\n2. Ratio construction: % drop vs w/h for 25um mask on h=0.2 and for b->inf")
for w in (0.02, 0.1, 0.3, 0.4):
    z = ms(w,0.2)
    r_mask = emb87(w,0.2,0.225)/emb87(w,0.2,0.2)
    r_inf  = emb87(w,0.2,50)/emb87(w,0.2,0.2)
    print(f"   w/h={w/0.2:<4} bare {z:6.2f}  mask ratio {r_mask:.5f} ({(1-r_mask)*100:.2f}% drop)  buried ratio {r_inf:.5f} ({(1-r_inf)*100:.2f}% drop)")
print("   -> the ratio is exactly sqrt((er'(h)+1.41)/(er'(b)+1.41)); w and t cancel.")
# physics check: Hammerstad eeff bare vs full embed (eeff -> er)
w,h=0.3,0.2
eeff = (er+1)/2+(er-1)/2/math.sqrt(1+12*h/w)
print(f"   Hammerstad eeff bare {eeff:.3f}; buried limit sqrt(eeff/er) = {math.sqrt(eeff/er):.4f} ({(1-math.sqrt(eeff/er))*100:.1f}% drop expected physically)")

print("\n3. Embedded microstrip with IPC's 60/sqrt(er') coefficient, w=0.3 h=0.2")
print(f"   surface 87-form            {ms(0.3,0.2):.2f}")
print(f"   emb 87-form (plan) b=h     {emb87(0.3,0.2,0.2):.2f}   b=inf {emb87(0.3,0.2,50):.2f}")
print(f"   emb 60-form (IPC)  b=h     {emb60(0.3,0.2,0.2):.2f}   b=1.125h {emb60(0.3,0.2,0.225):.2f}   b=inf {emb60(0.3,0.2,50):.2f}")
print(f"   60-form ratio-normalised: 25um mask {ms(0.3,0.2)*emb60(0.3,0.2,0.225)/emb60(0.3,0.2,0.2):.2f}, buried {ms(0.3,0.2)*emb60(0.3,0.2,50)/emb60(0.3,0.2,0.2):.2f}")

print("\n4. Asymmetric stripline at its symmetric limit (h=c) vs symmetric formula")
def sl(w,b): return 60/math.sqrt(er)*math.log(1.9*b/(0.8*w+t))
def asl(w,h,c): return 80/math.sqrt(er)*math.log(1.9*(2*h+t)/(0.8*w+t))*(1-h/(4*(h+c+t)))
w=0.2; b=1.0; hc=(b-t)/2
print(f"   symmetric formula, b=1.0:          {sl(w,b):.2f}")
print(f"   asym formula with h=c={hc:.4f}:     {asl(w,hc,hc):.2f}  ({(asl(w,hc,hc)/sl(w,b)-1)*100:+.1f}%)")
print(f"   asym plan vector h=.25 c=.75:      {asl(w,0.25,0.75):.2f}")
print(f"   asym h=0.45 c=0.55 (nearly centred): {asl(w,0.45,0.55):.2f}  -> exceeds symmetric 65.87 while claiming to be 'below'")
# where does asym drop below the symmetric value?
for hh in (0.10,0.20,0.25,0.30,0.35,0.40):
    print(f"      h={hh:.2f} c={b-t-hh:.3f}: {asl(w,hh,b-t-hh):.2f}")

print("\n5. R parallel 10k||4k7||1k exact:", 1/(1/10e3+1/4.7e3+1/1e3))

print("\n6. CPWG limits: h->inf should give plain CPW  (Z=30pi/(sqrt(eeff) r1), eeff=(er+1)/2)")
def cpwg(w,s,h):
    k=w/(w+2*s); k3=math.tanh(math.pi*w/(4*h))/math.tanh(math.pi*(w+2*s)/(4*h))
    r1,r3=kk_hilberg(k),kk_hilberg(k3); ee=(1+er*r3/r1)/(1+r3/r1)
    return 60*math.pi/(math.sqrt(ee)*(r1+r3)), ee
for h in (0.2, 1, 10, 1000):
    z,ee=cpwg(0.3,0.2,h); print(f"   h={h:<5} Z {z:6.2f} eeff {ee:.3f}")
k=0.3/0.7; print(f"   plain CPW: Z {30*math.pi/(math.sqrt((er+1)/2)*kk_hilberg(k)):.2f} eeff {(er+1)/2:.3f}")
# thin dielectric: h << s -> microstrip-like; compare to IPC microstrip of same w/h
z,ee=cpwg(0.3,5.0,0.2); print(f"   s=5mm (gaps far away) h=0.2: Z {z:.2f} eeff {ee:.3f}  vs IPC microstrip {ms(0.3,0.2):.2f} / Hammerstad-Z0 approx")
