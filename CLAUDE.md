# CLAUDE.md — EE Calculator

Conventions for this tool specifically. The user-level and `C:\Auterion` instructions still apply on top of these.

## What this is

`src/build_page.py` generates one self-contained `EE_Calculator.html` at the repo root. The whole HTML/CSS/JS template lives in a raw string in that file, so **every change is an edit to `src/build_page.py` followed by `pixi run build`** — never edit the generated HTML except to test something throwaway. Logic lives in JS because the page is interactive at runtime; Python only assembles it, so there is no second implementation and no parity test owed.

Patch `src/build_page.py` with a script written to the scratchpad, not with a shell heredoc. Backslash escapes in a non-raw Python string have silently corrupted anchors several times — `\b` became a backspace inside a regex, `\n` became a real newline inside a JS string literal. The file also contains literal Unicode (Ω, ±, —, ε), not `\u` escapes, so match those characters literally.

## Graphs

The page has two plotting paths: `drawGraph` for the filter response, and `miniPlot` for everything else. Both follow the same rules.

**A logarithmic x axis is labelled at round decades and carries minor gridlines.** Ticks land on whole powers of ten — 10 Hz, 1 kHz, 100 kHz — never on multiples of some reference frequency, so the range is snapped *outward* to whole decades rather than centred on the value of interest. Inside each decade, draw the eight lines at 2 through 9 in the lighter `.gridmin` style. Their bunching towards the next decade is the thing that tells the reader at a glance that the axis is logarithmic; a decade axis without them reads as linear and is quietly misleading. `decadeTicks(loDec, hiDec, unit)` and `decadeMinors(loDec, hiDec)` produce both, and both take whole decade numbers, not frequencies.

The rest, following the `dataviz` skill:

- One series needs no legend — the card heading names it. Two or more get **direct labels at the end of each curve**, never a legend box.
- A second series is distinguished by **dash pattern plus its own label, never by hue**. The page has one curve colour (`var(--a-link)`), which keeps every plot correct under any colour vision and in monochrome print without needing a validated multi-hue palette.
- Grid and axes are solid hairlines a shade off the surface; the curve is the only saturated ink.
- Every plot that reads a curve gets a **crosshair that snaps to the nearest sample**, on pointer move and on arrow keys. Value leads, label follows — the reader already has the curve and wants the number.
- **The plot enhances, never gates.** Every value the hover can show also appears in the card's results list, so nothing is reachable only by pointing at a chart.

## Card explanations

Every card carries an **Explain** button in its footer, right-justified on the same row as Copy results and Reset, opening a `<dialog>` with the equations behind that card. The content lives in one `HELP` object keyed by the card's reset id, and `tests/checks/check_page.py` fails if a card has no entry, an entry has no card, an entry is under 400 characters, or its markup is unbalanced — so a new card cannot ship without one.

Pitch it at an engineer who knows the theory but has not memorised these particular formulas. Give the governing equation, define every symbol, say where the model comes from, and — the part that earns its place — name the assumption that will catch them out. The IPC ampacity constant halving for internal layers, a class 2 ceramic's temperature spec being a bound over its whole rated range rather than a slope, DC bias dwarfing every other term in a capacitor budget, ε_eff differing between microstrip and stripline so length matching by physical length alone leaves skew: those are the lines worth writing. Avoid restating the card's own note, and avoid padding.

## Diagrams

Cards carry an inline SVG labelling the very parameters their fields ask for. Where a selector changes the geometry, the drawing is a function called from the top of that card's `calc*`, so the picture and the answer cannot disagree — `drawZ`, `drawDiff`, `drawTrace`, `drawVia`, `drawSP`, `drawPad`, `drawTopology`.

- Cross-sections share one convention: **filled is copper, an outline is dielectric, a heavy line is a reference plane, dashed is optional**. The `.key` paragraph under a drawing states it.
- **Prose never goes inside an SVG.** `<text>` cannot wrap, so anything longer than a symbol goes in a `.key` paragraph underneath. `tests/checks/diagram_check.py` enforces this by catching labels that run past the viewBox.
- Copper is drawn rectangular because the formulas assume a rectangle. Etch factor is not modelled, and drawing the etched trapezoid would claim an accuracy the maths does not have; the trace cards say so instead.
- No photographs or 3D renders. Saturn has four and they label nothing.
- **Never write a radical.** The mono face draws U+221A without its overbar, so `√(L/C)` in a plate, an equation block or an SVG label reads as an integral sign. `build_page.py` rewrites every radical to `sqrt(...)` as a build step and asserts none survive; keep it that way rather than reintroducing the glyph.
- A reference plane is drawn 3 px **outside** the dielectric rectangle, never on its edge or inside it. On the edge the heavy stroke is indistinguishable from the outline; inside, the rectangle edge lands on the w dimension label.
- Build symbols from `symSeries` and `symShunt` rather than by hand — they stop the wire at the component body. Branch a shunt well clear of a series body, or the junction dot is drawn inside the resistor.

## What the lint cannot see

`tests/checks/diagram_check.py` checks coordinates against the viewBox, label against label, and now label against line. It still cannot see three things, and only the browser can:

- **A glyph that renders wrongly.** The radical above is the example; the lint counted it as one character in the right place.
- **Two things that are merely too close.** Adjacent labels that read as one sentence, or a label a pixel from a dimension line, pass every numeric check.
- **A symbol that is drawn correctly but means the wrong thing** — a wire through a resistor body is valid SVG in a sane bounding box.

So run the browser pass on every change that touches a drawing. Serve the folder on an ephemeral port (the extension refuses `file://`), open each tab, and **zoom into every diagram and chart** — at full-page scale these defects are invisible.

## Fields and defaults

**A field with a default uses that default in the calculation from the start, until the user overwrites it.** A blank box showing `4.3` as its placeholder is not waiting for input — `numOr(id, dflt, lo, hi)` already computes with 4.3, and typing replaces it. Never make a card refuse to compute over a field that has a sensible default.

`tests/js/defaults_tests.js` enforces this behaviourally: for every field whose placeholder is a number, leaving the box blank must give byte-identical results to typing that number in. Add a case there whenever a new defaulted field appears.

Where a card *derives* a value that the user may then override, write it into the box with `setComputed`, which highlights it. Typing over a highlighted box makes it an input again and whatever is now missing gets solved instead. `clearComputed` at the top of a `calc*` clears only the boxes the calculator itself filled, so a user's own entry survives.

A card whose fields depend on a selector hides the ones that do not apply, from its own `calc*`, so it can never show a field its maths ignores. `.field` is a flex container, and an author `display` rule beats the UA default for `[hidden]` — hence the explicit `.field[hidden] { display: none }`. This has bitten twice now; if a hidden thing is still visible, look for a `display` rule on its own selector before looking anywhere else.

Shared board settings (copper weight, temp rise, ambient, E-series) are discovered from `data-mirror` attributes rather than hard-coded id lists: they appear on every card that reads them, with one value behind all copies.

## Standards tables

Where a card implements a published standard, **transcribe the tables mechanically, never by hand**. A typo in an IEC clearance table produces a plausible number that no unit test catches and that a reviewer will not spot. `tests/checks/iec60664_transcribe.py` translates KiCad's C++ ladders into JavaScript token for token and is re-runnable; do the same for any future table.

Then check the result against values published *independently* of the source you transcribed from. For IEC 60664-1 those are the ones every safety design note quotes — 2.5 kV impulse and 1.5 mm clearance at 230 V category II pollution degree 2, 3.0 mm reinforced, 1.0 mm creepage on a board at 250 V pollution degree 2 material group II — plus the monotonicity properties, since a worse pollution degree or material group can never require *less* creepage.

IEC 60664-1 is paywalled and its tables came from KiCad, which is GPL-3.0. That was flagged and the user decided; note it rather than re-litigating it, and flag the same thing again for any future standard.

## Honesty about models

Each card names its model and its validity window, and refuses geometry outside that window rather than returning a number that looks fine. Where a real answer lies between two computable limits — covered microstrip, say — give the bracket rather than inventing an interpolation curve. Indicative curves that are not from the user's own part must say so on the card.

## Layout

`src/` builds the page, `tests/` checks it — `tests/js/` for the node suites, `tests/checks/` for the Python structural checkers, `tests/run_all.py` as the one runner — `ext/` holds the openEMS submodule, `scripts/` has the setup scripts and `where.py`, `docs/` the design documents and the refactor plan, `examples/` the worked examples, and `user_data/` the things that are never committed. The generated `EE_Calculator.html` and its launcher stay at the repo root because they are the product; everything else is how it is made.

The tests live in `tests/`, not in `Tools\claude\scratch\` where they started. Suites are named after what they test, never after the sprint that produced them: the four `s2` to `s5` suites became `thermal_rf`, `passives_conversions`, `impedance` and `trace_width` on 2026-09-17. They are this project's tests rather than general-purpose analysis scripts, so they belong with the project; the scratch folder keeps only what is genuinely reusable elsewhere.

## Testing

`pixi run test` runs everything: the build, the harness, the three structural checkers, the EM model tests and every node suite, in one command. Use it rather than a hand-typed loop — the loop is how four stale duplicate suites went unnoticed, one of them calling a function deleted in the filter rework.

Before committing any change to the page:

```
python tests/checks/mkharness.py      # rebuild the node harness
python tests/checks/load_check.py     # the whole script runs to completion
python tests/checks/diagram_check.py  # diagram geometry lint
python tests/checks/check_page.py     # structural invariants
```

**Run the load check on every change.** The node harness stops at the wiring section, so nothing else executes the top-level code that builds the card footers, attaches listeners and restores the last tab — and an error there kills the entire script, not just one card. The specific trap is the temporal dead zone: a top-level `const` declared *below* the code that reads it throws `ReferenceError: Cannot access X before initialization` at load, and the page comes up dead with no visible clue. That has happened once already, with `HELP`. Anything the wiring section reads must be declared above the `/* wiring */` marker.

then run the node suites in `tests/js/*.js` by concatenating the harness with each suite. The harness stubs the DOM well enough to exercise the real `value` and `classList`; when a suite fails on a missing DOM method, that is a harness gap to fix in `tests/checks/mkharness.py`, not a page bug — it has been exactly that four times.

Three checks per new piece of behaviour: an interior value, a boundary or limit identity, and a sign or monotonicity check. Two of the originally planned tests were tautologies that could never fail, which is why the identity check is on the list.
