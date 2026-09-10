# EE Calculator — implementation plan for the Saturn-inspired additions

Written 2026-09-10. Everything here is specified to the point where implementation is mechanical: formulas with symbols and units, field ids, guard conditions, result rows, and a validation vector for every calculation. No code in `build_page.py` has been changed yet.

Every number quoted below was computed and checked by `C:\Auterion\Tools\claude\scratch\eecalc_formula_check.py`, which asserts against published reference values where they exist (AWG resistance per metre, copper skin depth, standard 50 Ω attenuator pads). That script is the evidence for this plan and should be re-run if any constant changes.

## How the Saturn inventory was corrected

The first inventory came from the marketing page and was thin. This revision is built from four sources that agree with each other: the 47-page help PDF shipped with the local V8.47 install, the tab captions and UI label strings recovered from the executable, and — most usefully — a screenshot of every one of the 19 tabs, read tab by tab in the appendix at the end of this document.

Two attempts to interrogate the running program failed and are recorded so nobody repeats them: the app exposes **nothing** through UI Automation (`TAB COUNT: 0`), and `EnumChildWindows` reports **zero child windows**. It is a single custom-painted VCL window, so its controls are not addressable by either mechanism. Mining the binary's label strings is the method that works; `C:\Auterion\Tools\claude\scratch\saturn_win32_dump.py` and `saturn_ui_dump.ps1` are kept only as a record of the dead ends.

What the corrected pass added over the first inventory: the **Conductor Impedance** tab covers six structures, not two (microstrip, embedded microstrip, symmetric / asymmetric / dual stripline, coplanar); there is a persistent global **Options** panel (base copper weight in nine steps from 0.25 oz to 5 oz, plating thickness separately, plane thickness, units, substrate library, temp rise, ambient) that applies across tabs; there are **skin depth**, **skin depth percentage**, **current density**, **loaded conductor temperature**, **insertion loss** and **melting temperature** outputs; the series/parallel calculators report **per-element current and power**; the LED calculator **solves in both directions**; and there are cross-tab **"Send to Via Calculator" / "Send to Wavelength Calculator"** actions. The substrate library holds roughly 25 named laminates, each carrying Er and Tg.

## Scope, settled

Decided by tab-by-tab interview on 2026-09-10. Fourteen of Saturn's nineteen tabs contribute something; five are excluded outright.

**In, and what each contributes**

| Saturn tab | What we take |
|---|---|
| Conductor Properties | Required vs achievable current shown together, skin depth and its percentage of copper thickness, current density, plane and parallel-conductor ampacity modifiers |
| Thermal Management | Junction temperature card, with a θ chain, Tj(max) headroom, maximum allowable power and required heatsink θ |
| Via Properties | Impedance √(L/C), self-resonant frequency, aspect-ratio check, via count, and drop and dissipation at a stated current |
| Ohm's Law | Capacitor and inductor series/parallel, per-element current and power, and PI/T/L-pad attenuators |
| Conductor Impedance | Covered/soldermask microstrip, grounded coplanar, asymmetric stripline, and per-unit-length L and C |
| Er Effective | Standalone card with frequency dependence, Hammerstad–Jensen |
| Wavelength Calculator | Divide-fraction slider from full to 1/20, and period as an alternative input |
| Mechanical Information | Wire voltage drop from run length, load current, round-trip and conductor temperature |
| Fusing Current | Adjustable Onderdonk multiplier and an explicit ">5 s is out of scope" warning |
| Conversion Calculator | Rectangular↔polar, degrees↔radians, and a dBm bench chain with volts into a stated impedance |
| PDN Calculator | Plane capacitance from area and separation, and PDN target impedance |
| PPM-XTAL | Actual minimum and maximum oscillation frequencies, not just the deviation |
| Min Conductor Spacing | Nothing — ours already covers all seven environments at once, which beats showing one at a time |
| XL-XC Reactance | Nothing — ours already matches, and SI-suffix parsing removes the need for unit radio buttons |

Two cross-cutting behaviours are also in: **validity windows printed on the face of each card** rather than only warning once breached, and a **shared settings strip** for copper weight, ambient and temperature rise instead of repeating them per card.

**Out, deliberately**

Bandwidth & Max Conductor Length as a dual-method presentation (we keep our knee frequency and critical length); Padstack Calculator; Differential Pairs / XTALK; Embedded Resistors; Planar Inductors; drill and screw-thread reference tables; via step response; the whole substrate-library and copper-modelling group (library, Tg warning, separate plating, etch factor); cross-tab send-to actions; print/export.

Excluding the substrate library has a consequence worth stating: Er stays a manually entered number on the impedance and wavelength cards. That is fine for the structures being added, but it means the Tg-exceeded warning cannot be built either, since it needs a laminate's Tg.

**One prerequisite.** The plane and parallel-conductor ampacity modifiers are IPC-2152 chart data. The decision was to use published open-literature fits and name the source on the card as an approximation. That is a research step before it is a coding step, and it may come back inconclusive — if no citable fit is found, the honest outcome is to report that and leave those two modifiers out rather than invent a curve.

## Grouping

Adding these calculators breaks the current tab structure in one specific way: **Series/Parallel stops being resistor-only** once capacitors and inductors join it, so it cannot stay under Resistors. That forces a rethink, and the rethink is worth doing properly rather than bolting new tabs on the end — six new calculators arriving as six new tabs would leave thirteen top-level tabs and no shape.

The organising idea is to group by the question being asked, not by the component involved, and to use the sub-tab pattern already proven on Resistors. Seven tabs, twenty-two cards, every tab holding two to four:

| Tab | Cards |
|---|---|
| **Fundamentals** | Ohm's Law & Power · Series / Parallel (R, C, L) |
| **Resistors** *(E-series selector lives here)* | Divider · LED Resistor · Attenuator Pads · Accuracy |
| **Filters & Resonance** | RC Filter · Reactance · Crystal Load Capacitance · Frequency Error |
| **PCB Copper** | Trace Current · Via · Fusing Current · Conductor Spacing |
| **PCB Signal** | Impedance · Er Effective · Wavelength & Critical Length |
| **Power & Thermal** | Junction Temperature · Plane Capacitance · PDN Target Impedance |
| **Utilities** | AWG Wire · Number Bases · Ratio Units · Conversions |

What moves and why:

- **Series/Parallel leaves Resistors for Fundamentals.** It now handles R, C and L, so filing it under Resistors would misdescribe it. Paired with Ohm's Law it makes a coherent "basic network arithmetic" tab, and it rescues Ohm's Law from being a one-card tab.
- **RC Filter, Reactance and Crystal merge into Filters & Resonance.** Three thin tabs become one four-card tab covering the same idea from different angles: how passives behave against frequency. Crystal load capacitance and ppm sit naturally beside LC resonance.
- **PCB splits into Copper and Signal.** These answer genuinely different questions — will the copper carry the current and fit the clearances, versus will the signal arrive intact — and the existing PCB tab was already four cards deep before adding anything. Via stays on the Copper side: power, thermal and stitching vias are its common use, and the new impedance and resonance figures ride along.
- **Impedance becomes PCB Signal** and gains the Er Effective card, which belongs beside the impedance maths that consumes ε_eff.
- **Power & Thermal is the one genuinely new tab.** Junction temperature and the PDN pair are both about getting power in and heat out, and neither justifies a tab alone.
- **The E-series selector stays with Resistors**, which still works: divider, LED and the new attenuator pads all want standard-value suggestions, and nothing that moved out needs it.

Net effect: eight tabs become seven while the tool gains roughly fifteen calculators.

## Build order

One batch, self-contained work first, anything touching verified code last.

1. **Regrouping** — move cards into the seven-tab structure with no behaviour change, and confirm the existing test suite still passes untouched. Doing this first means every later addition lands in its final home.
2. **New cards** — Junction Temperature, Plane Capacitance, PDN Target Impedance, Attenuator Pads, Er Effective. All new code, nothing to regress.
3. **Extensions to existing cards** — C and L in Series/Parallel, wire voltage drop, via extras, crystal min/max, Onderdonk multiplier, wavelength slider, the conversion additions.
4. **Impedance structures** — covered microstrip, coplanar, asymmetric stripline, per-unit-length L and C.
5. **Conductor Properties additions** — required vs achievable current, skin depth, current density. These touch the trace card, which carries verified reference values.
6. **Research, then build or abandon** — open-literature fits for the plane and parallel-conductor modifiers.
7. **Cross-cutting** — validity windows on each card, then the shared settings strip, which is a refactor and therefore last.

---

# Specifications

Every item below is specified to implementation depth. Each carries its final status from the interview; the excluded ones are kept because the reasoning is worth not relitigating, and because a later change of mind should not need the work redone.

## Status at a glance

**In:** A1 junction temperature · A2 wire voltage drop · A3 C and L series/parallel · A4 via extras · B2 impedance structures · B3 skin depth and current density · B5 plane capacitance and PDN · B6 attenuator pads · validity windows · shared settings strip · Er effective card · crystal min/max · Onderdonk multiplier · wavelength slider · conversion additions · plane/parallel modifiers *(pending a citable source)*

**Out:** B1 substrate library · B4 copper weight, plating and etch factor · B7 send-to actions · via step response · differential pairs · crosstalk · embedded resistors · planar inductors · padstack · dual-method bandwidth · drill and thread tables · print/export

---

# Confirmed items

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

# Remaining items, with their final status

## B1. Substrate library — **EXCLUDED**

> Not being built. Er stays a manually entered number, and the Tg-exceeded warning falls with it since it needs a laminate's Tg.

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

## B2. Additional impedance structures — **IN**

**Recommended to add**: asymmetric (offset) stripline and grounded coplanar waveguide. **Recommended to add with a caveat**: covered microstrip. **Recommended to skip**: dual stripline, as the niche case.

- *Asymmetric stripline*, h to the nearer plane and c to the farther: Z₀ = [80/√εr · ln(1.9(2h+t)/(0.8w+t))] · [1 − h/(4(h+c+t))]. Check: w = 0.2, h = 0.25, c = 0.75, εr 4.3 gives **59.85 Ω**, correctly below the 65.87 Ω of the same trace centred in a 1.0 mm cavity, since moving toward a plane raises capacitance.
- *Grounded coplanar waveguide*, track w, gap s, dielectric h: with k = w/(w+2s) and k₃ = tanh(πw/4h)/tanh(π(w+2s)/4h), and r = K(k)/K(k′) by Hilberg's approximation, ε_eff = (1 + εr·r₃/r₁)/(1 + r₃/r₁) and Z₀ = 60π/(√ε_eff·(r₁ + r₃)). Check: w = 0.3, s = 0.2, h = 0.2, εr 4.3 gives **55.95 Ω** at ε_eff 3.066. Hilberg is accurate to about 1e-5 and needs no elliptic-integral library; the tests assert the self-consistency K(k)/K(k′) · K(k′)/K(k) = 1.

**A defect found while checking, which must not be implemented naively.** IPC-2141's embedded-microstrip formula, ε′r = εr[1 − e^(−1.55b/h)] substituted into the microstrip expression, does **not** agree with IPC's own surface-microstrip formula at their shared boundary b/h = 1 — it gives 58.39 Ω against 53.52 Ω for the same geometry — and it asymptotes *to* the surface value as the covering grows. Taken at face value it therefore reports a buried trace as **higher** impedance than a surface one, which is backwards.

The fix, and it should be labelled in the page as our construction rather than IPC's: apply it as a ratio against its own b/h = 1 case, Z_covered = Z_surface · Z_embedded(b) / Z_embedded(h). The boundary is then exact by construction and the covering carries the right sign and a credible magnitude — a 25 µm solder mask on the 53.52 Ω line gives **52.64 Ω**, a 0.9 Ω drop, and 0.1 mm of cover gives 50.97 Ω. Both sit in the 1–3 Ω band fabricators quote for mask on a 50 Ω microstrip.

## B3. Skin depth and current density — **IN**

- δ = √(ρ / (π f μ₀)) for copper (μr = 1). Checks: **66.1 µm at 1 MHz**, 20.9 µm at 10 MHz, 6.61 µm at 100 MHz, all matching published copper figures.
- Skin depth as a percentage of copper thickness: at 1 MHz, δ is 188.8 % of 1 oz copper, i.e. the whole thickness still conducts. The percentage is more useful than the raw depth because it answers the actual question — whether the trace thickness is being wasted.
- Current density J = I/A: 3 A in 1 mm × 35 µm is **85.7 A/mm²**.

## B4. Copper weight, plating and etch factor — **EXCLUDED**

> Not being built. This was the only item that touched trace maths verified against reference values, so excluding it also removes the main regression risk from the batch.

Today copper weight is one dropdown and the cross-section is assumed rectangular. Saturn models base copper and plating separately (plating applies to external layers only; internal layers are unplated) and offers an etch factor for the trapezoidal reality of a subtractively etched conductor.

- Total copper = base + plating (external only)
- Cross-section, where T is total copper thickness and w the nominal width: none → w·T; 1:1 → T·(w − T); 2:1 → T·(w − T/2)
- Check on 1 mm of 1 oz copper: rectangular 0.035 mm², 1:1 etch 0.033775 mm² — the etch removes **3.50 %** of the section and drops IPC-2221 ampacity from 2.392 A to 2.331 A at ΔT = 10 °C. Small for 1 oz, and the reason to implement it is that it grows with copper weight, precisely where high-current designs live.

**Risk to manage.** This touches trace maths currently verified against reference values. The existing rectangular results must remain reachable and unchanged when etch factor is "none", and the current test vectors must keep passing untouched.

## B5. Plane capacitance and PDN target impedance — **IN**

- Parallel-plate: C = ε₀·εr·A/d. Check: 100 × 100 mm planes 0.1 mm apart in εr 4.3 give **3.807 nF**, with X_C = **41.80 Ω** at 1 MHz.
- Target impedance: Z_target = (V_rail · ripple%) / (I_max · transient%). Check: a 1.2 V rail, 20 A maximum, 50 % transient, 2 % ripple gives **2.4 mΩ**.

## B6. Attenuator pads — **IN**

Now selected. The formulas are exact. With K = 10^(A_dB/20) in a symmetric system of impedance Z₀:

- π pad: shunt legs Z₀(K+1)/(K−1), series leg Z₀(K²−1)/(2K)
- T pad: series legs Z₀(K−1)/(K+1), shunt leg 2KZ₀/(K²−1)

Checked against published 50 Ω tables at 6 dB: π gives 150.5 / 37.35 Ω, T gives 16.61 / 66.93 Ω. All four match to better than 0.5 %.

## B7. Cross-tab "send to" actions — **EXCLUDED**

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

---

# Appendix: the Saturn UI, tab by tab

Screenshots live in `SaturnPCB/`, one per tab, each named after the tab it shows. All 19 tabs are covered exactly once; the descriptions below were read off those captures. Values quoted are whatever the app happened to be showing, and are given because a worked example says more about a calculator than a field list does.

The right-hand **Options** panel persists across every tab and greys out whatever does not apply: base copper weight (0.25–5 oz), plating thickness (bare to 3 oz), plane thickness, conductor layer, imperial/metric units, a substrate dropdown with editable Er and Tg, temperature rise and ambient (each showing a live °F conversion), and an **Information** pane carrying derived values such as total copper thickness. Every tab has **Print** and **Solve!** buttons.

## Bandwidth_and_Max_Conductor_Length.png

How long a trace may be before it must be treated as a transmission line. Input is a signal risetime (1 ns) or a frequency. Two methods run side by side: the **IPC-2251** route gives bandwidth 350 MHz, propagation speed C/√Er = 139 778 954 m/s and a maximum length of 1.772 in via an "Sr divide by factor" slider defaulting to 0.25 Sr; the **frequency-domain** route gives full wavelength in air 33.72 in and a maximum length of 4.818 in via a lambda-divide slider defaulting to 1/7. The two answers differ by 2.7× on identical input, which is the honest reflection of how arbitrary the rule of thumb is. Microstrip/stripline selection affects only the IPC route. *We already have knee frequency and critical length; the pair-of-methods presentation is the borrowable idea.*

## Conductor_Impedance.png

Single-ended impedance for one trace. Inputs are width (17 mil), height above the plane (10 mil) and frequency (500 MHz); outputs are Zo 50.74 Ω, Lo 7.788 nH/in, Co 3.025 pF/in and Tpd 153.49 ps/in. The **Passive Circuits** selector offers six geometries — Microstrip, Microstrip Embed, Stripline, Stripline Asym, Dual Stripline, Coplanar Wave — and the cross-section graphic redraws for each. The Information pane surfaces Er Effective (3.2802) alongside total copper thickness. *This is the tab behind plan item B2: we have two of the six structures, and per-inch L and C are outputs we do not currently give.*

## Conductor_Properties.png

The flagship current-carrying calculator. Solve for amperage or for conductor width; options for parallel conductors and for a plane being present. Inputs shown: load current 5 A, width 50 mil, length 1000 mil, PCB thickness 62 mil, frequency 1 MHz with a DC checkbox. Outputs: skin depth 2.599 mil at 100 % of thickness, DC resistance 8.30 mΩ, cross-section 102.79 mil², conductor current 3.723 A, voltage drop 30.9 mV, loaded voltage drop 41.5 mV, power 115 mW and 20.61 dBm. The Information pane adds material Tg, loaded conductor temperature (142 °F), conductor temperature and current density J = 0.0362 A/mil². The mode line reads "IPC-2152 with modifiers" with an etch factor of 2:1.

Worth understanding before copying: **load current and conductor current are different things**. The 5 A input is what the design draws; the 3.723 A output is what the geometry can carry at the chosen temperature rise. Showing both together is what lets you see at a glance that this trace is undersized. *Plan items B3 and B4 come from this tab.*

## Conversion_Calculator.png

Six converters in one pane. Distance (10 mil → 0.01 in / 0.254 mm / 254 µm); temperature (72 °F → 22.22 °C); a **dB chain modelled on a bench setup** rather than a bare ratio — dBm in (−60) plus gain (23 dB) minus attenuator (10 dB) gives −47 dBm, with volts in/out and voltage gain 14.13; rectangular↔polar with a swap checkbox and a "Send →" button; degrees↔radians. The Information pane converts dBm to watts (19.95 nW). Shortcut buttons link to SI prefixes, an Ohm's law wheel, a resistor calculator, a dBm chart, a capacitor unit chart and PCB design rules. *We have distance, temperature and dB/ratio; rect↔polar and deg↔rad are plan items, and the bench-chain framing of dB is the better idea.*

## Differential_Pairs_XTALK.png

Differential impedance against a target, plus near-end crosstalk. Inputs: width 10 mil, spacing 5 mil, height 15 mil, applied voltage 1 V, coupled length 100 mil, risetime 1 ns, target Zdiff 100 Ω with a ±10 % tolerance slider, and a **protocol dropdown** (DDR2 CLK/DQS shown) that preloads the target. Six coupling geometries: edge-coupled external, internal symmetric, internal asymmetric, embedded, and broadside coupled shielded or unshielded. Outputs: Zdifferential 100.979 Ω with a **green in-tolerance indicator**, Zo 77.504 Ω, Zodd 50.490 Ω, Zeven 118.971 Ω; crosstalk gives Kb 0.2111 (−13.512 dB, 6.4 mV NEXT) terminated and Kb′ 0.4041 (−7.870 dB, 12.3 mV) unterminated, with Lsat 3289 mil. Formula restrictions are printed on the face of the tab: 0.1 < W/H < 3.0 and 0.1 < S/H < 3.0.

*We decided against differential impedance and crosstalk. Nothing here changes that — Saturn disowns its own separate crosstalk tab — but the presentation is the model to copy if we ever revisit: state the validity window on the page, and show a target with a coloured pass/fail band rather than a bare number.*

## Embedded_Resistors.png

Sizes a polymer-thick-film resistor buried in the stackup. Type selector: additive screened, subtractive copper-nickel, or embedded annular. Sheet resistance 25 Ω/sq with a 100 × 50 mil rectangle gives 5000 mil² and 50 Ω. References IPC-2316. *Confirmed niche; stays out of scope.*

## Er_Effective.png

Effective dielectric constant for a microstrip: width 17 mil, height 10 mil, 500 MHz → Er eff 3.2802. Explicitly states it uses the Hammerstad and Jensen formulation rather than the simplified IPC-2141A one, and offers **"Send to Wavelength Calculator"**. *We compute ε_eff inside the impedance tab but never expose it or its frequency dependence; the send-to button is plan item B7.*

## Fusing_Current.png

Onderdonk fusing current: 10 mil width for 1 s gives a 18.79 mil² section and 3.515 A, with the equation and the copper melting point (1084.62 °C) printed on the tab. Carries an etch-factor slider and an adjustable **Onderdonk multiplier**, and warns against use beyond about 5 seconds. *We have this. The multiplier and the explicit ">5 s is out of scope" warning are the refinements worth stealing.*

## Mechanical_Information.png

Three reference blocks. **Wire gauge**: AWG 4/0 gives 0.46 in diameter, 0.05 Ω per 1000 ft, 380 A chassis and 302.3 A power-transmission ampacity, and with load 5 A over a 10 ft run, a 2.5 mV drop. **Drill chart** and **imperial screw thread sizes** are scrollable read-only tables. *The wire voltage drop here is plan item A2. The drill and thread tables stay out — vendor data, better placed elsewhere.*

## Min_Conductor_Spacing.png

IPC-2221C clearance by voltage band and construction. Ten voltage bands from 0–15 V to >500 V (the last enabling a free-entry field) against eight device types, with the legend spelled out on the tab: B1 internal, B2/B3 external uncoated by altitude, B4 solder-mask covered, B5 external coated, A6–A8 component leads. 0–15 V on B1 gives 1.97 mil. *We have this with seven environments; Saturn lists eight, splitting the coated external case, and shows only the selected one rather than all at once. Showing all seven together, as we do, remains the better call for comparing options.*

## Ohms_Law.png

V/I/R/P with a solve-for selector — 1 A through 12 Ω gives 12 V and 12 W — sitting above a **nested strip of nine helper calculators**: LED bias, R series, R parallel, PI attenuator, T attenuator, C series, C parallel, L series, L parallel. LED bias is the visible one: 12 V supply, 2 V drop, 10 mA gives 1000 Ω dissipating 0.1 W, and a checkbox reverses it to solve for LED current. *Direct confirmation for plan items A3 (C and L series/parallel) and B6 (attenuator pads), and our LED calculator already solves both ways.*

## Padstack_Calculator.png

Seven pad geometry modes: thru-hole pad, BGA land size, conductor/pad TH, conductor/pad BGA, two conductors for each, and corner-to-corner. Thru-hole shown: 32 mil hole, 12 mil annular ring, 12 mil isolation, plated, giving 56 mil external and internal signal pads, an 80 mil plane outer diameter, 56 mil inner and a 10 mil spoke width. *We excluded land-pattern work as Altium's job. The conductor/pad modes — will a track of this width pass between these pads — are the part that remains genuinely useful and is plan item B5's padstack option.*

## PDN_Calculator.png

Two blocks. **Target PDN impedance** from a 5 V rail, 5 % ripple, 2 A maximum and 50 % transient → 0.25 Ω. **Plane capacitance** from 5 in² of plane 2 mil apart at 1 MHz → 2587.5 pF and 61.51 Ω of reactance, with a DC checkbox. *Both are plan item B5, and the arithmetic is already verified against our own worked example.*

## Planar_Inductors.png

Spiral inductor in copper: 5 turns, 10 mil track and gap, 350 mil outer diameter, square geometry (also hexagonal, octagonal, circular) → 170 mil inner diameter, 0.3462 fill factor, 248.59 nH. Shows the modified-Wheeler expression on the tab. *Confirmed niche; stays out.*

## PPM_XTAL_Calculator.png

Three blocks: **XTAL capacitor value** (10 pF load, 3 pF stray, C1 = C2 = 14 pF → 10.00 pF seen by the crystal, with a 14 pF rule-of-thumb figure); **Hertz to PPM** (32000 → 32001 Hz = 31.25 ppm); **PPM to Hertz** (50 MHz at 25 ppm → ±1250 Hz, giving the min and max oscillation frequencies). *We match this closely already. The min/max frequency pair is a small addition worth making.*

## Thermal_Management.png

Two blocks. **Device junction temperature**: 3 °C/W and 5 W on a 22 °C ambient → 37 °C. **Heat sink selection**: 25 °C/W and 5 W → 147 °C, captioned as being based on a 75 °C rise in natural convection. *This is plan item A1, and note that Saturn's version is thinner than what we specified — it has no θ chain, no headroom against Tj(max), no maximum-power figure and no "what θ_sa do I need" answer. Ours should be better, not merely equivalent.*

## Via_Properties.png

The richest tab. A 10 mil hole, 20 mil internal pad, 40 mil plane opening, 62 mil height and 1 mil plating gives capacitance 0.4021 pF, inductance 1.3262 nH, impedance 57.429 Ω, DC resistance 1.53 mΩ, resonant frequency 6891.7 MHz, step response 25.40 ps, power 5.99 mW, cross-section 34.56 mil² and via current 1.979 A. The Information pane adds dBm power, **aspect ratio 6.20:1**, current density, via temperature, thermal resistance 179.3 °C/W and — with a via count of 10 — 17.9 °C/W per via, plus a 3.03 mV drop. A second mode computes via stub length. *Plan item A4 takes impedance, resonance, aspect ratio, via count and current from here. Step response is the one extra worth considering: it states the rise-time damage a via does to a 50 Ω line, which is the number that actually matters at speed.*

## Wavelength_Calculator.png

Wavelength from a period (10 ns) or frequency with an Er eff of 4 → 59.014 in, with a divide slider from full down to 1/20 and a note to enter Er eff = 1 for air. Buttons jump to the Er Effective calculator and to a speed-of-light reference. *We have this; the divide-fraction slider is a nicer interaction than our fixed λ/4, λ/10, λ/20 rows.*

## XL_XC_Reactance.png

Xc, Xl and LC resonance with per-field unit selectors: 1 MHz, 1 µF, 1 mH → Xc 0.1592 Ω, Xl 6283.18 Ω, resonance 5032.93 Hz. Formulas printed on the tab. *We match this, and our SI-suffix parsing removes the need for the unit radio groups.*

## What the screenshots changed in the plan

Nothing in Group A moved — A1 to A4 are confirmed by what the screenshots show, and the thermal tab turned out thinner than our specification rather than richer. Three small additions are now worth folding into their existing items when built: **min/max oscillation frequency** on the crystal card (from PPM-XTAL), **via step response** alongside the other via extras (from Via Properties), and **per-inch L and C** on the impedance tab (from Conductor Impedance). Each is one line of arithmetic on values already in hand.

Two presentation ideas are worth adopting independently of any calculation: stating a formula's **validity window on the face of the tab** rather than only warning when it is breached, and showing a target with a **coloured pass/fail band** rather than a bare computed number.
