# Pad capacitance, plane cutouts, and an EM backend

Two proposals that arrived together. They are worth separating, because the first is a card and the second is an architecture decision, and the second is a much bigger commitment than it looks.

## Part 1 — Pad capacitance to each reference plane

### What already exists

The via card computes the capacitance of a via pad against the antipad in the plane it passes through, with the classic first-order form `C ≈ 1.41·εr·H·d_pad/(d_anti − d_pad)`. That is a different geometry from the one proposed: it is a pad sitting *inside* a hole in the same layer, which is nearly coaxial. What is missing is a **surface pad looking down at the planes below it**, and what changes when you void one of those planes.

Nothing else in the tool covers it. The impedance cards model an infinite uniform trace, not a local blob of copper.

### Why it matters

A 0402 pad is about 0.3 mm². Over 0.1 mm of FR-4 that is roughly 0.11 pF to the plane beneath. At 100 MHz that is 14 kΩ and irrelevant; at 6 GHz it is 240 Ω across a 50 Ω line and very much not. It is why RF pads get the plane voided under them, and the question the designer actually has is **"is the void worth it"** — which is exactly what a per-plane breakdown answers, because voiding the nearest plane often helps far less than expected once the next plane down picks up the field.

### The model

Reuse what is already validated rather than introducing a new approximation. A pad is a very wide, very short microstrip, so the per-unit-length capacitance already computed by Hammerstad–Jensen for a strip of width w at height h in εr, multiplied by the pad length, gives the capacitance **with the two long edges properly fringed**:

```
C' = t_pd / Z₀        (already computed on the impedance card)
C_pad ≈ C' × length
```

The two *ends* are not fringed by that model, so the figure reads slightly low — by roughly the end-fringe of a w-wide strip, which matters most for a near-square pad. The card should say so rather than hiding it. The pure parallel-plate value `ε₀εr·A/h` is also worth showing as an explicit floor, because the gap between the two is a good indication of how much of the answer is fringe rather than plate — for a small pad over thin dielectric, fringe is most of it.

### The cutout is where this gets hard, and that is the interesting part

With a full plane under the pad, the above is solid. With a void in the plane under the pad, it is not, and **no closed form I would trust covers the interior of the problem**:

- **Void much larger than the pad.** The pad barely sees that plane; the reference becomes the next plane down, and the capacitance to the voided plane is a rim-fringe term that falls off slowly with clearance.
- **Void smaller than the pad.** Most of the pad still faces copper; the reduction is roughly proportional to the missing area, plus a rim effect.
- **Void comparable to the pad.** Genuinely three-dimensional, and the answer depends on the rim geometry.

The tool's existing convention for this situation is the **covered-microstrip bracket**: give the two computable limits and refuse to invent the curve between them. That applies exactly here.

- Upper bound: no void, full capacitance at that plane's height.
- Lower bound: void large enough that the plane contributes nothing, so the reference is the next plane down.

A real void sits between, near the lower bound once the clearance is a couple of dielectric heights. The card would report the bracket per plane, the total with all planes in parallel (they are all AC ground), and the resulting `X_C` at a stated frequency, plus the two consequences the tool already knows how to express: the local impedance dip `sqrt(L'/(C' + C_pad/l))` and the edge degradation `2.2·C·Z₀/2`.

### What the card would take

A pad, and a small stackup: the height and cutout state of each plane below it. Two or three planes covers essentially everything real — signal on L1, ground on L2, ground or power on L3. A full editable stackup is more UI than any card here has, and I would not start there.

### Honest limits, stated on the card

The bracket is the headline limit. Beyond it: solder mask is ignored, the pad is treated as isolated rather than as part of a trace, and a pad on an inner layer with planes both above and below needs both contributions. None of these is hard to add once the shape of the card is settled.

## Part 2 — an openEMS backend

### The tension

`EE_Calculator.html` is one self-contained file. No server, no network, no dependencies, opens from `file://`, answers instantly. That is not incidental — it is why it gets used, and the constraint is written into its CLAUDE.md.

openEMS is a native FDTD solver driven from Python, with a meshing step and run times in minutes. Adding it as a backend to this page would mean every user needs a Python environment and a compiled solver in order to open a tool that is currently a double-click, and the ninety-odd per cent of uses that are arithmetic would pay for the ten per cent that are not.

That does not mean no. It means picking where it lives.

### Four options

**A. A separate tool.** `Tools\em_bench\`, with a local Python backend on an ephemeral port and a Browse button, exactly as the Altium tools are built. EE_Calculator stays untouched and instant; the EM tool does geometry, meshing, solving and plotting properly, which is a real piece of software rather than a card. The two can hand geometry to each other.

**B. A backend bolted onto EE_Calculator.** Fastest to a demo, and it costs the single-file property for everyone. I would not do this.

**C. The page exports a solver script.** EE_Calculator stays self-contained and gains a "Download openEMS script" button on the impedance, via and pad cards: it writes the Python that models the geometry you just entered. You run it where you like. No server, no dependency, no change to what the page is — the page becomes a front end that writes a model. Cheap, and useful immediately.

**D. Use openEMS offline to validate the closed forms, and bake the findings in.** Not a runtime feature at all. Sweep w/h, εr, frequency and via geometry, compare Hammerstad–Jensen, the IPC ampacity fit and the first-order via formulas against FDTD, and record where they diverge. Every validity note in the tool currently repeats a claim from the literature — "valid for 0.01 ≤ w/h ≤ 100". After this they could say *measured* things: within 2 % over this box, drifting to 8 % here, and here is the plot. That is the single highest-value use of an EM solver for this tool, and it needs no backend at all.

### A technical caveat worth raising before any of this

**openEMS is FDTD, and FDTD is the wrong tool for a pure capacitance number.** It is excellent for S-parameters, loss, resonance and anything with propagation — traces, vias, stubs, the things the message mentions. Extracting a static capacitance from it means running a low-frequency excitation and de-embedding, which is slow and fiddly for a quantity a quasi-static solver gets directly. If pad capacitance with cutouts is the immediate goal, a **capacitance extractor** such as FasterCap is the better-matched tool, and it is far cheaper to run. If the goal is EM-simulated traces and vias generally, openEMS is right.

Both can coexist; they answer different questions.

### Licence

openEMS is GPL-3.0; FasterCap is also open source under a GPL-family licence. Flagging that they exist and what they are, as relevant to how any of this gets distributed. The decision is yours.

## Decisions taken

Asked and answered on 2026-09-15. The user chose, against each of my three recommendations: **integrate openEMS as a submodule and simulate the pad rather than building the closed-form card**, put the **backend inside EE_Calculator**, and use **openEMS for everything** including the static capacitance. Recorded here because the reasoning for the alternatives is above and should not be re-litigated by accident.

## Current state

**Done.**

- openEMS pinned as a git submodule at `vendor/openEMS-Project` (commit `04e054d`), with the `openEMS` and `CSXCAD` nested modules initialised so the Python interface source is present to write against.
- `em/model.py` — the part with the physics in it. A geometry spec (pad, permittivity, loss tangent, a stack of planes each with an optional circular void), validation, mesh sizing, a run-cost estimate, and generation of a standalone openEMS script that drives a lumped port between the pad and a chosen plane and extracts C from Im(Z11).
- 43 tests in `eecalc_em_model_tests.py`, all passing. They run **without openEMS installed**, which is the point of keeping generation separate from solving.

Two things the tests caught that are worth knowing:

- **Meshing by wavelength alone is wrong here.** Lambda/50 at 10 GHz in FR-4 is 289 um, and the dielectric under the pad is 100 um — less than one cell across the gap that *is* the capacitor. The cell size is now the smaller of the wavelength criterion and what the geometry needs (eight cells across the thinnest dielectric, ten across the pad, ten across the smallest void). For the reference pad that is 12.5 um rather than 289.
- **The run-cost estimate was insensitive to the fine mesh**, because it counted the whole domain at the coarse cell. FDTD cost is cells times timesteps and the timestep is bounded by the *smallest* cell, so halving the cell costs about sixteen times. The estimate now counts the fine region separately and reports a cost relative to a plain 0402 pad: a thinner dielectric is 4x, a voided two-plane stack 14x, a 20 mm pad over 100 um is 15000x and flagged as heavy before anyone starts it.

**Blocked, and why.** There is no openEMS runtime on this machine and no way to build one here: no CMake, no C++ compiler, and openEMS additionally needs VTK, CGAL, Boost and HDF5. conda-forge has no `openems` package, so pixi cannot fetch it. The submodule therefore pins the *source* and gives provenance, but the runtime has to come from the project's prebuilt Windows release — and those pair with particular Python versions:

- **v0.0.36**, the current stable release (October 2023), 48 MB, ships wheels for Python 3.10 and 3.11.
- **v0.37.0-rc2**, a release candidate (September 2024), ships wheels for Python 3.13 and 3.14.

Our pixi environment is pinned to Python 3.12, which matches neither. So the environment has to move, and which way it moves depends on whether we take the stable release or the candidate. That is the open decision, and it is the reason the backend and the page integration are not built yet — they sit on top of that environment.

**Not started, pending the above:** the backend server (ephemeral port, health endpoint, queued runs), the pad card and its Simulate action, the launch `.bat`, and graceful degradation so the page still works by double-click with no backend present.

## Open questions

Which openEMS release and Python version to pair, and whether to pull the 48 MB runtime into `user_data/`. Put to the user rather than assumed; the answer is recorded above once given.
