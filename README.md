# EE Calculator

A single self-contained HTML page (`EE_Calculator.html`) with tabs for everyday electronics and PCB calculations. Each tab carries an inline SVG schematic of the circuit topology, drawn with theme tokens so it follows light and dark.

Where a tab is a solver, it writes its answer **into the relevant input box** and highlights it, rather than repeating it in a separate results list — so the card always reads as one filled-in form. Type into a highlighted box and it becomes an input again, and whatever is now missing is solved instead. Every card also has a **Copy results** button that puts its inputs and results on the clipboard as clean text for pasting into a document.

**Ohm's Law** — enter any two of V, I, R, P; the other two are filled in.

**Resistors** (sub-tabs, and the only tab that shows the E-series selector, default E96)

- *Divider* — one solver: enter any three of Vin, Vout, R1, R2, or just the two voltages, plus optional total resistance and midpoint load current. It fills in whatever is missing, suggests the nearest E-series value, and searches the best standard pairs when both legs are open.
- *Series / Parallel* — both combinations of a list of values at once.
- *LED Resistor* — solves the series resistor from the forward current, or the current from a resistor you already have.
- *Accuracy* — what tolerance, TCR and ageing do to a divider's ratio: exact worst case, RSS, the Vout window, and how much of the error cancels if the two legs track.

**RC Filter** — cutoff, with any two of R, C, f filled in from the third.

**Reactance** — X_C, X_L and LC resonance.

**PCB** — trace width ↔ current (IPC-2221, with resistance, drop and power over a given length), via properties (ampacity, DC resistance, inductance, capacitance, thermal resistance), fusing current (Onderdonk), and the IPC-2221 Table 6-1 conductor-spacing bands for all seven environments.

**Impedance** — single-ended microstrip and stripline Z₀ (IPC-2141 first-order, with validity-range warnings), ε_eff and propagation delay; wavelength, knee frequency and critical trace length.

**Crystal** — Pierce load capacitance (solve C1/C2 from the C_L spec, or the load a given pair presents) and ppm ↔ Hz with clock drift.

**Utilities** — AWG wire table (diameter, area, resistance, both handbook ampacities); number bases (decimal, hex, binary, octal, arbitrary size, with two's complement at each standard width); ratio units (%, ppm, ppb, decimal); and mm/mil, °C/°F, dB/ratio conversions.

All calculator logic runs client-side in the page — it works offline, opened straight from the filesystem, with no server and no network access. Python is only the build harness: `build_page.py` assembles the page and `theme_inline.py` inlines the stylesheet and its two webfonts so the file stays self-contained.

## Use

Open `EE_Calculator.html` in a browser, or run `EE_Calculator.bat`, which rebuilds the page (when pixi is available) and opens it.

Values accept SI suffixes: `4k7`, `10n`, `2.2M`, `100u` all parse as expected. Dimension fields on the PCB and Impedance tabs are millimetres by default and also take `mil`, `um` and `in` suffixes.

Deep links open a tab directly: `EE_Calculator.html#pcb`, `#res-acc`, `#util`.

## Build

```
pixi run build
```

Everything the build needs is inside this folder — `theme/` holds the stylesheet and the two webfonts. If `theme_inline.py` is missing the page is still written, unstyled, with a warning.

## Layout

- `build_page.py` — page generator; the HTML/CSS/JS template lives here.
- `theme_inline.py`, `theme/` — stylesheet and webfonts, inlined at build time.
- `EE_Calculator.html` — generated output, committed so the tool works without pixi.
- `user_data/` — local user files; never committed (gitignored).
