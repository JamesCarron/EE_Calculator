# EE Calculator — implementation checklist

Settled by tab-by-tab interview on 2026-09-10. This is now a record of what was decided rather than a selection sheet; the specifications are in `Implementation_Plan.md` and the per-tab reference in its appendix.

Effort: **S** = under an hour, extends an existing card · **M** = a few hours, new card or new maths · **L** = a day or more, or touches verified code.

---

## In scope

### New cards

- [x] **A1** — Junction temperature. θ chain (θjc + θcs + θsa), Tj, case and sink temperatures, headroom to Tj(max), maximum allowable power, required θsa for a target. Richer than Saturn's own version, which has none of the last four. **M**
- [x] **G1** — PI, T and L-pad attenuators. Closed-form from attenuation and impedance; verified against published 50 Ω tables at 6 dB. **M**
- [x] **G2** — Plane capacitance and PDN target impedance. Verified at 3.807 nF and 2.4 mΩ. **M**
- [x] **E5** — Standalone Er effective card with frequency dependence, Hammerstad–Jensen. **M**

### Extensions to existing cards

- [x] **A2** — Wire voltage drop: run length, load current, one-way/round-trip, conductor temperature. **S**
- [x] **A3** — Capacitors and inductors in series/parallel, plus per-element current and power. **S**
- [x] **A4** — Via impedance √(L/C), self-resonance, aspect-ratio check, via count, drop and dissipation at current. **S**
- [x] **B1** — Crystal min and max oscillation frequency. **S**
- [x] **B3** — Per-unit-length L and C on the impedance card. **S**
- [x] **B4** — Onderdonk multiplier and ">5 s out of scope" warning on fusing. **S**
- [x] **B5** — Wavelength divide-fraction slider (full to 1/20) and period as input. **S**
- [x] **F1** — Rectangular ↔ polar. **S**
- [x] **F2** — Degrees ↔ radians. **S**
- [x] **F3** — dBm bench chain with volts into a stated impedance. **M**

### Conductor properties

- [x] **D1** — Skin depth and skin depth as a percentage of copper thickness. **S**
- [x] **D2** — Current density. **S**
- [x] **D3** — Required vs achievable current shown together, so an undersized trace is obvious. **S**
- [x] **D4/D5** — Plane and parallel-conductor ampacity modifiers. **Conditional:** to be built from published open-literature fits with the source named on the card. If no citable fit is found, these are dropped rather than invented. **L**

### Impedance structures

- [x] **E1** — Asymmetric (offset) stripline. Verified 59.85 Ω. **M**
- [x] **E2** — Grounded coplanar waveguide via Hilberg's approximation. Verified 55.95 Ω. **M**
- [x] **E3** — Covered / soldermask microstrip, using the ratio construction that fixes IPC-2141's broken embedded formula. Verified 53.52 → 52.64 Ω for 25 µm of mask. **M**

### Cross-cutting

- [x] **H3** — Print each formula's validity window on the face of the card, not only on breach. **S**
- [x] **H4** — Shared settings strip for copper weight, ambient and temperature rise. Refactor, so it goes last. **M**
- [x] **Regrouping** — seven-tab structure, done first so everything else lands in its final home. **M**

---

## Excluded, with the reason

- [ ] **C1–C4** — Substrate library, Tg warning, separate plating thickness, etch factor. Consequence: Er stays a manually entered number, and the Tg-exceeded warning is not possible without a laminate's Tg. Excluding C4 also removes the batch's main regression risk.
- [ ] **B2** — Via step response. The one via output not taken.
- [ ] **E4** — Dual stripline. Niche.
- [ ] **F4** — Drill chart and screw thread tables. Vendor data that goes stale.
- [ ] **G3** — Padstack routing feasibility.
- [ ] **G4** — Dual-method max conductor length. We keep our knee frequency and critical length.
- [ ] **H1** — Send-to actions between tabs.
- [ ] **H2** — Print / export a report. Per-card Copy already exists.
- [ ] **X1** — Differential pair impedance. Empirical formulas materially less accurate than single-ended.
- [ ] **X2** — Crosstalk / NEXT. Saturn ships its own version disowned.
- [ ] **X3** — Embedded resistors. Niche.
- [ ] **X4** — Planar inductors. Niche.
- [ ] **X5** — BGA land sizes and padstack pad diameters. Altium generates these.
- [ ] **X6** — IPC-2152 with modifiers as the ampacity basis. Paywalled chart data; IPC-2221's published equation stays.

Two tabs contribute nothing because ours already match or beat them: **Min Conductor Spacing** (we show all seven environments at once rather than one at a time) and **XL-XC Reactance** (SI-suffix parsing removes the need for unit radio buttons).

---

## Resulting structure

Eight tabs become seven while the tool gains roughly fifteen calculators. Full reasoning in `Implementation_Plan.md`.

| Tab | Cards |
|---|---|
| **Fundamentals** | Ohm's Law & Power · Series / Parallel (R, C, L) |
| **Resistors** *(E-series selector)* | Divider · LED Resistor · Attenuator Pads · Accuracy |
| **Filters & Resonance** | RC Filter · Reactance · Crystal Load Capacitance · Frequency Error |
| **PCB Copper** | Trace Current · Via · Fusing Current · Conductor Spacing |
| **PCB Signal** | Impedance · Er Effective · Wavelength & Critical Length |
| **Power & Thermal** | Junction Temperature · Plane Capacitance · PDN Target Impedance |
| **Utilities** | AWG Wire · Number Bases · Ratio Units · Conversions |

## Build order

1. Regrouping, no behaviour change, existing tests must pass untouched.
2. New cards: junction temperature, plane capacitance, PDN target, attenuator pads, Er effective.
3. Extensions: C and L series/parallel, wire drop, via extras, crystal min/max, Onderdonk multiplier, wavelength slider, conversions.
4. Impedance structures: covered microstrip, coplanar, asymmetric stripline, per-unit-length L and C.
5. Conductor properties: required vs achievable, skin depth, current density.
6. Research then build or abandon: plane and parallel-conductor modifiers.
7. Cross-cutting: validity windows, then the shared settings strip.
