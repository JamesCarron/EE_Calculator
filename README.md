# EE Calculator

A single self-contained HTML page (`EE_Calculator.html`) with 26 calculators across seven tabs, for everyday electronics and PCB work. It opens straight from the filesystem — no server, no network, nothing leaves the machine.

Every card has an **Explain** button in its footer, opening the equations behind that card: what the formula is, where it comes from, what each symbol means, and the assumption that will catch you out. A field showing a value in its placeholder is already computing with it — a blank εr box means 4.3, not "waiting for input" — and typing replaces it. Where a card is a solver it writes its answer **into the relevant input box** and highlights it, rather than repeating it in a separate results list, so the card reads as one filled-in form. Type into a highlighted box and it becomes an input again, and whatever is now missing is solved instead. Every card has a **Copy results** button that puts its inputs and results on the clipboard as clean text.

Copper weight, temperature rise, ambient and the E-series sit **on the cards that use them**, so the control is where you are working — but there is only one value behind each. Set copper on the trace card and the impedance card sees it too; edit it from either side and the rest follow. Controls shared this way are drawn with a dashed border. A tab with more than three sections gets sub-tabs, and the page reopens on whichever tab you last used.

## Layout

```
EE_Calculator.html     the product - one self-contained file, open it directly
EE_Calculator.bat      rebuild if pixi is present, then open
src/                   everything that builds the page
  build_page.py          the generator; the whole HTML/CSS/JS template lives here
  theme_inline.py        inlines the stylesheet and fonts as base64
  theme/                 stylesheet and woff2 fonts
  em/model.py            openEMS model generation for pad capacitance
ext/openEMS-Project/   the solver, pinned as a git submodule
tests/                 every suite and structural checker; `pixi run test`
  js/                  node suites against the page's own JavaScript
  checks/              Python structural checkers and the harness generator
  run_all.py           the one runner
tools/setup_openems.py fetches the solver runtime into user_data/
docs/                  design documents and the reference screenshots
examples/              worked examples that generate solver models
user_data/             never committed; solver runtime and generated models
```

Run `pixi run build` to regenerate the page and `pixi run test` for the lot: twenty-three node suites plus the structural checks, in one command.

## Tabs

**Fundamentals** — Ohm's law and power (any two of V, I, R, P) · series/parallel for resistors, capacitors and inductors, with per-element voltage and power.

**Resistors** — divider solver (any three of Vin, Vout, R1, R2, or just the two voltages, plus optional total resistance and midpoint load current) · LED series resistor, solving either direction.

**Tolerance** — a component budget covering resistors, capacitors, inductors, crystals and voltage references, adding up initial tolerance, temperature and time drift; EIA dielectric codes are decoded rather than looked up, so X7R, Y5V and X6T all work, and DC bias and thermal hysteresis are there for the parts that need them · divider ratio error, which is the separate question of how the two legs move *relative to each other*, where matched parts beat tight parts.

**Filters & Resonance** — filter design: pick RC, RL or LC, low-pass or high-pass, and an order, and the card draws the matching topology, solves the missing value and plots the magnitude response with a hover readout · reactance and self-resonance for real capacitors *and* inductors, including their parasitics · crystal load capacitance · attenuator pads in five topologies (PI, T, bridged T, L, resistive splitter) between equal or unequal impedances.

**PCB Copper** — trace current, showing what the design draws next to what the copper can carry, with current density, skin depth and the width needed if it falls short · via properties including lumped impedance, aspect ratio, parallel count and stub resonance · fusing current under both published models, Onderdonk and an energy balance carrying the latent heat of fusion, with the spread between them · conductor spacing to IPC-2221 across all seven environments at once, and clearance and creepage to IEC 60664-1 — the standard a mains- or high-voltage-connected product is assessed against, which IPC-2221 does not cover.

**PCB Signal** — impedance for five structures (bare and covered microstrip, centred and offset stripline, grounded coplanar) with per-unit-length L and C and, given a frequency, conductor and dielectric loss in dB/m including the copper-roughness correction · differential pairs against a target band · effective permittivity with dispersion · wavelength, knee frequency and critical length · via shielding pitch for stitching fences.

**Power & Thermal** — junction temperature through a θ chain, with headroom, maximum power and the heatsink you would need · PDN target impedance.

**Utilities** — AWG wire with run length, load current and voltage drop · battery packs: pick a chemistry and it fills the cell voltages, then get energy, C-rate, runtime, charge and discharge limits and an indicative discharge curve · frequency error in ppm · conversions, holding units (mm/mil, °C/°F, dB, rectangular/polar, degrees/radians), ratio units and number bases on one tab.

Every card that has a geometry or a topology carries a diagram labelling the very parameters its fields ask for, and where a selector changes that geometry the drawing changes with it — the five impedance structures, both differential-pair structures, external against internal traces, the three filter topologies, resistors against capacitors against inductors, and a via with or without a stub. Cross-sections share one convention: filled is copper, an outline is dielectric, a heavy line is a reference plane and a dashed line is optional. Copper is drawn rectangular because that is what the formulas assume; real etched copper is a trapezoid, and the cards say so.

Cards whose point is a relationship rather than a shape get a curve instead: the filter's magnitude response, the V-shaped impedance of a real capacitor or inductor around its self-resonance, fusing current falling as the square root of fault duration, a divider's error band opening out either side of T nominal, and a battery's discharge curve. Every logarithmic axis is labelled at round decades — 10 Hz, 1 kHz, 100 kHz — and carries the eight minor gridlines inside each decade, whose bunching towards the next decade is what tells you at a glance that the axis is logarithmic. All but the error band carry a crosshair readout on hover and on arrow keys; every value they show is also in the results list, so the plot never gates anything.

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

The verification harness lives in `tests/`: `tests/checks/mkharness.py` extracts the page's JavaScript and wraps it in a DOM stub whose `value` and `classList` are real, and the suites in `tests/js/` run against it under node. Roughly 165 assertions cover every calculator, including limit identities and sign checks rather than only worked values. `tests/checks/formula_check.py` and `tests/checks/hj_kj_check.py` verify the formulas themselves against published reference values.
