# EE Calculator

A single self-contained HTML page (`EE_Calculator.html`) with 26 calculators across seven tabs, for everyday electronics and PCB work. It opens straight from the filesystem — no server, no network, nothing leaves the machine.

Where a card is a solver it writes its answer **into the relevant input box** and highlights it, rather than repeating it in a separate results list, so the card reads as one filled-in form. Type into a highlighted box and it becomes an input again, and whatever is now missing is solved instead. Every card has a **Copy results** button that puts its inputs and results on the clipboard as clean text.

Copper weight, temperature rise, ambient and the E-series sit **on the cards that use them**, so the control is where you are working — but there is only one value behind each. Set copper on the trace card and the impedance card sees it too; edit it from either side and the rest follow. Controls shared this way are drawn with a dashed border. A tab with more than three sections gets sub-tabs, and the page reopens on whichever tab you last used.

## Tabs

**Fundamentals** — Ohm's law and power (any two of V, I, R, P) · series/parallel for resistors, capacitors and inductors, with per-element voltage and power.

**Resistors** — divider solver (any three of Vin, Vout, R1, R2, or just the two voltages, plus optional total resistance and midpoint load current) · LED series resistor, solving either direction · accuracy, showing what tolerance, TCR and ageing do to a divider's ratio.

**Filters & Resonance** — filter design: pick RC, RL or LC, low-pass or high-pass, and an order, and the card draws the matching topology, solves the missing value and plots the magnitude response with a hover readout · reactance and self-resonance for real capacitors *and* inductors, including their parasitics · crystal load capacitance · PI, T and L attenuator pads.

**PCB Copper** — trace current, showing what the design draws next to what the copper can carry, with current density, skin depth and the width needed if it falls short · via properties including lumped impedance, aspect ratio, parallel count and stub resonance · Onderdonk fusing current · IPC-2221 conductor spacing across all seven environments at once.

**PCB Signal** — impedance for five structures (bare and covered microstrip, centred and offset stripline, grounded coplanar) with per-unit-length L and C · differential pairs against a target band · effective permittivity with dispersion · wavelength, knee frequency and critical length · via shielding pitch for stitching fences.

**Power & Thermal** — junction temperature through a θ chain, with headroom, maximum power and the heatsink you would need · PDN target impedance.

**Utilities** — AWG wire with run length, load current and voltage drop · battery energy, C-rate and runtime · frequency error in ppm · number bases · ratio units · mm/mil, °C/°F, dB, rectangular/polar and degrees/radians.

Every card that has a geometry or a topology carries a diagram labelling the very parameters its fields ask for, and where a selector changes that geometry the drawing changes with it — the five impedance structures, both differential-pair structures, external against internal traces, the three filter topologies, resistors against capacitors against inductors, and a via with or without a stub. Cross-sections share one convention: filled is copper, an outline is dielectric, a heavy line is a reference plane and a dashed line is optional. Copper is drawn rectangular because that is what the formulas assume; real etched copper is a trapezoid, and the cards say so.

Cards whose point is a relationship rather than a shape get a curve instead: the filter's magnitude response, the V-shaped impedance of a real capacitor or inductor around its self-resonance, fusing current falling as the square root of fault duration, and a divider's error band opening out either side of T nominal. All but the error band carry a crosshair readout on hover and on arrow keys; every value they show is also in the results list, so the plot never gates anything.

Where the model is the interesting part — impedance, effective permittivity, fusing, wavelength, reactance, junction temperature, via shielding, spacing — the governing equation sits on a plate beside the drawing rather than only in a footnote, and the Ohm's law card carries the twelve-way wheel.

## Models and their limits

Impedance uses **Hammerstad–Jensen** throughout, with **Kirschning–Jansen** dispersion when a frequency is given, so Zo, ε_eff, propagation delay and the per-unit-length L and C all agree — √(L/C) returns Zo. Geometry outside the model's 0.01 ≤ w/h ≤ 100 range is refused rather than computed, because the formula breaks down there rather than merely losing accuracy.

Current capacity uses **IPC-2221**, whose equation is freely published, rather than IPC-2152, whose data sits behind a paywall. IPC-2152 permits somewhat more current, so this errs conservative; each result names the method and constant it used.

Covered microstrip gives the **fully covered limit and the bare value as a bracket** rather than interpolating to a finite mask thickness, because any curve between the two would be invented rather than sourced. Offset stripline is normalised against the centred case, without which the IPC expression reports a *higher* impedance for an off-centre trace than a centred one.

Differential pair and coplanar figures come from empirical fits. Each card prints its validity window; treat the results as a starting geometry and have the fabricator field-solve the real stackup.

## Use

Open `EE_Calculator.html`, or run `EE_Calculator.bat`, which rebuilds the page when pixi is available and opens it.

Values accept SI suffixes — `4k7`, `10n`, `2.2M`, `100u` all parse. Dimension fields on the PCB tabs are millimetres by default and also take `mil`, `um` and `in`.

Deep links open a tab directly: `#copper`, `#signal`, `#res-acc`, `#pwr`.

## Build

```
pixi run build
```

Everything the build needs is in this folder; `theme/` holds the stylesheet and its two webfonts, inlined at build time by `theme_inline.py`.

## Layout

- `build_page.py` — page generator; the HTML/CSS/JS template lives here.
- `theme_inline.py`, `theme/` — stylesheet and webfonts.
- `EE_Calculator.html` — generated output, committed so the tool works without pixi.
- `Implementation_Plan.md`, `Implementation_Checklist.md`, `Saturn_Feature_Comparison.md`, `SaturnPCB/` — the design record.
- `user_data/` — local files; never committed.

## Tests

The verification harness lives in `C:\Auterion\Tools\claude\scratch\`: `eecalc_mkharness.py` extracts the page's JavaScript and wraps it in a DOM stub whose `value` and `classList` are real, and the `eecalc_*_tests.js` files run against it under node. Roughly 165 assertions cover every calculator, including limit identities and sign checks rather than only worked values. `eecalc_formula_check.py` and `eecalc_hj_kj_check.py` verify the formulas themselves against published reference values.
