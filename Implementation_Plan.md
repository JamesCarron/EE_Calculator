# EE Calculator — implementation plan for the Saturn-inspired additions

Written 2026-09-10. Everything here is specified to the point where implementation is mechanical: formulas with symbols and units, field ids, guard conditions, result rows, and a validation vector for every calculation. No code in `build_page.py` has been changed yet.

Every number quoted below was computed and checked by `C:\Auterion\Tools\claude\scratch\eecalc_formula_check.py`, which asserts against published reference values where they exist (AWG resistance per metre, copper skin depth, standard 50 Ω attenuator pads). That script is the evidence for this plan and should be re-run if any constant changes.

## How the Saturn inventory was corrected

The first inventory came from the marketing page and was thin. This revision is built from three sources that agree with each other: the 47-page help PDF shipped with the local V8.47 install, the tab captions and UI label strings recovered from the executable, and a screenshot of the running application.

Two attempts to interrogate the running program failed and are recorded so nobody repeats them: the app exposes **nothing** through UI Automation (`TAB COUNT: 0`), and `EnumChildWindows` reports **zero child windows**. It is a single custom-painted VCL window, so its controls are not addressable by either mechanism. Mining the binary's label strings is the method that works; `C:\Auterion\Tools\claude\scratch\saturn_win32_dump.py` and `saturn_ui_dump.ps1` are kept only as a record of the dead ends.

What the corrected pass added over the first inventory: the **Conductor Impedance** tab covers six structures, not two (microstrip, embedded microstrip, symmetric / asymmetric / dual stripline, coplanar); there is a persistent global **Options** panel (base copper weight in nine steps from 0.25 oz to 5 oz, plating thickness separately, plane thickness, units, substrate library, temp rise, ambient) that applies across tabs; there are **skin depth**, **skin depth percentage**, **current density**, **loaded conductor temperature**, **insertion loss** and **melting temperature** outputs; the series/parallel calculators report **per-element current and power**; the LED calculator **solves in both directions**; and there are cross-tab **"Send to Via Calculator" / "Send to Wavelength Calculator"** actions. The substrate library holds roughly 25 named laminates, each carrying Er and Tg.

## Scope

Confirmed by the owner: junction temperature, wire voltage drop, C and L series/parallel, and the via extras. Group B below is specified to the same depth but awaits a go-ahead, since the owner asked for the fuller picture before choosing.

---

# Group A — confirmed

## A1. Junction temperature

New sub-tab **Thermal** under a new top-level **Thermal** tab, or as a second card on the PCB tab. Recommendation: its own top-level tab, because nothing thermal exists yet and the PCB tab is already four cards deep.

**Fields** (`th-` prefix): `th-p` device power (W) · `th-ta` ambient (°C, default 25) · `th-jc` θ(junction–case) · `th-cs` θ(case–sink, interface) · `th-sa` θ(sink–ambient) · `th-ja` θ(junction–ambient, alternative to the three-part chain) · `th-tjmax` device rating (°C, optional).

**Model.** Series thermal resistances add, exactly like a resistor divider carrying power instead of current:

- θ_total = θ_jc + θ_cs + θ_sa, or θ_ja when the single-figure route is used. If both are supplied, prefer the chain and flag the conflict.
- ΔT = P · θ_total
- T_j = T_a + ΔT  → written into `th-tj` as a computed field
- T_case = T_j − P·θ_jc (only when θ_jc given)
- T_sink = T_a + P·θ_sa (only when θ_sa given)
- Headroom = T_j(max) − T_j, flagged red when negative
- P_max = (T_j(max) − T_a) / θ_total — the largest dissipation the design tolerates
- θ_sa required to hit a target T_j = (T_j(max) − T_a)/P − θ_jc − θ_cs — the heatsink selection answer

**Guards.** P ≥ 0; θ values ≥ 0; at least one θ present; θ_total > 0 before dividing; if θ_sa required comes out negative, say plainly that no heatsink can achieve the target and the package or ambient must change.

**Validation vector.** P = 5 W, θ_jc = 1.5, θ_cs = 0.5, θ_sa = 8, T_a = 25 °C, T_j(max) = 150 °C:

| Quantity | Value |
|---|---|
| θ_total | 10 °C/W |
| Rise | 50 K |
| T_j | 75 °C |
| T_case | 67.5 °C |
| T_sink | 65 °C |
| Headroom | 75 K |
| P_max | 12.5 W |
| θ_sa needed for T_j = 125 °C | 18 °C/W |

Cross-check that must hold in the tests: T_j computed down the sink path, T_sink + P·(θ_jc + θ_cs), equals 75 °C by the other route.

## A2. Wire voltage drop

Extends the existing AWG card in Utilities rather than adding a new one.

**New fields**: `awg-len` run length (m) · `awg-i` load current (A) · `awg-return` one-way / round-trip select (default round trip, because a drop that ignores the return conductor is wrong by exactly a factor of two) · `awg-temp` conductor temperature (°C, default 20) · `awg-vsupply` supply voltage (V, optional, for percentage drop).

**Model.** R per metre already comes from ρ/A. Then:

- R(T) = R₂₀ · (1 + α(T − 20)), α = 0.00393 /K for copper
- R_loop = R(T) · L · (1 for one-way, 2 for round trip)
- V_drop = I · R_loop
- P_loss = I² · R_loop
- % drop = V_drop / V_supply · 100 when a supply is given

**Validation vector.** 12 AWG, 0.5 m run, round trip, 40 A, 20 °C: loop 5.211 mΩ, drop 208.4 mV, loss 8.34 W. At 85 °C the same run is 6.542 mΩ/m, drop 261.7 mV — **25.5 % worse**, which is the number worth surfacing, since it is the difference between a harness that meets spec on the bench and one that does not in a hot airframe.

Reference values the tests assert against: AWG18 = 1.024 mm / 20.9 mΩ/m, AWG12 = 2.053 mm / 5.21 mΩ/m, AWG10 = 2.588 mm / 3.28 mΩ/m.

## A3. Capacitors and inductors in series/parallel

Extends the existing Series/Parallel card with a component-type select (`sp-type`: Resistor Ω / Capacitor F / Inductor H), plus an optional applied voltage `sp-v` for the resistor case.

**Model.** Resistors and inductors combine identically; capacitors are the mirror image:

| Type | Series | Parallel |
|---|---|---|
| Resistor, Inductor | Σxᵢ | 1 / Σ(1/xᵢ) |
| Capacitor | 1 / Σ(1/xᵢ) | Σxᵢ |

Result units follow the type (Ω / F / H). With an applied voltage on a resistor string, add per-element current and power: series current I = V/ΣR, each element sees I·Rᵢ and I²·Rᵢ; parallel elements each see V, drawing V/Rᵢ and V²/Rᵢ.

**Validation.** 10k + 4k7 + 1k → series 15.7 kΩ, parallel 761.75 Ω. Two 10 nF → series 5 nF, parallel 20 nF. 10 µH + 22 µH → series 32 µH, parallel 6.875 µH. At 12 V the series resistor string draws 764.3 µA and the element voltages sum back to exactly 12 V — that summation is the invariant worth asserting.

## A4. Via impedance, resonance, aspect ratio

Extends the existing Via card. L and C are already computed, so most of this is arithmetic on values in hand.

**New fields**: `via-i` current through the via (A, optional) · `via-n` via count (default 1) · `via-arlimit` aspect-ratio limit (default 10 for through vias; 1 is the usual microvia limit).

**Model.**

- Characteristic impedance Z = √(L/C) in SI. Saturn writes this as √(L_nH / (C_pF · 0.001)); the two agree exactly, which is a useful cross-check to keep in the tests.
- Self-resonant frequency f = 1 / (2π√(LC)) — above this the via stops behaving as a via.
- Aspect ratio = via height / drill diameter, flagged when it exceeds the limit. This is a fabrication constraint, not physics, and catching it early is worth more than the arithmetic suggests.
- With N vias in parallel: θ per via = θ_single / N, and R = R_single / N.
- With a current: V_drop = I·R, P = I²·R.

**Validation vector.** 0.3 mm drill, 25 µm plating, 1.6 mm board, pad 0.6 mm, antipad 1.0 mm, εr 4.3 — all of which reproduce the already-verified L and C:

| Quantity | Value |
|---|---|
| Barrel cross-section | 0.02553 mm² |
| DC resistance | 1.081 mΩ |
| Inductance | 1.299 nH |
| Capacitance | 0.5734 pF |
| **Impedance √(L/C)** | **47.6 Ω** |
| **Resonant frequency** | **5.83 GHz** |
| **Aspect ratio** | **5.33 : 1** (passes a 10:1 limit) |
| Thermal resistance, 1 via | 160.7 K/W |
| Thermal resistance, 10 vias | 16.07 K/W |
| At 3 A | 3.24 mV drop, 9.73 mW |

---

# Group B — specified, awaiting go-ahead

## B1. Substrate library

A laminate select feeding Er into Impedance, Wavelength and the via capacitance, and Tg into a new over-temperature warning on the trace card. Both values stay editable after selection, exactly as Saturn does it, because Er varies with frequency, glass style and resin content and the datasheet always wins.

Typical values, to be marked in the UI as nominal rather than authoritative:

| Laminate | Er (≈1 MHz–1 GHz) | Tg (°C) |
|---|---|---|
| FR-4 standard | 4.6 | 130 |
| FR-4 high-Tg | 4.4 | 170 |
| Isola 370HR | 4.04 | 180 |
| Megtron 6 | 3.4 | 185 |
| Rogers RO4003C | 3.38 | >280 |
| Rogers RO4350B | 3.48 | >280 |
| Rogers RO3003 | 3.00 | >280 |
| Rogers RO3010 | 10.2 | >280 |
| Polyimide | 4.3 | 250 |
| PTFE / Teflon | 2.1 | — |

The Tg warning fires when ambient + temperature rise exceeds Tg on the trace card, which is a genuine design error the tool currently lets through silently.

## B2. Additional impedance structures

**Recommended to add**: asymmetric (offset) stripline and grounded coplanar waveguide. **Recommended to add with a caveat**: covered microstrip. **Recommended to skip**: dual stripline, as the niche case.

- *Asymmetric stripline*, h to the nearer plane and c to the farther: Z₀ = [80/√εr · ln(1.9(2h+t)/(0.8w+t))] · [1 − h/(4(h+c+t))]. Check: w = 0.2, h = 0.25, c = 0.75, εr 4.3 gives **59.85 Ω**, correctly below the 65.87 Ω of the same trace centred in a 1.0 mm cavity, since moving toward a plane raises capacitance.
- *Grounded coplanar waveguide*, track w, gap s, dielectric h: with k = w/(w+2s) and k₃ = tanh(πw/4h)/tanh(π(w+2s)/4h), and r = K(k)/K(k′) by Hilberg's approximation, ε_eff = (1 + εr·r₃/r₁)/(1 + r₃/r₁) and Z₀ = 60π/(√ε_eff·(r₁ + r₃)). Check: w = 0.3, s = 0.2, h = 0.2, εr 4.3 gives **55.95 Ω** at ε_eff 3.066. Hilberg is accurate to about 1e-5 and needs no elliptic-integral library; the tests assert the self-consistency K(k)/K(k′) · K(k′)/K(k) = 1.

**A defect found while checking, which must not be implemented naively.** IPC-2141's embedded-microstrip formula, ε′r = εr[1 − e^(−1.55b/h)] substituted into the microstrip expression, does **not** agree with IPC's own surface-microstrip formula at their shared boundary b/h = 1 — it gives 58.39 Ω against 53.52 Ω for the same geometry — and it asymptotes *to* the surface value as the covering grows. Taken at face value it therefore reports a buried trace as **higher** impedance than a surface one, which is backwards.

The fix, and it should be labelled in the page as our construction rather than IPC's: apply it as a ratio against its own b/h = 1 case, Z_covered = Z_surface · Z_embedded(b) / Z_embedded(h). The boundary is then exact by construction and the covering carries the right sign and a credible magnitude — a 25 µm solder mask on the 53.52 Ω line gives **52.64 Ω**, a 0.9 Ω drop, and 0.1 mm of cover gives 50.97 Ω. Both sit in the 1–3 Ω band fabricators quote for mask on a 50 Ω microstrip.

## B3. Skin depth and current density

- δ = √(ρ / (π f μ₀)) for copper (μr = 1). Checks: **66.1 µm at 1 MHz**, 20.9 µm at 10 MHz, 6.61 µm at 100 MHz, all matching published copper figures.
- Skin depth as a percentage of copper thickness: at 1 MHz, δ is 188.8 % of 1 oz copper, i.e. the whole thickness still conducts. The percentage is more useful than the raw depth because it answers the actual question — whether the trace thickness is being wasted.
- Current density J = I/A: 3 A in 1 mm × 35 µm is **85.7 A/mm²**.

## B4. Copper weight, plating and etch factor on the trace card

Today copper weight is one dropdown and the cross-section is assumed rectangular. Saturn models base copper and plating separately (plating applies to external layers only; internal layers are unplated) and offers an etch factor for the trapezoidal reality of a subtractively etched conductor.

- Total copper = base + plating (external only)
- Cross-section, where T is total copper thickness and w the nominal width: none → w·T; 1:1 → T·(w − T); 2:1 → T·(w − T/2)
- Check on 1 mm of 1 oz copper: rectangular 0.035 mm², 1:1 etch 0.033775 mm² — the etch removes **3.50 %** of the section and drops IPC-2221 ampacity from 2.392 A to 2.331 A at ΔT = 10 °C. Small for 1 oz, and the reason to implement it is that it grows with copper weight, precisely where high-current designs live.

**Risk to manage.** This touches trace maths currently verified against reference values. The existing rectangular results must remain reachable and unchanged when etch factor is "none", and the current test vectors must keep passing untouched.

## B5. Plane capacitance and PDN target impedance

- Parallel-plate: C = ε₀·εr·A/d. Check: 100 × 100 mm planes 0.1 mm apart in εr 4.3 give **3.807 nF**, with X_C = **41.80 Ω** at 1 MHz.
- Target impedance: Z_target = (V_rail · ripple%) / (I_max · transient%). Check: a 1.2 V rail, 20 A maximum, 50 % transient, 2 % ripple gives **2.4 mΩ**.

## B6. Attenuator pads

Not selected, specified because it is cheap and the formulas are exact. With K = 10^(A_dB/20) in a symmetric system of impedance Z₀:

- π pad: shunt legs Z₀(K+1)/(K−1), series leg Z₀(K²−1)/(2K)
- T pad: series legs Z₀(K−1)/(K+1), shunt leg 2KZ₀/(K²−1)

Checked against published 50 Ω tables at 6 dB: π gives 150.5 / 37.35 Ω, T gives 16.61 / 66.93 Ω. All four match to better than 0.5 %.

## B7. Cross-tab "send to" actions

Saturn passes values between tabs. The cheap, high-value version here: send ε_eff from Impedance into Wavelength, and send a solved trace width into the PCB current card. Low effort, and it removes the retyping that makes multi-step work tedious.

---

# Cross-cutting work

**Units.** Dimension fields already accept `mm`, `mil`, `um`, `in` per field, which is better than Saturn's global toggle because it removes the "which mode am I in" error entirely. Recommendation: keep per-field parsing and do **not** adopt a global units switch. A global *default* for new fields is the only part worth taking.

**Shared settings.** Copper weight, ambient and temperature rise are currently repeated per card. Consolidating them into a shared strip beside the E-series selector would match Saturn and remove duplication, but it is a refactor of working code with no new capability, so it should follow the feature work rather than precede it.

**Testing.** Each item above adds vectors to the node harness, which already models `value` and `classList` for real. The invariants worth asserting, beyond matching the numbers, are the ones that catch sign and unit errors: T_j agreeing down two different paths; series element voltages summing to the source; the two forms of via impedance agreeing; the Hilberg ratio being self-consistent; covered microstrip reproducing bare microstrip exactly at b = h; and rectangular cross-section results being unchanged when etch factor is off.

**Execution order.** A1 and A3 are independent and self-contained, so they go first. A2 and A4 extend existing cards and should follow, since they touch verified code. In Group B, B1 unlocks B2's realism and B4's Tg warning, so it leads; B4 goes last because it carries the regression risk.

## Estimated shape of the work

| Item | New fields | New results | Risk |
|---|---|---|---|
| A1 junction temperature | 7 | 7 | none, new card |
| A2 wire voltage drop | 5 | 4 | low, extends a card |
| A3 C/L series-parallel | 2 | 3 + per-element | low |
| A4 via extras | 3 | 6 | low, arithmetic on existing values |
| B1 substrate library | 1 select + 2 | — (feeds others) | low |
| B2 impedance structures | 3 | 3 | medium, formula validity |
| B3 skin depth | 1 | 3 | none |
| B4 copper/plating/etch | 3 | 2 | **medium, touches verified maths** |
| B5 plane C and PDN | 7 | 4 | none, new card |
| B6 attenuator pads | 3 | 4 | none |
