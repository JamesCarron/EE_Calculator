# Saturn PCB Toolkit — full feature inventory and what to borrow

Source: the help PDF shipped with **Saturn PCB Toolkit V8.47**, installed at `C:\Program Files (x86)\Saturn PCB Design\Saturn PCB Toolkit V8.47\Saturn PCB Toolkit Help.pdf` (47 pages, help text dated 6-8-2026). Feature names and computed quantities below are read from that document, not from the marketing page, so this list is complete rather than indicative. Compiled 2026-09-10 to decide what EE Calculator should adopt.

## Complete Saturn feature inventory

| # | Tool | Inputs | Computes |
|---|---|---|---|
| 1 | Bandwidth & Max Conductor Length | Risetime or frequency; Er; microstrip/stripline; Sr divide factor (default 0.25 Sr); λ divide factor (default 1/7) | Maximum conductor length before it must be treated as a transmission line, by IPC-2251 method and by a frequency-domain method |
| 2 | Conductor Impedance | Conductor width, height above reference plane, frequency (microstrip) | Zo, Lo, Co, Tpd |
| 3 | Conductor Properties | Solve for amperage *or* width; internal/external; plane present, plane thickness, distance to plane; parallel conductor count; width, length, PCB thickness, frequency, load current; temp rise, ambient | Conductor current for a given temp rise, DC resistance, total cross-section, power dissipation (W and dBm), voltage drop, loaded voltage drop, skin depth, skin-depth percentage, warning when ambient + rise exceeds material Tg |
| 4 | Conversion Calculator | — | mils ↔ mm (plus other units), °C ↔ °F, dB/voltage gain as a bench chain (dBm in + gain − attenuator → dBm out, volts out), rectangular ↔ polar, degrees ↔ radians, links to reference charts, copper-weight vs conductor-spacing guide |
| 5 | Differential Pairs with Crosstalk | W/H, S/H; target ZDiff with tolerance slider; protocol preset dropdown; applied voltage, coupled length, risetime | Zo, Zdifferential, Zodd, Zeven with in/out-of-tolerance indicator; NEXT: Kb, Kb′, coupling in dB, NEXT voltage, saturated length Lsat. Valid only for 0.1 < W/H < 3.0 and 0.1 < S/H < 3.0 |
| 6 | Embedded Resistors | Resistance per square, length, width | Resistance of the embedded element |
| 7 | Er Effective | Conductor width, height, frequency | Effective dielectric constant for microstrip |
| 8 | Fusing Current | Conductor width, fuse time, Onderdonk multiplier | Cross-section, current that destroys the conductor |
| 9 | Mechanical Information | Wire gauge; load current; wire length | Wire diameter, ohms per unit length, ampacity, voltage drop over the run; plus drill chart and screw-thread size tables |
| 10 | Minimum Conductor Spacing | Voltage band (or custom above 500 V), device/assembly type | Minimum spacing per IPC-2221C |
| 11 | Ohm's Law (and friends) | V/I/R/P; LED supply, Vf, current; 2–4 resistors series or parallel with applied voltage; PI-pad and T-pad attenuation, Zin, Zout; 2–4 capacitors; 2–4 inductors | The missing Ohm's-law quantity; LED series resistor; total R with per-resistor current and wattage; attenuator resistor values; total C; total L |
| 12 | Padstack Calculator | Hole diameter, plated/non-plated, annular ring, isolation width; BGA ball diameter; pad pitch, conductor width, spacing constraint; pin side a/b | Pad diameters for external / internal signal / internal plane layers, thermal inner diameter and spoke width; BGA nominal land and land variation (IPC-7351A); maximum pad diameter to fit one or two conductors between pads, with an annular-ring warning; corner-to-corner pin diagonal with suggested min/max drill |
| 13 | PDN Calculator | Rail voltage, maximum current, transient percentage, maximum AC ripple; plane area, plane separation, frequency | Target PDN impedance; plane capacitive reactance and total plane capacitance |
| 14 | Planar Inductors | Turns, conductor width, spacing, outer radius; square / hexagonal / octagonal / circular | Inner diameter, fill factor, inductance |
| 15 | PPM-XTAL | Crystal load capacitance, stray capacitance, chosen C1/C2; centre frequency, ppm or drifted frequency | Load the crystal actually sees, rule-of-thumb C1/C2 starting point, ppm ↔ Hz both directions with min/max oscillation frequency |
| 16 | Thermal Management | Device thermal resistance and power dissipation; heat-sink thermal resistance | Device junction temperature; heat-sink junction temperature |
| 17 | Via Properties | 2-layer / multilayer / microvia; hole diameter, internal pad diameter, reference-plane opening, via height, plating thickness, temp rise, via count; drill diameter, anti-pad H/W, via spacing, substrate anisotropy, baud rate | Via capacitance, inductance, AC impedance √(L/C), DC resistance, resonant frequency, T10–90 step response, power dissipation (W and dBm), voltage drop, cross-section, current for a given temp rise, thermal resistance per via, aspect-ratio check; and maximum via stub length before resonant nulls |
| 18 | Wavelength | Period or frequency, Er effective, divide factor (full to 1/20) | Wavelength and its fractions |
| 19 | XC-XL Reactance | Frequency, capacitance, inductance | Xc, Xl, LC resonant frequency |
| 20 | Program Options / General Settings | — | IPC version choice (2152 with or without modifiers, or 2221), manual base copper weight and plating thickness, conductor etch factor (none / 1:1 / 2:1) for trapezoidal cross-section, via-height influence toggle, aspect-ratio limit, imperial/metric with optional microns, substrate material presets carrying Er and Tg, global temp rise and ambient, print |
| 21 | Crosstalk Calculator | — | Readded but marked unsupported; the documentation cites a "lack of faith in the formula" that drives it |

## What EE Calculator already covers

Ohm's law; series/parallel resistance; LED series resistor; RC cutoff; Xc/Xl and LC resonance; IPC-2221 trace width ↔ current with resistance, drop and power; via ampacity, resistance, inductance, capacitance and thermal resistance; Onderdonk fusing; IPC-2221 Table 6-1 spacing across all seven environments; microstrip and stripline Zo with ε_eff and Tpd; wavelength, knee frequency and critical length; crystal load capacitance and ppm; AWG table; mm/mil, °C/°F, dB/ratio, number bases and ratio units.

Several things EE Calculator has are **absent from Saturn**: a divider solver of any kind, the divider tolerance/TCR error budget, RC filter cutoff, E-series standard-value suggestions and pair search, number-base conversion, and ppm/ppb/% conversion. The two tools are not in a subset relationship.

## Recommendations

### Tier 1 — small effort, broad use, extends cards that already exist

- **Junction temperature.** Tj = Ta + P·Σθ across a θ_jc + θ_cs + θ_sa chain, with headroom against Tj(max). Two multiplications, universally needed, and nothing in the tool does thermal yet.
- **Series/parallel for capacitors and inductors.** The existing resistor card already does the arithmetic; capacitors just swap which formula is series and which is parallel. One card becomes three for almost no code.
- **Wire voltage drop.** The AWG table already yields ohms per metre; adding a run length and load current turns a lookup into an answer. Directly relevant to harness work.
- **Skin depth.** One formula, and it makes the existing frequency-aware tabs more useful. Saturn also reports it as a percentage of conductor thickness.
- **Via extras that are nearly free.** L and C are already computed, so AC impedance √(L/C) and the LC resonant frequency are one line each; the aspect-ratio check (height ÷ drill, against a limit) is a division that catches a real manufacturability problem.
- **Rectangular ↔ polar and degrees ↔ radians.** Two more pairs in the Utilities conversion card, which is already built for exactly this.
- **Substrate material presets.** A dropdown carrying Er and Tg for common laminates, feeding the Impedance and Wavelength tabs, and enabling a Tg-exceeded warning on the trace card. This improves three existing tabs rather than adding a fourth.

### Tier 2 — worth doing, more than an afternoon

- **PI-pad, T-pad and L-pad attenuators.** Closed-form resistor values from attenuation and impedances. Fits the Resistors tab, which is the tool's strongest area.
- **dBm chain.** Input level plus gain minus attenuation, with volts into a stated impedance. A natural extension of the dB/ratio conversion already present.
- **Plane capacitance and PDN target impedance.** Parallel-plate capacitance from area and separation, and Z_target = V_rail·ripple% / (I_max·transient%). Both are simple, and together they make a credible decoupling starting point.
- **Copper weight, plating thickness and etch factor as trace inputs.** Currently copper weight is a fixed dropdown and the cross-section is assumed rectangular. Modelling plating separately and applying a trapezoidal etch factor is what separates a rough answer from a defensible one.
- **Padstack feasibility checks.** Not the BGA land tables — Altium owns those — but the routing questions: the largest pad that still lets a conductor of given width pass between two pads at a given pitch and clearance, and the corner-to-corner diagonal of a rectangular pin with a suggested drill range.

### Tier 3 — deliberately skip

- **Crosstalk / NEXT.** Saturn ships it disowned, and that is the strongest possible argument against copying it.
- **Differential pair impedance.** The empirical formulas are materially less accurate than the single-ended ones. Worth noting that Saturn's presentation is the right model if this is ever revisited: it states the validity window explicitly and flags out-of-range input rather than returning a confident number.
- **Embedded resistors, planar inductors.** Genuinely niche.
- **Drill charts, screw threads, BGA land sizes.** Reference tables better served by Altium and vendor data.
- **IPC-2152 with modifiers.** Chart data from a paywalled standard; the freely published IPC-2221 equation stays the honest choice, named on the page.

## Open items

None. The tier list above was put to the owner for selection; whatever is chosen becomes the next build task and this file records why the rest was declined.
