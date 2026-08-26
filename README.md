# EE Calculator

A single self-contained HTML page (`EE_Calculator.html`) with tabs for simple electronics calculations: Ohm's law and power, resistor dividers (one solver: enter any three of Vin, Vout, R1, R2 — or just the two voltages — plus optional total resistance and midpoint load current; it solves whatever is missing, suggests E-series values, and searches the best standard pairs when both legs are open), series/parallel resistance, RC filter cutoff, reactance, and LED series resistors. Each tab carries an inline SVG schematic of the circuit topology, drawn with house-token colors so it follows light/dark theme.

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
