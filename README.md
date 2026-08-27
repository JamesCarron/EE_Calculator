# EE Calculator

A single self-contained HTML page (`EE_Calculator.html`) with tabs for everyday electronics and PCB calculations. Each tab carries an inline SVG schematic of the circuit topology, drawn with house-token colors so it follows light/dark theme.

**Circuit tabs** — Ohm's law and power; resistor dividers (one solver: enter any three of Vin, Vout, R1, R2 — or just the two voltages — plus optional total resistance and midpoint load current; it solves whatever is missing, suggests E-series values, and searches the best standard pairs when both legs are open); series/parallel resistance; RC filter cutoff; reactance; LED series resistors.

**PCB Power** — trace width ↔ current (IPC-2221, with resistance, drop and power over a given length), via properties (ampacity, DC resistance, inductance, capacitance, thermal resistance), fusing current (Onderdonk), and the IPC-2221 Table 6-1 conductor-spacing bands for all seven environments.

**Impedance** — single-ended microstrip and stripline Z₀ (IPC-2141 first-order, with validity-range warnings), ε_eff and propagation delay; wavelength, knee frequency and critical trace length.

**Crystal** — Pierce load capacitance (solve C1/C2 from the C_L spec or check what the crystal sees) and ppm ↔ Hz with clock drift.

**Utilities** — AWG wire table (diameter, area, resistance, both handbook ampacities) and mm/mil, °C/°F, dB/ratio conversions.

All calculator logic runs client-side in the page — it works offline, opened straight from the filesystem, with no server and no network access. Python is only the build harness: `build_page.py` assembles the page and inlines the Auterion house stylesheet and fonts so the file stays self-contained.

## Use

Open `EE_Calculator.html` in a browser, or run `EE_Calculator.bat`, which rebuilds the page (when pixi is available) and opens it.

Values accept SI suffixes: `4k7`, `10n`, `2.2M`, `100u` all parse as expected. The E-series used for standard-value suggestions (divider solver, pair finder, LED resistor) is a single top-level setting in the tab bar, defaulting to E96.

## Build

```
pixi run build
```

Requires the house stylesheet helper at `C:\Auterion\Tools\brand\` (falls back to plain output with a warning if absent).

## Layout

- `build_page.py` — page generator; the HTML/JS template lives here.
- `EE_Calculator.html` — generated output, committed so the tool works without pixi.
- `user_data/` — local user files; never committed (gitignored).
