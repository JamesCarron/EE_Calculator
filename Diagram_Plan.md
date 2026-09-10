# Diagram Plan

## Goal

Explain the non-obvious parameters of every calculator with a picture, the way the Saturn PCB Toolkit does — a drawing beside the fields that labels the very symbols the fields ask for, so "Dielectric height h" or "Edge-to-edge spacing" needs no prose. This document is the research step (a complete inventory of Saturn's own diagrams), the resulting plan, and a record of what was built. All three tiers are implemented.

## Part 1 — Inventory of every diagram in the Saturn PCB Toolkit

Taken from the nineteen tab screenshots in `SaturnPCB/`, captured from PCB Toolkit V8.47. Every visual element is listed, including the ones that carry no information.

| Tab | Visual | Kind | What it labels |
| --- | --- | --- | --- |
| Conductor Properties | 3D trace cross-section — green substrate, blue conductor on top | Render, unlabelled | Nothing; it conveys "external trace on a board" only |
| Conductor Properties | Small orange trapezoid beside "Etch Factor: 2:1" | Glyph | That the etched cross-section is a trapezoid, not a rectangle |
| Conductor Impedance | Cross-section with `W` horizontal dimension arrow and `H` vertical dimension arrow | Labelled cross-section, **mode-switching** | Conductor width and dielectric height; the drawing changes with the Passive Circuits radio group (Microstrip, Microstrip Embed, Stripline, Stripline Asym, Dual Stripline, Coplanar Wave) |
| Er Effective | The same `W`/`H` cross-section | Labelled cross-section | Identical drawing reused, so one geometry idea is taught once |
| Differential Pairs / XTALK | Cross-section with `W`, `S`, `W` across the top and `H` down the side, two traces over a plane | Labelled cross-section, mode-switching | Trace width, edge-to-edge spacing, dielectric height; follows the Differential Layer radio group (six options) |
| Via Properties | Plan view: concentric circles with leader lines reading "Via Pad", "Ref Plane Opening", "Via Plating" | Annotated plan view | Which diameter each field means, from the outside in |
| Via Properties | Section view: layer stack with a "Ref Plane" leader and a "Via Height" dimension arrow | Annotated section | That via height is the drilled depth, not the board outline |
| Padstack Calculator | Thermal-relief pad plan view with red dimension arrows: Spoke Width, Annular Over Drill, Inner Diameter, Outer Diameter, Isolation Width | Annotated plan view | Five padstack dimensions that are impossible to name unambiguously in words |
| Min Conductor Spacing | Cross-section, green substrate with a blue trapezoidal conductor between planes | Render, unlabelled | Context only; the actual spacing dimension is not drawn |
| Fusing Current | Photograph — micrograph of a burnt/fused trace | Photo, decorative | Nothing; it sets the subject |
| Fusing Current | Orange trapezoid glyph beside "Etch Factor: 2:1" | Glyph | As above |
| Planar Inductors | Spiral plan view with `W`, `S`, `D_IN`, `D_OUT` red dimension arrows | Annotated plan view | All four geometry inputs at once |
| Planar Inductors | Rendered equation plate, `Lmw = K1·µ1·n²·d_avg / (1 + K2·ρ)` | Formula plate | The model in use, as typeset maths rather than a code line |
| Thermal Management | Package on a board in section, with a `Tj` leader pointing into the die | Annotated section | Where junction temperature is measured, versus case and board |
| Thermal Management | 3D heatsink render | Render, decorative | Nothing |
| Embedded Resistors | Plan view with `L` and `W` dimension arrows over a three-colour stack | Annotated plan view + colour key | Length and width, plus a legend mapping blue = copper contact area, orange = material overlap, grey = resistor |
| PDN Calculator | 3D render of planes, traces and via barrels | Render, decorative | Nothing |
| Wavelength Calculator | Sine wave on x/y axes with λ dimension arrows for full and half wave | Labelled plot | What λ measures on a waveform |
| Wavelength Calculator | Formula plate, `λ = c / (f · √Er_eff)` | Formula plate | The model |
| XL-XC Reactance | Photograph of an electrolytic capacitor and a chip inductor | Photo, decorative | Nothing |
| XL-XC Reactance | Formula plate, `Xc = 1/2πfC`, `Xl = 2πfL`, `f = 1/2π√LC` | Formula plate | The three models on the tab |
| PPM-XTAL | Photograph of a crystal can | Photo, decorative | Nothing |
| Ohm's Law | The Ohm's law wheel — a twelve-segment colour disc, quadrants for I, E, P, R, each holding three rearrangements | Reference wheel | Every rearrangement of V = IR and P = VI in one glance |
| Ohm's Law | LED bias pictorial — a 3D render of supply, chip resistor and LED in a chain | Render, semi-labelled | The series topology, loosely |
| Bandwidth & Max Conductor Length | none | — | — |
| Mechanical Information | none (drill chart and screw-thread tables instead) | — | — |
| Conversion Calculator | none inline; buttons open separate chart windows (SI Prefixes, dBm Chart, Capacitor µF-nF-pF, PCB Design Rules, Resistor calculator) | Pop-out reference charts | — |

### What Saturn is actually doing, as a method

Seven distinct devices, in descending order of how much they earn their space.

1. **Labelled cross-section keyed to the field names.** The single most valuable one. Every symbol in the drawing is a field label, and vice versa; the geometry question is answered without prose.
2. **Mode-switching geometry.** One drawing slot that redraws when the structure selector changes, so the picture is never lying about which of six structures you are solving.
3. **Annotated plan view with dimension arrows.** For anything concentric or nested — vias, padstacks, spirals — where words genuinely cannot disambiguate "inner diameter".
4. **Formula plate.** The governing equation typeset beside the answer, so the model is visible rather than buried in a footnote.
5. **Colour key.** Where a drawing carries more than one material, a legend maps colour to material.
6. **Reference wheel or chart.** Not a diagram of the input, a lookup device in its own right — the Ohm's law wheel is the example.
7. **Photographs and 3D renders.** Four tabs carry these. They label nothing and teach nothing; they are subject-setting decoration. **We should not copy this one.**

Saturn also leans on `? Help` and `Information` buttons that open text panels — a fallback for what the drawing could not carry.

## Part 2 — What this tool already has

Twenty-three of the twenty-six cards already carry an inline SVG. The three without are `nb` (number bases), `rt` (ratio units) and `cv` (conversions), which are unit converters with nothing geometric to draw, so the coverage gap is not "cards with no picture".

The real gap is **within** the cards: several drawings are static while the card offers a selector that changes the geometry, and several non-obvious parameters appear in the fields but nowhere in the drawing.

| Card | Existing drawing | Gap |
| --- | --- | --- |
| `z` Single-ended Z0 | One static picture showing microstrip and stripline side by side | The selector offers **five** structures — microstrip bare, microstrip covered, stripline centred, stripline offset, coplanar over ground. Three are never drawn, and `Cover εr`, `Far plane distance` and `Gap to ground` appear as fields with no geometry behind them |
| `dp` Differential pair | One static edge-coupled microstrip | Selector offers edge-coupled microstrip **and** stripline; the stripline case is undrawn |
| `tw` Trace width | One trace cross-section | External versus internal is a selector and changes the answer by roughly half; the drawing does not distinguish them |
| `via` Via | Barrel cross-section | `Pad dia`, `Antipad dia`, `Aspect ratio limit` and `Stub length` are all undrawn — exactly the four that need a picture. Saturn devotes two diagrams and a separate mode to this |
| `re` Reactance | Parasitic schematic (C with ESL/ESR, L with DCR and winding C) | The schematic is good, but the *behaviour* — the V-shaped impedance curve with the minimum at SRF — is what the card is for and is not shown |
| `ac` Error budget | Divider with tolerance bands | `TCR`, `T min`, `T max`, `T nominal` and `Ageing` are the substance of the card and have no visual; the band does not widen with temperature |
| `pad` PI, T and L pads | PI and T topologies | The **L** pad is offered in the fields (`Second impedance`) but not drawn |
| `sp` Series / parallel | Resistor chains | The component selector switches to capacitors and inductors; symbols stay resistors |
| `fu` Fusing current | Trace cross-section | `Onderdonk multiplier` and `Fault duration` have no visual; the current-versus-time trade is the whole point |
| `xc` Load capacitance | Crystal with two load caps | Worth confirming that stray C is labelled where it physically sits |
| `ohm`, `sp`, `div`, `led`, `th`, `pdn`, `awg`, `bat`, `pp`, `wl`, `vs`, `spc`, `ee`, `flt` | Adequate | The filter card already redraws its topology and plots its response, which is the mode-switching pattern done right — it is the template for the rest |

## Part 3 — The plan, and what was built

Three tiers, ordered by how much confusion each removes per drawing. All three were built.

### Tier 1 — Mode-switching geometry (9 drawings, 4 cards)

Follow the pattern `drawTopology()` already established on the filter card: a single SVG slot, redrawn from the selector. This is the highest-value work because a static drawing beside a five-way selector is not merely unhelpful, it is **actively wrong four times out of five**.

- `z` — five cross-sections, one per structure. Each labels `w`, `h`, `t`, `εr`, and adds the symbol unique to that structure: cover εr and cover thickness on covered microstrip, both plane distances on offset stripline, gap `g` and ground pour on coplanar. Fields that do not apply to the current structure are already inert; the drawing should agree with them.
- `dp` — two cross-sections, edge-coupled microstrip and edge-coupled stripline, both labelled `W`, `S`, `H`, `εr`.
- `tw` — two variants, external (one exposed surface, convection) and internal (buried, conduction only), which is the physical reason the IPC curves differ.

### Tier 2 — Parameters that exist only as words (7 drawings)

- `via` **stub length** — section view of a signal entering on layer 1, exiting on an inner layer, with the unused barrel below marked as the stub, plus `aspect ratio = board thickness / drill` annotated on the same drawing.
- `via` **pad and antipad** — plan view, concentric, in the Saturn style: drill, plating, pad, antipad, outward.
- `re` **impedance versus frequency** — the V curve, capacitive slope down, inductive slope up, minimum at SRF equal to ESR. This is a plot, so it follows the dataviz rules already applied to the filter graph: 2px curve, hairline grid, crosshair on hover, no legend for a single series.
- `ac` **tolerance band over temperature** — nominal ratio as a centre line, the band widening from tolerance alone at T nominal to tolerance plus TCR plus ageing at the temperature extremes.
- `pad` **L pad** — third topology added to the existing PI and T drawing, showing the asymmetry that the second impedance field implies.
- `fu` **current versus fault duration** — the Onderdonk curve, log-log, with the chosen duration marked, and the multiplier shown as a vertical scaling of the curve.
- `sp` — swap the resistor symbols for capacitor or inductor symbols with the selector. Cheap, and removes a small persistent lie.

### Tier 3 — Saturn devices worth adopting (3 items)

- **Formula plates.** A typeset equation beside the results on the cards where the model is the interesting part — `z`, `ee`, `fu`, `wl`, `re`. Currently these are prose in the notes. A plate is scanned, prose is read.
- **Colour key.** Where a drawing carries more than one material — the impedance cross-sections in particular, with copper, dielectric, cover and plane — a two-line legend beside it, following the embedded-resistor pattern.
- **Ohm's law wheel** on the `ohm` card. Genuinely useful as a lookup device, and the one piece of Saturn's decoration that carries information.

### Explicitly not adopted

- **Photographs and 3D renders.** Four Saturn tabs carry them; they label nothing. They would also break the self-contained-file rule cheaply only as large base64 blobs.
- **The etch-factor trapezoid.** Saturn draws the trapezoidal etched cross-section because it models etch factor. This tool does not, so drawing a trapezoid would claim an accuracy the maths does not have. If etch factor is ever modelled, the drawing follows then.

### How the work is done

Every drawing is an inline SVG in `build_page.py`, using the existing `.schem` class and the `wire` / `dot` / `opt` stroke classes, so all of it inherits the theme tokens and works in light and dark without a second palette. Mode-switching drawings become small functions beside `drawTopology()`, called from the card's `calc*` function so the picture and the answer can never disagree. No new dependencies, no images, no network — the page stays a single self-contained file.

Testing: the node suites gain a check per switching card that the rendered SVG changes with the selector and that every symbol drawn corresponds to a field on that card, which is the same invariant style used for the shared board settings.

## Current state

Everything in Part 3 is implemented, and the page rebuilds to about 346 KB. Thirty-three diagrams are checked by the geometry lint and all are clean.

- **Tier 1** — `drawZ`, `drawDiff` and `drawTrace` render nine mode-specific cross-sections, called from the top of their `calc*` functions so the picture cannot lag the answer.
- **Tier 2** — `drawVia` (section plus concentric plan view, marking the stub when one is given), `drawSP` (symbols follow the component selector), `drawPad` (the L pad added), and three curves: self-resonance on the reactance card, fusing current against fault duration, and the divider error band across temperature.
- **Tier 3** — formula plates on thirteen cards, a line-style key on the cross-sections, and the Ohm's law wheel, generated at build time rather than hand-drawn.
- **Etch factor** — not modelled, and the trace cards now say so.

Two conventions came out of the build and are worth keeping. **Prose never goes inside an SVG**: `<text>` cannot wrap, so anything longer than a symbol lands in a `.key` paragraph underneath, and the lint enforces it by catching labels that run past the viewBox. **A second series is told apart by dash and by its own direct label, never by hue**, so the plots survive any colour vision and a monochrome print without needing a validated two-colour palette.

## Verification

- `python C:\Auterion\Tools\claude\scratch\eecalc_diagram_check.py` — geometry lint over all thirty-three diagrams: every coordinate inside its viewBox, no two horizontal labels overlapping, and each switching drawing genuinely differing between modes and carrying the symbol unique to that mode. Confirmed able to fail by injecting an out-of-frame label and an overlapping one.
- `eecalc_diagram_tests.js` — 24 assertions that each plot is drawn when the card has enough to say and cleared when it does not, that the second series is dashed rather than recoloured, and that the plates are present.
- The eleven existing node suites and `eecalc_check_page.py` all pass unchanged.
- **Not** checked by eye in a browser this session: the Chrome extension refused `file://` URLs, so the geometry lint stands in for the look-at-it step. It catches overflow and collisions, not ugliness.

## Files touched

- `C:\Auterion\Tools\EE_Calculator\Diagram_Plan.md` — this document.
- `C:\Auterion\Tools\EE_Calculator\build_page.py` — all the drawing code and the HTML hosts.
- `C:\Auterion\Tools\EE_Calculator\README.md` — the diagram and plot paragraphs.
- `C:\Auterion\Tools\claude\scratch\eecalc_diagram_check.py` — new geometry lint.
- `C:\Auterion\Tools\claude\scratch\eecalc_diagram_tests.js` — new node suite.
- `C:\Auterion\Tools\claude\scratch\eecalc_mkharness.py` — the id scrape now keeps only literal ids, because the page builds `id="' + hostId + '-cursor"` in JS and the stub choked on it.
- `C:\Auterion\Tools\EE_Calculator\SaturnPCB\` — the nineteen source screenshots for Part 1.

## How to continue

The ask was for all three tiers so the whole set could be judged together and then simplified. **Simplification is the expected next step**: open the page, decide which drawings and plates earn their space, and delete rather than add. Candidates for cutting, in the order I would consider them: the plates on `spc` and `th`, which restate a one-line note; the key on `via`, since the dashed antipad is fairly self-evident; and the Ohm's law wheel, which is a reference device rather than an explanation of a parameter.

To change a drawing, patch `build_page.py` with a script written to the scratchpad (never a heredoc — backslash escapes in a non-raw Python string have silently corrupted anchors several times), regenerate with `python build_page.py`, then run the geometry lint and the node suites.

The three long-standing failures in `eecalc_planned_tests.js` are resolved. All three were wrong expectations rather than defects: two demanded more significant figures than the page prints (8.337 W, 16.1 K/W), and the third assumed the whole 3 A ran through a single via instead of splitting across the bank of ten, so it expected 9.73 mW where 973 µW is correct. The page was right in each case; the assertions were corrected, and the via card's `At 3 A` row now reads `At 3 A shared across the 10`, because the ambiguity that misled the test would mislead a reader too.

## Decisions taken

- **Build all three tiers**, then simplify from a complete page rather than guessing which drawings earn their space in the abstract. Asked and answered on 2026-09-10.
- **Keep rectangular trace cross-sections and state the idealisation.** Etch factor is not modelled, so drawing a trapezoid would claim accuracy the maths does not have; instead the trace cards carry a one-line note that real etched copper is trapezoidal and a rectangular model reads slightly optimistic on narrow traces. Asked and answered on 2026-09-10.
