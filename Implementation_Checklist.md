# EE Calculator — implementation checklist

Tick what you want built. Every item has a short id, so you can reply with just the ids (for example "A1, C2, D1–D3") rather than editing the file. Formulas and validation vectors for everything already specified are in `Implementation_Plan.md`; anything here marked *unspecified* would need a short spec first.

Status against our tool: **have** = already built · **partial** = built but missing what is listed · **none** = not built.

Effort: **S** = under an hour, extends an existing card · **M** = a few hours, new card or new maths · **L** = a day or more, or touches verified code.

Items already confirmed by you are pre-ticked.

---

## A. Confirmed — ready to build now

- [x] **A1** — Junction temperature. θ chain (θjc + θcs + θsa), Tj, case and sink temperatures, headroom to Tj(max), maximum allowable power, and the required θsa to hit a target. Richer than Saturn's own version. *New tab. **M***
- [x] **A2** — Wire voltage drop. Adds run length, load current, one-way/round-trip and conductor temperature to the AWG card. *Extends Utilities. **S***
- [x] **A3** — Capacitors and inductors in series/parallel, plus per-element current and power for resistor strings. *Extends Resistors. **S***
- [x] **A4** — Via impedance √(L/C), self-resonant frequency, aspect-ratio check, via count, and drop/dissipation at a stated current. *Extends PCB. **S***

## B. Small additions found in the screenshots

- [ ] **B1** — Crystal min/max oscillation frequency from centre frequency and ppm. *Extends Crystal. **S***
- [ ] **B2** — Via step response (T10–90), the rise-time cost a via imposes on a 50 Ω line. *Extends PCB. **S***
- [ ] **B3** — Per-inch (or per-mm) L and C on the impedance tab, alongside Zo and Tpd. *Extends Impedance. **S***
- [ ] **B4** — Onderdonk multiplier and an explicit ">5 s is out of scope" warning on the fusing card. *Extends PCB. **S***
- [ ] **B5** — Wavelength divide-fraction slider (full down to 1/20) and period-as-input, replacing our fixed λ/4, λ/10, λ/20 rows. *Extends Impedance. **S***

## C. Materials and copper modelling

- [ ] **C1** — Substrate library: ~25 laminates each carrying Er and Tg, feeding Impedance, Wavelength and via capacitance, with both values editable after selection. *Cross-cutting. **M***
- [ ] **C2** — Tg exceeded warning on the trace card when ambient + rise passes the laminate's Tg. Needs C1. *Extends PCB. **S***
- [ ] **C3** — Base copper weight and plating thickness as separate inputs, plating applying to external layers only. *Extends PCB. **M***
- [ ] **C4** — Etch factor (none / 1:1 / 2:1) for a trapezoidal rather than rectangular cross-section. Changes ampacity by ~3.5 % at 1 oz and more as copper thickens. **Touches trace maths currently verified against reference values.** *Extends PCB. **L***

## D. Conductor properties (Saturn's flagship tab)

- [ ] **D1** — Skin depth and skin depth as a percentage of copper thickness. *Extends PCB. **S***
- [ ] **D2** — Current density (A/mm² or A/mil²). *Extends PCB. **S***
- [ ] **D3** — Show required current against achievable current together, so an undersized trace is obvious at a glance. This is the single best presentation idea in Saturn. *Extends PCB. **S***
- [ ] **D4** — Plane present and distance to plane as ampacity modifiers. *IPC-2152 chart data, paywalled — would need a defensible source. **L, unspecified***
- [ ] **D5** — Parallel conductor count as an ampacity modifier. *Same sourcing problem. **L, unspecified***

## E. Impedance structures

- [ ] **E1** — Asymmetric (offset) stripline. Verified: 59.85 Ω for w 0.2, h 0.25, c 0.75, εr 4.3. *Extends Impedance. **M***
- [ ] **E2** — Grounded coplanar waveguide, via Hilberg's elliptic approximation. Verified: 55.95 Ω at ε_eff 3.066. *Extends Impedance. **M***
- [ ] **E3** — Covered / solder-masked microstrip, using the ratio construction that fixes IPC-2141's broken embedded formula. Verified: 25 µm mask drops 53.52 Ω to 52.64 Ω. *Extends Impedance. **M***
- [ ] **E4** — Dual stripline (two signal layers between planes). *Niche. **M, unspecified***
- [ ] **E5** — Standalone Er effective calculator with frequency dependence, Hammerstad–Jensen. *New card. **M***

## F. Utilities and conversions

- [ ] **F1** — Rectangular ↔ polar. *Extends Utilities. **S***
- [ ] **F2** — Degrees ↔ radians. *Extends Utilities. **S***
- [ ] **F3** — dBm bench chain: input level + gain − attenuation → output dBm, with volts into a stated impedance, and dBm → watts. *Extends Utilities. **M***
- [ ] **F4** — Drill chart and screw thread tables. *Reference data better served by vendor tables. **M***

## G. New cards

- [ ] **G1** — PI, T and L-pad attenuators. Verified against published 50 Ω tables at 6 dB. *New card in Resistors. **M***
- [ ] **G2** — Plane capacitance (area, separation, εr) and PDN target impedance. Verified: 3.807 nF and 2.4 mΩ on the worked example. *New card. **M***
- [ ] **G3** — Padstack routing feasibility: largest pad that still passes a conductor between two pads at a given pitch and clearance; pin corner-to-corner diagonal with a suggested drill range. Not BGA land tables. *New card. **M***
- [ ] **G4** — Bandwidth and max conductor length presented as two methods side by side (IPC-2251 and frequency-domain) with adjustable divide factors, the way Saturn does. We already have knee frequency and critical length. *Extends Impedance. **M***

## H. Cross-cutting behaviour

- [ ] **H1** — "Send to…" actions passing values between tabs (ε_eff into Wavelength, solved width into the current card). *Cross-cutting. **S***
- [ ] **H2** — Print / export a card or the whole page as a clean report. *Cross-cutting. **M***
- [ ] **H3** — Print each formula's validity window on the face of the card, rather than only warning once it is breached. *Cross-cutting. **S***
- [ ] **H4** — Shared settings strip for copper weight, ambient and temperature rise, replacing the per-card duplicates. Refactor of working code, no new capability. *Cross-cutting. **M***

## X. Recommended against — listed so the decision is yours

- [ ] **X1** — Differential pair impedance (Zdiff, Zodd, Zeven). Empirical formulas materially less accurate than the single-ended ones.
- [ ] **X2** — Crosstalk / NEXT. Saturn ships its own version disowned, citing a lack of faith in the formula.
- [ ] **X3** — Embedded resistors. Niche; needs IPC-2316 sheet-resistance data.
- [ ] **X4** — Planar inductors. Niche outside RFID and wireless coil work.
- [ ] **X5** — BGA land sizes and padstack pad diameters. Altium already generates these.
- [ ] **X6** — IPC-2152 with modifiers as the ampacity basis. Chart data from a paywalled standard; IPC-2221's published equation is the honest choice.

---

## Suggested groupings, if you would rather pick a shape than items

- **Fastest useful win** — A1–A4 plus B1–B5 and D1–D3. All small, all extend existing cards, no risk to verified code.
- **Power electronics focus** — A1, A2, A4, C1–C4, D1–D3. Thermal, harness, copper and current, which is where drone work actually bites.
- **Signal integrity focus** — B2, B3, B5, C1, E1–E3, E5, G4, H1. Impedance structures and the transmission-line questions.
- **Everything low-risk** — every S and M item, leaving out C4, D4, D5 and the X list.
