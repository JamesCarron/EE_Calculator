# KiCad PCB Calculator — feature comparison and proposals

## How this was sourced

Two sources, because the published documentation lags the shipping build. The **feature set** came from the installed binary at `C:\Program Files\KiCad\10.0\bin\_pcb_calculator.dll`, by extracting the RTTI class names — `PANEL_*` for the calculators and the transmission-line type names — which gives exactly what version 10.0 ships rather than what the 9.0 manual describes. The **models** came from the source at `https://gitlab.com/kicad/code/kicad`, under `pcb_calculator/`, read through the GitLab raw endpoint.

**Licence.** KiCad is GPL-3.0. Everything proposed below is written as *implement the published model or standard ourselves*, not as *copy KiCad's code*, and the formulas cited are from the underlying standards and literature rather than from KiCad's implementation. Flagging it because it is relevant to how any of this gets built; the decision is yours.

**A second licensing-shaped issue, on content rather than code.** IEC 60664-1 is a paywalled standard and its clearance and creepage tables are the substance of that calculator. KiCad embeds them. We would need them too, from somewhere. This is the same situation that made us choose IPC-2221 over the paywalled IPC-2152 for trace width.

## What KiCad ships

Fifteen panels in v10.0.

| Panel | What it does |
| --- | --- |
| Regulators | Feedback-divider resistors for a linear regulator; standard `Vout = Vref(1 + R2/R1)` and a 3-terminal form carrying the adjust-pin current |
| RF attenuators | PI, Tee, Bridged Tee and resistive splitter, with **unequal input and output impedances** |
| E-series / R calculator | Best 2, 3 or 4 resistor series-parallel combination for an **arbitrary target**, over E1 to E24, with values excludable |
| Color code | Resistor band decoding |
| TransLine | Nine line types, each with **loss modelling** — see below |
| Via size | Plated through-hole electrical and thermal properties |
| Track width | IPC-2221 |
| Electrical spacing | **IPC-2221 and IEC 60664** as separate sub-panels |
| Board classes | IPC-6011 performance classes and IPC-6012 board types, as reference |
| Fusing current | Energy-balance model **including the latent heat of fusion** |
| Cable size | AWG geometry, temperature-corrected resistance, ampacity from a current density, drop, loss, and the frequency at which skin depth equals the wire radius |
| Galvanic corrosion | Electrochemical potential difference between metals in contact |
| Wavelength | Free-space and in-medium wavelength |

The TransLine panel is the deepest part of the tool. Nine types — microstrip, coplanar, grounded coplanar, rectangular waveguide, coax, coupled microstrip, coupled stripline, stripline, twisted pair — and for each it reports not just Z₀ and ε_eff but **conductor loss, dielectric loss and skin depth**, taking `tan δ`, conductor resistivity, surface roughness and both permeabilities as inputs. The coupled types report even and odd mode impedances, differential and common-mode impedance, and the coupling coefficient. It also runs in both directions: analysis (geometry → impedance) and synthesis (impedance → geometry).

## Where we stand against it

| Capability | KiCad | Us |
| --- | --- | --- |
| Trace width, IPC-2221 | yes | yes |
| Conductor spacing, IPC-2221 | yes | yes |
| **Clearance and creepage, IEC 60664** | yes | **no** |
| Via properties | yes | yes, plus stub resonance and aspect ratio |
| Fusing current | energy balance with latent heat | Onderdonk |
| Wavelength | yes | yes, plus knee frequency and critical length |
| AWG / cable | yes | yes, plus round-trip handling and two ampacity bases |
| Attenuators | PI, T, bridged T, splitter; unequal impedances | PI, T, L |
| E-series | **arbitrary target from 2–4 resistors** | ratio search for a divider, and nearest value |
| Regulator feedback divider | yes | **no**, only a generic divider |
| Microstrip / stripline / CPWG Z₀ | yes | yes, five structures |
| Differential pair | coupled microstrip and stripline, full even/odd | yes, edge-coupled, Zdiff and Zodd/Zeven |
| **Transmission-line losses** | conductor, dielectric, roughness | **none** |
| **Coax, twisted pair, waveguide** | yes | **no** |
| **Galvanic corrosion** | yes | **no** |
| Colour code, board classes | yes | no, deliberately |
| Component tolerance budget | no | yes |
| Filters, reactance, self-resonance | no | yes |
| Junction temperature, PDN | no | yes |
| Battery, crystal load, ppm | no | yes |

The two tools have genuinely different centres of gravity. KiCad is a PCB-fabrication and RF calculator with no component-behaviour side at all — nothing on filters, self-resonance, tolerance stack-up, thermal or power integrity. We have all of that. What KiCad has and we do not is **loss modelling, cable and connector work, and the safety standard**.

## Proposals

Ranked by what they would actually be used for here, not by how hard they are.

### 1. IEC 60664 clearance and creepage

The strongest case, because **our own spacing card already tells the user this is missing**. Its note reads: "Clearance is not creepage… for mains isolation it is usually the larger of the two and the one that decides your layout. IPC-2221 does not cover creepage; IEC 60664 does." We diagnose the gap and then leave the user to go elsewhere.

Inputs: working voltage (RMS or DC), rated impulse voltage or the overvoltage category and mains supply voltage to derive it, pollution degree 1–3, insulation material group I–IIIb, functional/basic/reinforced insulation, and altitude. Outputs: minimum clearance and minimum creepage, with reinforced insulation taking double the basic clearance, and the altitude multiplier applied above 2000 m.

Relevant here beyond mains: a 12S pack sits near 50 V, and pollution degree and material group drive creepage well before the voltage looks dangerous.

**Blocker:** the tables are the calculator, and IEC 60664-1 is paywalled. Nothing to build until we have a legitimate source for them.

### 2. Transmission-line loss

We compute Z₀, ε_eff, delay and per-unit-length L and C, and stop. For anything carrying RF — a video downlink, GPS, a cellular modem — the number that decides the design is **dB per unit length**, and we do not produce it.

Three additions to the impedance card, all standard:

- Skin depth and surface resistivity: `δ = sqrt(ρ / (π f μ))`, `Rs = ρ/δ = sqrt(π f μ ρ)`.
- Conductor loss: `αc ≈ 8.686 · Rs / (Z₀ · w)` dB per unit length, with the Hammerstad–Jensen roughness correction `Kr = 1 + (2/π)·arctan(1.4·(Δ/δ)²)` — roughness typically doubles the conductor loss on standard foil by a few GHz, which is exactly the kind of factor that makes a link budget wrong.
- Dielectric loss from the loss tangent: microstrip `αd = 27.3 · (εr(ε_eff − 1)) / (sqrt(ε_eff)(εr − 1)) · tanδ / λ₀`, stripline `αd = 27.3 · sqrt(εr) · tanδ / λ₀`, both dB per unit length.

Needs two new inputs, `tan δ` and copper roughness, both of which the fabricator quotes. The card would then report loss at the given frequency and, usefully, the length at which the budget hits a stated dB.

### 3. Resistor substitution from an arbitrary target

We search E-series **pairs for a divider ratio**, and suggest a nearest standard value. What we cannot answer is "I need 3.14 kΩ and I have E24 in the drawer" — the answer being two or three parts in series or parallel. KiCad searches 2, 3 and 4 resistor combinations.

Two resistors covers almost every practical case and is a trivial search: for each pair in the series, evaluate `Ra + Rb` and `Ra·Rb/(Ra+Rb)`, keep the closest few, report the error in percent and in ppm. Three resistors is a bigger search but still cheap over one decade. It fits naturally on the existing Tolerance tab, and it should carry the warning KiCad's does not: **combining parts stacks their tolerances**, so two 1 % resistors in series give a worse result than one 0.1 % part, which is precisely what our tolerance budget card exists to compute.

### 4. Regulator feedback divider

`Vout = Vfb · (1 + Rtop/Rbot)`, plus the adjust-pin or feedback bias term `Ibias · Rtop` for the three-terminal case. Ten lines of arithmetic, but the card earns its place through what it reports around the answer:

- The **actual** Vout once both resistors are rounded to E-series values, which is the number that matters and is usually not the one asked for.
- Divider current against the feedback pin's bias current — the classic error, and the reason a high-value divider shifts the output.
- Quiescent drain from the divider, which on a battery product is a real standby-budget line item.

Our divider solver already does the arithmetic; this is the regulator framing plus those three checks.

### 5. Coax and twisted pair

Cable assemblies are a real part of the work here, and neither is on any of our cards.

- Coax: `Z₀ = (138/sqrt(εr))·log₁₀(D/d)`, `C' = 2πε/ln(D/d)`, `L' = (μ/2π)·ln(D/d)`, velocity factor `1/sqrt(εr)`, and the TE₁₁ cutoff above which it stops being single-mode, `f ≈ c / (π·sqrt(εr)·(D+d)/2)`.
- Twisted pair: `Z₀ ≈ (120/sqrt(ε_eff))·arccosh(D/d)`, with ε_eff depending on the twist rate and the jacket — genuinely approximate, and it must say so on the card.

### 6. Fusing current: report both models

Ours is Onderdonk. KiCad's is an energy balance: melt the copper from ambient, including the **latent heat of fusion** at 205 kJ/kg, against I²Rt with the resistivity averaged between ambient and melting. The two differ in an interesting way — **Onderdonk integrates the resistivity properly but ignores the latent heat; KiCad includes the latent heat but uses a mean resistivity.** Neither is strictly better.

The honest thing is to report both and show the spread, in the same spirit as the covered-microstrip bracket. If they agree, the answer is trustworthy; where they diverge, the user learns something real about how rough a fusing estimate is. KiCad also estimates a thermal time constant and warns when the duration approaches it, which is a better-founded version of our flat "valid to about 5 seconds".

### 7. Two small additions

- **Skin-limited frequency on the AWG card.** `f = ρ / (π r² μ)` is the frequency at which skin depth equals the wire radius — above it the centre of the conductor is carrying nothing. One row, and it answers "can I use this wire at this frequency" directly.
- **Galvanic corrosion.** An anodic-index table and the difference between two selected metals, against the usual thresholds: under about 0.15 V for harsh or outdoor environments, 0.25 V for normal, 0.50 V for controlled. Directly relevant to connectors, enclosure hardware and anything flying in weather.

## Not proposed

- **Colour code.** Every phone has one, and nobody reads bands off a reel.
- **Board classes.** A static IPC-6011/6012 reference table with no calculation in it.
- **Rectangular waveguide.** No plausible use here.
- **E-series display.** A table of series values; ours are already offered wherever they are relevant.
- **Transmission-line synthesis** (impedance → geometry). Tempting, but our cards deliberately solve in the direction the model is valid in, and inverting an empirical fit outside its range is how tools end up quietly wrong. The existing approach — compute, then state the validity window — is the more honest one.

## Files

- `C:\Auterion\Tools\EE_Calculator\KiCad_Feature_Comparison.md` — this document.
- Source read: `https://gitlab.com/kicad/code/kicad`, `pcb_calculator/` — `resistor_substitution_utils.cpp`, `transline_ident.cpp`, `calculator_panels/panel_fusing_current.cpp`, `calculator_panels/panel_cable_size.cpp`, `iec60664_help.md`, `fusing_current_help.md`.
- Feature set read from `C:\Program Files\KiCad\10.0\bin\_pcb_calculator.dll`; the extraction is in the session scratchpad and can be redone with a strings dump filtered for `PANEL_`.

## Decisions taken, and what was built

Asked and answered on 2026-09-15.

- **Build transmission-line loss and the dual fusing model.** Both are done.
- **Use KiCad's embedded IEC 60664-1 tables.** The licensing question was flagged and the user decided; the tables were transcribed mechanically rather than retyped, because a typo in a safety table is not something a unit test would catch. `eecalc_iec60664_transcribe.py` does the translation and is re-runnable.
- **Close the gaps in the power/current group and in RF attenuators**, raised after the first pass through KiCad's grouped tabs. Done, and the gaps were real.

### What is now in the tool

**Attenuators, rewritten.** Five topologies against KiCad's four, selected from a dropdown with the drawing following the selection. **PI and T now take a source and a load impedance separately** and reduce exactly to the symmetric formulas when they are equal, which is one of the tests. Bridged T and the resistive splitter are new. The minimum attenuation between unequal impedances is enforced on every topology, not just the L pad. What stock parts deliver is now a full transducer-loss calculation solved from the node equations, so it stays correct for the bridged T and for unequal impedances, where the old symmetric shortcut did not apply.

Two bugs surfaced while testing this, one of them pre-existing:

- **The L pad silently ignored the attenuation you asked for.** A matched L pad has exactly one geometry between two impedances and therefore exactly one loss — the minimum the ratio allows. The old card accepted a dB figure and quietly discarded it. It now reports the attenuation as fixed and says so.
- The resistive splitter's third arm was modelled into ground rather than into its terminated third port, giving 12 dB instead of 6.02 dB. Caught by hand-checking the node voltages.

**IEC 60664-1 clearance and creepage**, beside the IPC-2221 card, closing the gap our own spacing note complained about. Overvoltage category, pollution degree, material group, board-versus-other construction, field homogeneity and altitude; it reports the rated impulse withstand, clearance, creepage and the minimum groove width, with the reinforced rule stepping the preferred series rather than doubling. Creepage is floored at the clearance, because a surface path cannot be shorter than the air path beside it. The classic values come out right: 2.5 kV and 1.5 mm at 230 V category II pollution degree 2, 3.0 mm reinforced, 3.6 mm creepage at pollution degree 3.

**Transmission-line loss** on the impedance card: skin depth, surface resistivity, conductor loss with the Hammerstad roughness correction, dielectric loss from the loss tangent, the total in dB/m and dB/in, and the length that costs 1 dB and 3 dB. A 50 ohm FR-4 microstrip at 1 GHz comes out at 0.19 dB/inch, which is the figure everyone quotes. The conductor term is stated as a floor, because the wide-strip approximation ignores edge current crowding.

**Fusing current under both published models.** Onderdonk integrates the resistivity across the temperature rise but ignores the energy of melting; the energy balance includes the latent heat of fusion but uses a mean resistivity. They differ by about 11 % on a 1 mm trace, and the card now shows both and the spread, which is the honest width of a fusing estimate.

**Trace width** now gives the width the *other* layer would need for the same current, so the routing question is answered without flipping the selector. The ratio is 2 to the power 1/0.725, about 2.6 times, which is the test.

**Via** now reports what it does to an edge: the reactance a given rise time sees, as a fraction of the line impedance, and how much the via's capacitance slows that edge.

### Still not built

- The **resistor substitution solver** and the **regulator feedback divider**, both proposed and neither selected.
- **Coax and twisted pair**, proposed and not selected.
- **Galvanic corrosion** and the **skin-limited frequency on the AWG card**, proposed and not selected.
- Colour code, board classes, rectangular waveguide, E-series display and transmission-line synthesis, all deliberately declined above.

### Verification

Twenty node suites, of which three are new: 76 assertions on the attenuators, 30 on IEC 60664 and 22 on loss. The IEC suite checks against values published in the standard rather than against the source they were transcribed from, plus monotonicity properties — a worse pollution degree or material group can never need less creepage. The loss suite checks the physical trends: conductor loss as the square root of frequency, dielectric loss linear in it, so the dielectric term eventually dominates. The load check, the diagram lint and the page check all pass.
