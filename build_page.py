"""Generate EE_Calculator.html - a self-contained tabbed EE calculator page.

Written 2026-08-26.

All calculator logic is in-page JavaScript because the page is interactive at
runtime with no server; Python here is only the build harness. The house
stylesheet and its two webfonts are inlined via the local `theme_inline`
module, so the output works offline, opened straight from the filesystem.

Verified by: building and exercising every tab in a browser (divider results
cross-checked by hand: 12 V, 10k/4k7 -> 3.837 V, 816.3 uA).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "EE_Calculator.html"

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EE Calculator</title>
<style>
  body { background: var(--a-bg); color: var(--a-ink); font-family: var(--a-font); margin: 0; }
  .wrap { max-width: 880px; margin: 0 auto; padding: 0 1.25rem; }
  header.site { padding: 2rem 0 1rem; }
  .eyebrow { font-size: var(--a-text-xs); letter-spacing: var(--a-tracking-eyebrow); text-transform: uppercase; color: var(--a-ink-muted); margin: 0 0 .35rem; }
  h1 { font-family: var(--a-font-display); line-height: var(--a-lh-heading); margin: 0; }
  .tabs { display: flex; flex-wrap: wrap; gap: .4rem; border-bottom: var(--a-border) solid var(--a-line); padding-bottom: .6rem; margin-bottom: 1.4rem; }
  .tabs button { font: inherit; font-size: var(--a-text-sm); color: var(--a-ink-secondary); background: var(--a-bg-subtle); border: var(--a-border) solid var(--a-line); border-radius: var(--a-radius-chip); padding: .4rem .85rem; cursor: pointer; }
  .tabs button:hover { color: var(--a-ink); border-color: var(--a-line-strong); }
  .tabs button[aria-selected="true"] { background: var(--a-link); color: var(--a-on-accent); border-color: var(--a-link); }
  .tabs button:focus-visible { outline: 2px solid var(--a-focus); outline-offset: 2px; }
  .serieswrap { margin-left: auto; display: flex; align-items: center; gap: .45rem; font-size: var(--a-text-xs); color: var(--a-ink-secondary); }
  .serieswrap select { font: inherit; font-family: var(--a-font-mono); color: var(--a-ink); background: var(--a-bg); border: var(--a-border) solid var(--a-line-strong); border-radius: var(--a-radius-sm); padding: .3rem .45rem; }
  .serieswrap select:focus-visible { outline: 2px solid var(--a-focus); outline-offset: 1px; }
  .subtabs { display: flex; flex-wrap: wrap; align-items: center; gap: .4rem; margin: 0 0 1.4rem; }
  .subtabs button { font: inherit; font-size: var(--a-text-sm); color: var(--a-ink-secondary); background: none; border: none; border-bottom: 2px solid transparent; padding: .35rem .2rem; margin-right: .7rem; cursor: pointer; }
  .subtabs button:hover { color: var(--a-ink); }
  .subtabs button[aria-selected="true"] { color: var(--a-ink); border-bottom-color: var(--a-link); }
  .subtabs button:focus-visible { outline: 2px solid var(--a-focus); outline-offset: 2px; }
  .subpanel { display: none; }
  .subpanel.active { display: block; }
  .panel { display: none; padding-bottom: 3rem; }
  .panel.active { display: block; }
  .panel h2 { font-family: var(--a-font-display); margin: 0 0 .3rem; }
  .panel p.hint { color: var(--a-ink-secondary); font-size: var(--a-text-sm); margin: 0 0 1.2rem; max-width: var(--a-measure); }
  .card { background: var(--a-bg-panel); border: var(--a-border) solid var(--a-line); border-radius: var(--a-radius); padding: 1.1rem 1.25rem 1.25rem; margin-bottom: 1rem; }
  .card h3 { margin: 0 0 .8rem; font-size: var(--a-text-body); }
  .cardrow { display: flex; flex-wrap: wrap; gap: 1rem 2.5rem; align-items: flex-start; }
  .cardrow .fields { flex: 1 1 20rem; }
  svg.schem { color: var(--a-ink-secondary); flex: 0 0 auto; max-width: 100%; }
  .diagram { flex: 0 0 auto; color: var(--a-ink-secondary); }
  .diagram svg { max-width: 100%; }
  /* the container sizes to plot + axis band, so the axis labels are never
     clipped into a nested scrollbar */
  .chart { margin-top: 1.1rem; cursor: crosshair; }
  .chart svg { display: block; max-width: 100%; }
  .chart:focus-visible { outline: 2px solid var(--a-focus); outline-offset: 3px; }
  .chart .grid { stroke: var(--a-line); stroke-width: 1; fill: none; }
  .chart .axis { stroke: var(--a-line-strong); stroke-width: 1; fill: none; }
  .chart .curve { stroke: var(--a-link); stroke-width: 2; fill: none; stroke-linejoin: round; }
  .chart .hair { stroke: var(--a-ink-muted); stroke-width: 1; }
  .chart .knob { fill: var(--a-link); stroke: var(--a-bg-panel); stroke-width: 2; }
  .chart text { fill: var(--a-ink-muted); font-size: 10px; font-family: var(--a-font-mono); }
  .chart text.read { fill: var(--a-ink); font-size: 11px; }
  .chart text.readlabel { fill: var(--a-ink-secondary); font-size: 10px; }
  svg.schem .wire { fill: none; stroke: currentColor; stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; }
  svg.schem .dot { fill: currentColor; stroke: none; }
  svg.schem .opt { stroke-dasharray: 4 3; }
  svg.schem text { fill: currentColor; stroke: none; font-family: var(--a-font-mono); font-size: 11px; }
  .fields { display: flex; flex-wrap: wrap; gap: .9rem 1.2rem; }
  .field { display: flex; flex-direction: column; gap: .25rem; }
  .field label { font-size: var(--a-text-xs); color: var(--a-ink-secondary); }
  .field input, .field select, .field textarea { font: inherit; font-family: var(--a-font-mono); font-size: var(--a-text-sm); color: var(--a-ink); background: var(--a-bg); border: var(--a-border) solid var(--a-line-strong); border-radius: var(--a-radius-sm); padding: .45rem .6rem; width: 9.5rem; }
  .field textarea { width: 100%; box-sizing: border-box; }
  .field input:focus-visible, .field select:focus-visible, .field textarea:focus-visible { outline: 2px solid var(--a-focus); outline-offset: 1px; }
  .field input.bad { border-color: var(--a-critical); }
  .results { display: grid; grid-template-columns: max-content 1fr; gap: .35rem 1.2rem; margin-top: 1.1rem; font-size: var(--a-text-sm); }
  .results dt { color: var(--a-ink-secondary); margin: 0; }
  .results dd { margin: 0; font-family: var(--a-font-mono); }
  .note { font-size: var(--a-text-xs); color: var(--a-ink-muted); margin-top: .9rem; }
  .warn { color: var(--a-warning); }
  .err { color: var(--a-critical); }
  table.finder { border-collapse: collapse; width: 100%; margin-top: 1.1rem; font-size: var(--a-text-sm); }
  table.finder th, table.finder td { text-align: left; padding: .4rem .7rem; border-bottom: var(--a-border) solid var(--a-line); font-family: var(--a-font-mono); white-space: nowrap; }
  table.finder th { font-family: var(--a-font); color: var(--a-ink-secondary); font-weight: 600; }
  .tablewrap { overflow-x: auto; }
  button.reset { font: inherit; font-size: var(--a-text-xs); color: var(--a-link); background: none; border: none; cursor: pointer; padding: 0; }
  button.reset:hover { color: var(--a-link-hover); text-decoration: underline; }
  .field input.computed { background: var(--a-bg-accent); color: var(--a-ink); border-color: var(--a-link); }
  .cardfoot { display: flex; align-items: center; gap: 1.1rem; margin-top: 1rem; }
  .cardfoot button { font: inherit; font-size: var(--a-text-xs); color: var(--a-link); background: none; border: none; cursor: pointer; padding: 0; }
  .cardfoot button:hover { color: var(--a-link-hover); text-decoration: underline; }
  .cardfoot button:focus-visible { outline: 2px solid var(--a-focus); outline-offset: 2px; }
  .cardfoot .copied { color: var(--a-good); text-decoration: none; }
  /* a control whose value is shared with its twins on other cards */
  .field [data-mirror] { border-style: dashed; }
  .legend { font-size: var(--a-text-xs); color: var(--a-ink-muted); margin: 0 0 .35rem; }
  .legend b { display: inline-block; background: var(--a-bg-accent); color: var(--a-ink); border: var(--a-border) solid var(--a-link); border-radius: var(--a-radius-sm); padding: 0 .35rem; font-weight: 400; }
  footer.site { border-top: var(--a-border) solid var(--a-line); color: var(--a-ink-muted); font-size: var(--a-text-xs); padding: 1rem 0 2rem; }
</style>
</head>
<body>
<header class="site wrap">
  <h1>EE Calculator</h1>
</header>

<div class="wrap">
<nav class="tabs" role="tablist" id="tabbar">
  <button role="tab" data-tab="fund" aria-selected="true">Fundamentals</button>
  <button role="tab" data-tab="res" aria-selected="false">Resistors</button>
  <button role="tab" data-tab="filt" aria-selected="false">Filters &amp; Resonance</button>
  <button role="tab" data-tab="copper" aria-selected="false">PCB Copper</button>
  <button role="tab" data-tab="signal" aria-selected="false">PCB Signal</button>
  <button role="tab" data-tab="pwr" aria-selected="false">Power &amp; Thermal</button>
  <button role="tab" data-tab="util" aria-selected="false">Utilities</button>
</nav>
</div>

<main class="wrap">

<section class="panel active" id="panel-fund">
  <h2>Fundamentals</h2>
  <p class="hint">Basic network arithmetic. Every field accepts SI suffixes (<code>4k7</code>, <code>10n</code>, <code>2.2M</code>).</p>
  <div class="card">
    <h3>Ohm&rsquo;s law and power</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="ohm-v">Voltage V (V)</label><input id="ohm-v" inputmode="decimal" placeholder="e.g. 12"></div>
      <div class="field"><label for="ohm-i">Current I (A)</label><input id="ohm-i" inputmode="decimal" placeholder="e.g. 20m"></div>
      <div class="field"><label for="ohm-r">Resistance R (&Omega;)</label><input id="ohm-r" inputmode="decimal" placeholder="e.g. 4k7"></div>
      <div class="field"><label for="ohm-p">Power P (W)</label><input id="ohm-p" inputmode="decimal" placeholder="e.g. 250m"></div>
    </div>
    <svg class="schem" width="210" height="130" viewBox="0 0 210 130" role="img" aria-label="Voltage source driving a resistor">
      <circle class="wire" cx="35" cy="65" r="14"/>
      <text x="31" y="69">V</text>
      <path class="wire" d="M35 51 V25 H160 V45"/>
      <path class="wire" d="M160 85 V105 H35 V79"/>
      <rect class="wire" x="149" y="45" width="22" height="40"/>
      <text x="180" y="69">R</text>
      <path class="dot" d="M92 20 L104 25 L92 30 Z"/>
      <text x="86" y="14">I</text>
      <text x="60" y="122">P = V&#183;I</text>
    </svg>
    </div>
    <dl class="results" id="ohm-out"></dl>
    <button class="reset" data-reset="ohm">Reset</button>
  </div>
  <div class="card">
    <h3>Series / parallel</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="sp-type">Component</label>
        <select id="sp-type"><option value="R" selected>Resistors (&Omega;)</option><option value="C">Capacitors (F)</option><option value="L">Inductors (H)</option></select>
      </div>
      <div class="field"><label for="sp-v">Applied voltage (V, optional)</label><input id="sp-v" inputmode="decimal" placeholder="e.g. 12"></div>
      <div class="field" style="flex:1 1 100%"><label for="sp-list">Values</label><textarea id="sp-list" rows="3" placeholder="e.g. 10k, 4k7, 1k"></textarea></div>
    </div>
    <svg class="schem" width="260" height="125" viewBox="0 0 260 125" role="img" aria-label="Resistors in series and in parallel">
      <path class="wire" d="M8 40 H26"/>
      <rect class="wire" x="26" y="32" width="34" height="16"/>
      <text x="35" y="27">R1</text>
      <path class="wire" d="M60 40 H76"/>
      <rect class="wire" x="76" y="32" width="34" height="16"/>
      <text x="85" y="27">R2</text>
      <path class="wire" d="M110 40 H128"/>
      <text x="42" y="72">Series</text>
      <path class="wire" d="M205 12 V22 M205 22 H180 V35 M205 22 H230 V35"/>
      <circle class="dot" cx="205" cy="22" r="2.5"/>
      <rect class="wire" x="171" y="35" width="18" height="42"/>
      <rect class="wire" x="221" y="35" width="18" height="42"/>
      <text x="163" y="30">R1</text>
      <text x="228" y="30">R2</text>
      <path class="wire" d="M180 77 V90 H230 V77 M205 90 V100"/>
      <circle class="dot" cx="205" cy="90" r="2.5"/>
      <text x="181" y="118">Parallel</text>
    </svg>
    </div>
    <dl class="results" id="sp-out"></dl>
    <button class="reset" data-reset="sp">Reset</button>
  </div>
</section>

<section class="panel" id="panel-res">
  <nav class="subtabs" role="tablist" id="subbar-res">
    <button role="tab" data-sub="div" aria-selected="true">Divider</button>
    <button role="tab" data-sub="led" aria-selected="false">LED Resistor</button>
    <button role="tab" data-sub="acc" aria-selected="false">Accuracy</button>
  </nav>
<div class="subpanel active" id="sub-div">
  <h2>Divider</h2>
  <p class="hint">R1 on top, R2 to ground; unloaded, V<sub>out</sub> = V<sub>in</sub> &middot; R2 / (R1 + R2). The solver fills in whatever is missing as soon as it has enough &mdash; give it three of the four values, or just the two voltages to search standard E-series pairs.</p>
  <div class="card">
    <h3>Divider solver</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="div-vin">V<sub>in</sub> (V)</label><input id="div-vin" inputmode="decimal" placeholder="e.g. 12"></div>
      <div class="field"><label for="div-vout">V<sub>out</sub> (V)</label><input id="div-vout" inputmode="decimal" placeholder="e.g. 3.3"></div>
      <div class="field"><label for="div-r1">R1 &mdash; top (&Omega;)</label><input id="div-r1" inputmode="decimal" placeholder="e.g. 10k"></div>
      <div class="field"><label for="div-r2">R2 &mdash; bottom (&Omega;)</label><input id="div-r2" inputmode="decimal" placeholder="e.g. 4k7"></div>
      <div class="field"><label for="div-rtot">Total R1&#8202;+&#8202;R2 (&Omega;, optional)</label><input id="div-rtot" inputmode="decimal" placeholder="e.g. 100k"></div>
      <div class="field"><label for="div-iload">Load current at midpoint (A, optional)</label><input id="div-iload" inputmode="decimal" placeholder="e.g. 50u"></div>
          <div class="field"><label for="div-series">E-series</label>
        <select id="div-series" data-mirror="series"><option value="E12">E12 (10 %)</option><option value="E24">E24 (5 %)</option><option value="E96" selected>E96 (1 %)</option></select>
      </div>
    </div>
    <svg class="schem" width="210" height="235" viewBox="0 0 210 235" role="img" aria-label="Resistor divider: R1 from Vin to the midpoint, R2 from the midpoint to ground, optional load current out of the midpoint">
      <circle class="wire" cx="60" cy="18" r="3.5"/>
      <text x="72" y="22">Vin</text>
      <path class="wire" d="M60 21.5 V45"/>
      <rect class="wire" x="49" y="45" width="22" height="46"/>
      <text x="80" y="72">R1</text>
      <path class="wire" d="M60 91 V115"/>
      <circle class="dot" cx="60" cy="115" r="3"/>
      <path class="wire" d="M60 115 H130"/>
      <circle class="wire" cx="133.5" cy="115" r="3.5"/>
      <text x="144" y="119">Vout</text>
      <path class="wire opt" d="M100 115 V148"/>
      <path class="dot" d="M96 146 L100 156 L104 146 Z"/>
      <text x="108" y="150">I load</text>
      <text x="108" y="163">(optional)</text>
      <path class="wire" d="M60 115 V133"/>
      <rect class="wire" x="49" y="133" width="22" height="46"/>
      <text x="80" y="160">R2</text>
      <path class="wire" d="M60 179 V202"/>
      <path class="wire" d="M46 202 H74 M51 209 H69 M56 216 H64"/>
    </svg>
    </div>
    <dl class="results" id="div-out"></dl>
    <div class="tablewrap"><table class="finder" id="div-table" hidden>
      <thead><tr><th>R1 (top)</th><th>R2 (bottom)</th><th>V<sub>out</sub></th><th>Error</th><th>Current in R1</th><th>Total R</th></tr></thead>
      <tbody id="div-body"></tbody>
    </table></div>
    <p class="note" id="div-note"></p>
    <p class="note">Fill in any three of V<sub>in</sub>, V<sub>out</sub>, R1 and R2 &mdash; the fourth is calculated as soon as enough is entered, and a solved resistor gets a nearest-standard-value suggestion. With only V<sub>in</sub> and V<sub>out</sub>, the best standard-value pairs are searched instead (total R, if given, sets the exact solution and steers the search; with one leg known it stands in for the other). The load is a constant current drawn out of the midpoint, so R1 carries the R2 current plus the load; leave it empty for an unloaded divider.</p>
    <button class="reset" data-reset="div">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-led">
  <h2>LED Resistor</h2>
  <p class="hint">R = (V<sub>supply</sub> &minus; V<sub>f</sub>) / I<sub>f</sub>, or the current a resistor you already have will give.</p>
  <div class="card">
    <h3>LED series resistor</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="led-vs">V<sub>supply</sub> (V)</label><input id="led-vs" inputmode="decimal" placeholder="e.g. 5"></div>
      <div class="field"><label for="led-vf">LED V<sub>f</sub> (V)</label><input id="led-vf" inputmode="decimal" placeholder="e.g. 2.1"></div>
      <div class="field"><label for="led-if">LED I<sub>f</sub> (A)</label><input id="led-if" inputmode="decimal" placeholder="e.g. 10m"></div>
      <div class="field"><label for="led-r">Series R (&Omega;)</label><input id="led-r" inputmode="decimal" placeholder="solved, or enter"></div>
          <div class="field"><label for="led-series">E-series</label>
        <select id="led-series" data-mirror="series"><option value="E12">E12 (10 %)</option><option value="E24">E24 (5 %)</option><option value="E96" selected>E96 (1 %)</option></select>
      </div>
    </div>
    <svg class="schem" width="250" height="125" viewBox="0 0 250 125" role="img" aria-label="Supply, series resistor, LED to ground">
      <circle class="wire" cx="18" cy="45" r="3.5"/>
      <text x="8" y="30">Vs</text>
      <path class="wire" d="M21.5 45 H50"/>
      <rect class="wire" x="50" y="37" width="40" height="16"/>
      <text x="64" y="32">R</text>
      <path class="wire" d="M90 45 H128"/>
      <path class="wire" d="M128 31 L128 59 L154 45 Z"/>
      <path class="wire" d="M154 31 V59"/>
      <path class="wire" d="M146 26 L157 15 M153 29 L164 18"/>
      <path class="dot" d="M157 15 L159 21 L163 17 Z"/>
      <path class="dot" d="M164 18 L166 24 L170 20 Z"/>
      <text x="126" y="76">LED</text>
      <path class="wire" d="M154 45 H190 V80"/>
      <path class="wire" d="M176 80 H204 M181 87 H199 M186 94 H194"/>
    </svg>
    </div>
    <dl class="results" id="led-out"></dl>
    <button class="reset" data-reset="led">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-acc">
  <h2>Accuracy</h2>
  <p class="hint">What tolerance, temperature coefficient and ageing do to a divider&rsquo;s ratio. A divider only cares how the two legs move <em>relative to each other</em>, so matched parts beat tight parts.</p>
  <div class="card">
    <h3>Error budget</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="ac-r1">R1 &mdash; top (&Omega;)</label><input id="ac-r1" inputmode="decimal" placeholder="e.g. 10k"></div>
      <div class="field"><label for="ac-r2">R2 &mdash; bottom (&Omega;)</label><input id="ac-r2" inputmode="decimal" placeholder="e.g. 4k7"></div>
      <div class="field"><label for="ac-vin">V<sub>in</sub> (V, optional)</label><input id="ac-vin" inputmode="decimal" placeholder="e.g. 12"></div>
      <div class="field"><label for="ac-tol1">R1 tolerance (%)</label><input id="ac-tol1" inputmode="decimal" placeholder="1"></div>
      <div class="field"><label for="ac-tol2">R2 tolerance (%)</label><input id="ac-tol2" inputmode="decimal" placeholder="1"></div>
      <div class="field"><label for="ac-tcr1">R1 TCR (ppm/&deg;C)</label><input id="ac-tcr1" inputmode="decimal" placeholder="100"></div>
      <div class="field"><label for="ac-tcr2">R2 TCR (ppm/&deg;C)</label><input id="ac-tcr2" inputmode="decimal" placeholder="100"></div>
      <div class="field"><label for="ac-tmin">T min (&deg;C)</label><input id="ac-tmin" inputmode="decimal" placeholder="-40"></div>
      <div class="field"><label for="ac-tmax">T max (&deg;C)</label><input id="ac-tmax" inputmode="decimal" placeholder="85"></div>
      <div class="field"><label for="ac-tnom">T nominal (&deg;C)</label><input id="ac-tnom" inputmode="decimal" placeholder="25"></div>
      <div class="field"><label for="ac-age">Ageing / drift (ppm, optional)</label><input id="ac-age" inputmode="decimal" placeholder="e.g. 500"></div>
    </div>
    <svg class="schem" width="150" height="180" viewBox="0 0 150 180" role="img" aria-label="Divider with tolerance bands on each leg">
      <circle class="wire" cx="55" cy="14" r="3.5"/>
      <text x="66" y="18">Vin</text>
      <path class="wire" d="M55 17.5 V38"/>
      <rect class="wire" x="44" y="38" width="22" height="40"/>
      <text x="74" y="56">R1 &plusmn;</text>
      <path class="wire" d="M55 78 V100"/>
      <circle class="dot" cx="55" cy="100" r="3"/>
      <path class="wire" d="M55 100 H100"/>
      <circle class="wire" cx="103.5" cy="100" r="3.5"/>
      <text x="112" y="104">out</text>
      <path class="wire" d="M55 100 V116"/>
      <rect class="wire" x="44" y="116" width="22" height="40"/>
      <text x="74" y="140">R2 &plusmn;</text>
      <path class="wire" d="M55 156 V166 M41 166 H69 M46 172 H64 M51 178 H59"/>
    </svg>
    </div>
    <dl class="results" id="ac-out"></dl>
    <p class="note">Worst case is exact (both legs at their opposing extremes); RSS treats the contributions as independent random variables, which is the realistic figure for a production run but assumes the two TCRs are uncorrelated. Blank fields default to 1 %, 100 ppm/&deg;C, and &minus;40/+85/25 &deg;C.</p>
    <button class="reset" data-reset="ac">Reset</button>
  </div>
</div>
</section>

<section class="panel" id="panel-filt">
  <nav class="subtabs" role="tablist" id="subbar-filt">
    <button role="tab" data-sub="flt" aria-selected="true">Filter Design</button>
    <button role="tab" data-sub="re" aria-selected="false">Reactance</button>
    <button role="tab" data-sub="xc" aria-selected="false">Crystal Load</button>
    <button role="tab" data-sub="pad" aria-selected="false">Attenuator Pads</button>
  </nav>
<div class="subpanel active" id="sub-flt">
  <h2>Filter Design</h2>
  <p class="hint">Pick a topology and give it any two values; the third follows. First-order RC and RL give a cutoff and a time constant, LC gives resonance and, with a resistance, Q and bandwidth.</p>
  <div class="card">
    <h3>Filter design</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="flt-type">Elements</label>
        <select id="flt-type">
          <option value="rc" selected>RC</option>
          <option value="rl">RL</option>
          <option value="lc">LC</option>
        </select>
      </div>
      <div class="field"><label for="flt-resp">Response</label>
        <select id="flt-resp">
          <option value="lp" selected>Low-pass</option>
          <option value="hp">High-pass</option>
        </select>
      </div>
      <div class="field"><label for="flt-order">Order</label>
        <select id="flt-order">
          <option value="1" selected>1st</option>
          <option value="2">2nd</option>
          <option value="3">3rd</option>
          <option value="4">4th</option>
        </select>
      </div>
      <div class="field"><label for="flt-r">R (&Omega;)</label><input id="flt-r" inputmode="decimal" placeholder="e.g. 10k"></div>
      <div class="field"><label for="flt-c">C (F)</label><input id="flt-c" inputmode="decimal" placeholder="e.g. 100n"></div>
      <div class="field"><label for="flt-l">L (H)</label><input id="flt-l" inputmode="decimal" placeholder="e.g. 10u"></div>
      <div class="field"><label for="flt-f">Section f<sub>0</sub> (Hz)</label><input id="flt-f" inputmode="decimal" placeholder="solved"></div>
    </div>
    <div id="flt-diagram" class="diagram"></div>
    </div>
    <div id="flt-graph" class="chart" tabindex="0" role="img" aria-label="Magnitude response"></div>
    <dl class="results" id="flt-out"></dl>
    <p class="note" id="flt-note"></p>
    <button class="reset" data-reset="flt">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-re">
  <h2>Reactance &amp; Self-Resonance</h2>
  <p class="hint">Ideal reactance at a frequency, and what real parts do once their parasitics matter. Every capacitor has series inductance and every inductor has winding capacitance, so both self-resonate and both stop behaving like themselves above that point.</p>
  <div class="card">
    <h3>Reactance and self-resonance</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="re-f">Frequency (Hz)</label><input id="re-f" inputmode="decimal" placeholder="e.g. 10M"></div>
      <div class="field"><label for="re-c">Capacitance C (F)</label><input id="re-c" inputmode="decimal" placeholder="e.g. 100n"></div>
      <div class="field"><label for="re-esl">C: ESL (H)</label><input id="re-esl" inputmode="decimal" placeholder="e.g. 500p"></div>
      <div class="field"><label for="re-esr">C: ESR (&Omega;)</label><input id="re-esr" inputmode="decimal" placeholder="e.g. 10m"></div>
      <div class="field"><label for="re-n">C in parallel</label><input id="re-n" inputmode="numeric" placeholder="1"></div>
      <div class="field"><label for="re-l">Inductance L (H)</label><input id="re-l" inputmode="decimal" placeholder="e.g. 22u"></div>
      <div class="field"><label for="re-epc">L: winding C (F)</label><input id="re-epc" inputmode="decimal" placeholder="e.g. 3p"></div>
      <div class="field"><label for="re-dcr">L: DCR (&Omega;)</label><input id="re-dcr" inputmode="decimal" placeholder="e.g. 50m"></div>
    </div>
    <svg class="schem" width="230" height="150" viewBox="0 0 230 150" role="img" aria-label="Real capacitor as C, ESL and ESR in series; real inductor as L and DCR in series with winding capacitance across">
      <text x="6" y="14">real capacitor</text>
      <path class="wire" d="M8 40 H26"/>
      <path class="wire" d="M26 30 V50 M34 30 V50"/>
      <text x="22" y="64">C</text>
      <path class="wire" d="M34 40 H48"/>
      <path class="wire" d="M48 40 A5 5 0 0 1 58 40 A5 5 0 0 1 68 40"/>
      <text x="50" y="28">ESL</text>
      <rect class="wire" x="68" y="33" width="26" height="14"/>
      <text x="70" y="64">ESR</text>
      <path class="wire" d="M94 40 H112"/>
      <text x="6" y="104">real inductor</text>
      <path class="wire" d="M136 130 H154"/>
      <path class="wire" d="M154 130 A6 6 0 0 1 166 130 A6 6 0 0 1 178 130 A6 6 0 0 1 190 130"/>
      <text x="162" y="146">L</text>
      <rect class="wire" x="190" y="123" width="24" height="14"/>
      <text x="192" y="146">DCR</text>
      <path class="wire" d="M214 130 H224"/>
      <path class="wire" d="M145 130 V104 H176 M182 104 H214 V130"/>
      <path class="wire" d="M176 96 V112 M182 96 V112"/>
      <text x="158" y="92">winding C</text>
    </svg>
    </div>
    <dl class="results" id="re-out"></dl>
    <p class="note">A capacitor is C, ESL and ESR in series: capacitive below self-resonance, resistive at it, <em>inductive above</em>. An inductor is L and DCR in series with its winding capacitance across the whole thing: inductive below self-resonance, <em>capacitive above</em>. Paralleling n identical capacitors multiplies C and divides ESL and ESR by n, which lowers the impedance floor without moving self-resonance.</p>
    <button class="reset" data-reset="re">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-xc">
  <h2>Crystal Load</h2>
  <p class="hint">Pierce-oscillator load capacitance: what the crystal sees, or the partner a chosen leg needs.</p>
  <div class="card">
    <h3>Load capacitance</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="xc-cl">Crystal C<sub>L</sub> spec (F)</label><input id="xc-cl" inputmode="decimal" placeholder="e.g. 12p"></div>
      <div class="field"><label for="xc-c1">C1 (F)</label><input id="xc-c1" inputmode="decimal" placeholder="e.g. 18p"></div>
      <div class="field"><label for="xc-c2">C2 (F)</label><input id="xc-c2" inputmode="decimal" placeholder="e.g. 18p"></div>
      <div class="field"><label for="xc-cs">Stray C (F)</label><input id="xc-cs" inputmode="decimal" placeholder="3p"></div>
    </div>
    <svg class="schem" width="220" height="130" viewBox="0 0 220 130" role="img" aria-label="Crystal with two load capacitors to ground">
      <path class="wire" d="M40 30 H180"/>
      <rect class="wire" x="95" y="20" width="30" height="20"/>
      <path class="wire" d="M88 15 V45 M132 15 V45"/>
      <text x="98" y="60">XTAL</text>
      <path class="wire" d="M60 30 V62 M48 62 H72 M48 72 H72 M60 72 V92 M48 92 H72 M53 99 H67 M58 106 H62"/>
      <text x="26" y="72">C1</text>
      <path class="wire" d="M160 30 V62 M148 62 H172 M148 72 H172 M160 72 V92 M148 92 H172 M153 99 H167 M158 106 H162"/>
      <text x="178" y="72">C2</text>
    </svg>
    </div>
    <dl class="results" id="xc-out"></dl>
    <p class="note">C<sub>L</sub> = C1&middot;C2/(C1+C2) + C<sub>stray</sub>. Give C1 and C2 to check the load the crystal sees, or just the C<sub>L</sub> spec to get the required C1 = C2. Stray defaults to 3 pF (pads + pins).</p>
    <button class="reset" data-reset="xc">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-pad">
  <h2>Attenuator Pads</h2>
  <p class="hint">Resistive attenuators that keep source and load matched. The E-series suggestion shows the attenuation stock parts would actually give.</p>
  <div class="card">
    <h3>PI, T and L pads</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="pad-a">Attenuation (dB)</label><input id="pad-a" inputmode="decimal" placeholder="e.g. 6"></div>
      <div class="field"><label for="pad-z0">System impedance Z<sub>0</sub> (&Omega;)</label><input id="pad-z0" inputmode="decimal" placeholder="50"></div>
      <div class="field"><label for="pad-z2">Second impedance (&Omega;, for an L pad)</label><input id="pad-z2" inputmode="decimal" placeholder="e.g. 75"></div>
          <div class="field"><label for="pad-series">E-series</label>
        <select id="pad-series" data-mirror="series"><option value="E12">E12 (10 %)</option><option value="E24">E24 (5 %)</option><option value="E96" selected>E96 (1 %)</option></select>
      </div>
    </div>
    <svg class="schem" width="220" height="150" viewBox="0 0 220 150" role="img" aria-label="PI pad and T pad topologies">
      <path class="wire" d="M12 26 H40 M40 26 H70 M70 26 H98"/>
      <rect class="wire" x="40" y="18" width="30" height="16"/>
      <circle class="dot" cx="40" cy="26" r="2.5"/><circle class="dot" cx="70" cy="26" r="2.5"/>
      <rect class="wire" x="32" y="44" width="16" height="24"/>
      <rect class="wire" x="62" y="44" width="16" height="24"/>
      <path class="wire" d="M40 34 V44 M70 34 V44 M40 68 V78 M70 68 V78 M20 78 H90 M30 84 H80"/>
      <text x="122" y="30">PI pad</text>
      <path class="wire" d="M12 112 H34 M64 112 H98"/>
      <rect class="wire" x="34" y="104" width="24" height="16"/>
      <rect class="wire" x="64" y="104" width="24" height="16" transform="translate(-6,0)"/>
      <circle class="dot" cx="61" cy="112" r="2.5"/>
      <rect class="wire" x="53" y="124" width="16" height="20"/>
      <path class="wire" d="M61 112 V124"/>
      <text x="122" y="116">T pad</text>
    </svg>
    </div>
    <dl class="results" id="pad-out"></dl>
    <p class="note">Valid for any attenuation above 0 dB. An L pad matches two <em>different</em> impedances and has a minimum loss set by their ratio &mdash; enter a second impedance to size one.</p>
    <button class="reset" data-reset="pad">Reset</button>
  </div>
</div>
</section>

<section class="panel" id="panel-copper">
  <nav class="subtabs" role="tablist" id="subbar-copper">
    <button role="tab" data-sub="tw" aria-selected="true">Trace Current</button>
    <button role="tab" data-sub="via" aria-selected="false">Via</button>
    <button role="tab" data-sub="fu" aria-selected="false">Fusing Current</button>
    <button role="tab" data-sub="spc" aria-selected="false">Conductor Spacing</button>
  </nav>
<div class="subpanel active" id="sub-tw">
  <h2>Trace Current</h2>
  <p class="hint">Will the copper carry the current. Dimension fields take mm by default and accept <code>mil</code>, <code>um</code> and <code>in</code>.</p>
  <div class="card">
    <h3>Trace width &harr; current (IPC-2221)</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="tw-i">Current (A)</label><input id="tw-i" inputmode="decimal" placeholder="e.g. 3"></div>
      <div class="field"><label for="tw-w">Trace width (mm)</label><input id="tw-w" inputmode="decimal" placeholder="or e.g. 20mil"></div>
      <div class="field"><label for="tw-layer">Layer</label>
        <select id="tw-layer"><option value="ext" selected>External</option><option value="int">Internal</option></select>
      </div>
      <div class="field"><label for="tw-len">Length (mm, optional)</label><input id="tw-len" inputmode="decimal" placeholder="e.g. 50"></div>
      <div class="field"><label for="tw-f">Frequency (Hz, optional)</label><input id="tw-f" inputmode="decimal" placeholder="e.g. 1M"></div>
          <div class="field"><label for="tw-oz">Copper weight</label>
        <select id="tw-oz" data-mirror="copper"><option value="17.5">0.5 oz (17.5 &micro;m)</option><option value="35" selected>1 oz (35 &micro;m)</option><option value="70">2 oz (70 &micro;m)</option><option value="105">3 oz (105 &micro;m)</option></select>
      </div>
      <div class="field"><label for="tw-dt">Temp rise (&deg;C)</label><input id="tw-dt" data-mirror="dt" inputmode="decimal" placeholder="10"></div>
      <div class="field"><label for="tw-ta">Ambient (&deg;C)</label><input id="tw-ta" data-mirror="ta" inputmode="decimal" placeholder="25"></div>
    </div>
    <svg class="schem" width="230" height="110" viewBox="0 0 230 110" role="img" aria-label="Trace cross-section on a board">
      <rect class="wire" x="20" y="55" width="190" height="28"/>
      <path class="dot" d="M85 38 H145 V52 H85 Z"/>
      <path class="wire" d="M85 24 V34 M145 24 V34 M85 29 H145"/>
      <text x="106" y="18">w</text>
      <path class="wire" d="M158 38 H166 M158 52 H166 M162 38 V52"/>
      <text x="171" y="49">t</text>
      <text x="24" y="74">substrate</text>
    </svg>
    </div>
    <dl class="results" id="tw-out"></dl>
    <p class="note">IPC-2221: I = k&middot;&Delta;T<sup>0.44</sup>&middot;A<sup>0.725</sup> (k = 0.048 external, 0.024 internal, A in mil&sup2;). Enter current to get width, width to get max current, or both to check margin. Blank temp rise defaults to 10 &deg;C, ambient to 25 &deg;C. IPC-2152 allows somewhat more; this is the conservative classic.</p>
    <button class="reset" data-reset="tw">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-via">
  <h2>Via</h2>
  <p class="hint">Electrical, thermal and fabrication properties of a plated through hole.</p>
  <div class="card">
    <h3>Via</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="via-d">Drill diameter (mm)</label><input id="via-d" inputmode="decimal" placeholder="e.g. 0.3"></div>
      <div class="field"><label for="via-tp">Plating (&micro;m)</label><input id="via-tp" inputmode="decimal" placeholder="25"></div>
      <div class="field"><label for="via-h">Board thickness (mm)</label><input id="via-h" inputmode="decimal" placeholder="1.6"></div>
      <div class="field"><label for="via-pad">Pad dia (mm, optional)</label><input id="via-pad" inputmode="decimal" placeholder="e.g. 0.6"></div>
      <div class="field"><label for="via-anti">Antipad dia (mm, optional)</label><input id="via-anti" inputmode="decimal" placeholder="e.g. 1.0"></div>
      <div class="field"><label for="via-er">&epsilon;<sub>r</sub></label><input id="via-er" inputmode="decimal" placeholder="4.3"></div>
      <div class="field"><label for="via-i">Current (A, optional)</label><input id="via-i" inputmode="decimal" placeholder="e.g. 3"></div>
      <div class="field"><label for="via-n">Vias in parallel</label><input id="via-n" inputmode="numeric" placeholder="1"></div>
      <div class="field"><label for="via-arlimit">Aspect ratio limit</label><input id="via-arlimit" inputmode="decimal" placeholder="10"></div>
      <div class="field"><label for="via-stub">Stub length (mm, optional)</label><input id="via-stub" inputmode="decimal" placeholder="e.g. 1.2"></div>
          <div class="field"><label for="via-dt">Temp rise (&deg;C)</label><input id="via-dt" data-mirror="dt" inputmode="decimal" placeholder="10"></div>
    </div>
    <svg class="schem" width="180" height="140" viewBox="0 0 180 140" role="img" aria-label="Via barrel cross-section">
      <rect class="wire" x="20" y="30" width="140" height="80"/>
      <path class="wire" d="M70 20 V120 M110 20 V120"/>
      <path class="wire" d="M76 20 V120 M104 20 V120"/>
      <path class="wire" d="M55 20 H76 M104 20 H125 M55 120 H76 M104 120 H125"/>
      <text x="128" y="76">plating</text>
      <path class="wire opt" d="M76 68 H104"/>
      <text x="82" y="62">drill</text>
    </svg>
    </div>
    <dl class="results" id="via-out"></dl>
    <p class="note">Ampacity uses the IPC-2221 internal-layer constant on the barrel cross-section; L and C are the classic first-order via formulas (C needs pad and antipad diameters). Blank plating/thickness default to 25 &micro;m and 1.6 mm.</p>
    <button class="reset" data-reset="via">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-fu">
  <h2>Fusing Current</h2>
  <p class="hint">What destroys the trace, as opposed to what merely warms it.</p>
  <div class="card">
    <h3>Fusing current (Onderdonk)</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="fu-w">Trace width (mm)</label><input id="fu-w" inputmode="decimal" placeholder="e.g. 1"></div>
      <div class="field"><label for="fu-t">Fault duration (s)</label><input id="fu-t" inputmode="decimal" placeholder="e.g. 1"></div>
      <div class="field"><label for="fu-k">Onderdonk multiplier</label><input id="fu-k" inputmode="decimal" placeholder="1"></div>
          <div class="field"><label for="fu-oz">Copper weight</label>
        <select id="fu-oz" data-mirror="copper"><option value="17.5">0.5 oz (17.5 &micro;m)</option><option value="35" selected>1 oz (35 &micro;m)</option><option value="70">2 oz (70 &micro;m)</option><option value="105">3 oz (105 &micro;m)</option></select>
      </div>
      <div class="field"><label for="fu-ta">Ambient (&deg;C)</label><input id="fu-ta" data-mirror="ta" inputmode="decimal" placeholder="25"></div>
    </div>
    <svg class="schem" width="215" height="130" viewBox="0 0 215 130" role="img" aria-label="Trace cross-section showing width and copper thickness, the two dimensions that set the fusing current">
      <rect class="wire" x="18" y="62" width="180" height="30"/>
      <text x="22" y="82">substrate</text>
      <path class="dot" d="M62 44 H154 V60 H62 Z"/>
      <path class="wire" d="M62 30 V40 M154 30 V40 M62 35 H154"/>
      <text x="100" y="26">w</text>
      <path class="wire" d="M162 44 H172 M162 60 H172 M167 44 V60"/>
      <text x="176" y="56">t</text>
      <text x="18" y="112">cross-section = w &#215; t</text>
      <text x="18" y="126">the fuse is the copper, not the current</text>
    </svg>
    </div>
    <dl class="results" id="fu-out"></dl>
    <p class="note">Onderdonk&rsquo;s equation, copper melting at 1083 &deg;C, adiabatic &mdash; valid for events up to a few seconds; longer events shed heat and survive more.</p>
    <button class="reset" data-reset="fu">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-spc">
  <h2>Conductor Spacing</h2>
  <p class="hint">IPC-2221 Table 6-1 minimum clearance, all seven environments at once.</p>
  <div class="card">
    <h3>Conductor spacing (IPC-2221 Table 6-1)</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="spc-v">Peak voltage between conductors (V)</label><input id="spc-v" inputmode="decimal" placeholder="e.g. 48"></div>
    </div>
    <svg class="schem" width="225" height="130" viewBox="0 0 225 130" role="img" aria-label="Two conductors on a substrate separated by a gap, with an optional coating over them">
      <rect class="wire" x="14" y="58" width="196" height="30"/>
      <path class="dot" d="M40 40 H86 V56 H40 Z"/>
      <path class="dot" d="M138 40 H184 V56 H138 Z"/>
      <path class="wire" d="M86 48 H138"/>
      <path class="wire" d="M86 34 V44 M138 34 V44"/>
      <text x="102" y="30">S</text>
      <path class="wire opt" d="M30 34 H194 V58"/>
      <text x="30" y="24">coating, if any</text>
      <text x="14" y="108">S is the gap between copper edges, and the</text>
      <text x="14" y="122">minimum depends on coating and altitude</text>
    </svg>
    </div>
    <dl class="results" id="spc-out"></dl>
    <p class="note">Minimum spacing per environment. B1 internal layers; B2 external uncoated &le;3050 m; B3 external uncoated &gt;3050 m; B4 external with permanent polymer coating; A5 external conformal coated; A6 external component leads uncoated; A7 component leads conformal coated.</p>
    <button class="reset" data-reset="spc">Reset</button>
  </div>
</div>
</section>

<section class="panel" id="panel-signal">
  <nav class="subtabs" role="tablist" id="subbar-signal">
    <button role="tab" data-sub="z" aria-selected="true">Impedance</button>
    <button role="tab" data-sub="dp" aria-selected="false">Differential Pair</button>
    <button role="tab" data-sub="ee" aria-selected="false">Effective &epsilon;<sub>r</sub></button>
    <button role="tab" data-sub="wl" aria-selected="false">Wavelength</button>
    <button role="tab" data-sub="vs" aria-selected="false">Via Shielding</button>
  </nav>
<div class="subpanel active" id="sub-z">
  <h2>Impedance</h2>
  <p class="hint">Five structures on one consistent model. Each result names the model and its validity window; for a real stackup, confirm with the fab&rsquo;s field solver.</p>
  <div class="card">
    <h3>Single-ended Z<sub>0</sub></h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="z-struct">Structure</label>
        <select id="z-struct">
          <option value="ms" selected>Microstrip, bare</option>
          <option value="mscov">Microstrip, covered</option>
          <option value="sl">Stripline, centred</option>
          <option value="asym">Stripline, offset</option>
          <option value="cpwg">Coplanar over ground</option>
        </select>
      </div>
      <div class="field"><label for="z-w">Trace width (mm)</label><input id="z-w" inputmode="decimal" placeholder="e.g. 0.3"></div>
      <div class="field"><label for="z-h" id="z-hlabel">Dielectric height h (mm)</label><input id="z-h" inputmode="decimal" placeholder="e.g. 0.2"></div>
      <div class="field"><label for="z-er">&epsilon;<sub>r</sub></label><input id="z-er" inputmode="decimal" placeholder="4.3"></div>
      <div class="field"><label for="z-ermask">Cover &epsilon;<sub>r</sub></label><input id="z-ermask" inputmode="decimal" placeholder="3.8 (solder mask)"></div>
      <div class="field"><label for="z-c">Far plane distance (mm)</label><input id="z-c" inputmode="decimal" placeholder="offset stripline"></div>
      <div class="field"><label for="z-s">Gap to ground (mm)</label><input id="z-s" inputmode="decimal" placeholder="coplanar"></div>
      <div class="field"><label for="z-f">Frequency (Hz, optional)</label><input id="z-f" inputmode="decimal" placeholder="e.g. 1G"></div>
          <div class="field"><label for="z-oz">Copper weight</label>
        <select id="z-oz" data-mirror="copper"><option value="17.5">0.5 oz (17.5 &micro;m)</option><option value="35" selected>1 oz (35 &micro;m)</option><option value="70">2 oz (70 &micro;m)</option><option value="105">3 oz (105 &micro;m)</option></select>
      </div>
    </div>
    <svg class="schem" width="230" height="120" viewBox="0 0 230 120" role="img" aria-label="Microstrip and stripline cross-sections">
      <rect class="wire" x="15" y="45" width="90" height="30"/>
      <path class="dot" d="M40 34 H80 V44 H40 Z"/>
      <path class="wire" d="M15 76 H105" stroke-width="3"/>
      <text x="30" y="102">microstrip</text>
      <rect class="wire" x="125" y="35" width="90" height="50"/>
      <path class="dot" d="M150 55 H190 V64 H150 Z"/>
      <path class="wire" d="M125 34 H215" stroke-width="3"/>
      <path class="wire" d="M125 86 H215" stroke-width="3"/>
      <text x="142" y="102">stripline</text>
    </svg>
    </div>
    <dl class="results" id="z-out"></dl>
    <button class="reset" data-reset="z">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-dp">
  <h2>Differential Pair</h2>
  <p class="hint">Edge-coupled pairs against a target impedance band.</p>
  <div class="card">
    <h3>Differential pair</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="dp-struct">Structure</label>
        <select id="dp-struct"><option value="ms" selected>Edge-coupled microstrip</option><option value="sl">Edge-coupled stripline</option></select>
      </div>
      <div class="field"><label for="dp-w">Trace width (mm)</label><input id="dp-w" inputmode="decimal" placeholder="e.g. 0.2"></div>
      <div class="field"><label for="dp-s">Edge-to-edge spacing (mm)</label><input id="dp-s" inputmode="decimal" placeholder="e.g. 0.2"></div>
      <div class="field"><label for="dp-h">Dielectric height (mm)</label><input id="dp-h" inputmode="decimal" placeholder="e.g. 0.2"></div>
      <div class="field"><label for="dp-er">&epsilon;<sub>r</sub></label><input id="dp-er" inputmode="decimal" placeholder="4.3"></div>
      <div class="field"><label for="dp-target">Target Z<sub>diff</sub> (&Omega;)</label>
        <select id="dp-target">
          <option value="">none</option>
          <option value="90">90 &mdash; USB 2.0</option>
          <option value="100" selected>100 &mdash; Ethernet, LVDS, PCIe</option>
          <option value="85">85 &mdash; PCIe (85 &Omega; variant)</option>
          <option value="100dsi">100 &mdash; MIPI D-PHY</option>
        </select>
      </div>
          <div class="field"><label for="dp-oz">Copper weight</label>
        <select id="dp-oz" data-mirror="copper"><option value="17.5">0.5 oz (17.5 &micro;m)</option><option value="35" selected>1 oz (35 &micro;m)</option><option value="70">2 oz (70 &micro;m)</option><option value="105">3 oz (105 &micro;m)</option></select>
      </div>
    </div>
    <svg class="schem" width="210" height="105" viewBox="0 0 210 105" role="img" aria-label="Edge-coupled differential pair over a reference plane">
      <rect class="wire" x="15" y="40" width="180" height="30"/>
      <path class="dot" d="M55 28 H85 V39 H55 Z"/>
      <path class="dot" d="M120 28 H150 V39 H120 Z"/>
      <path class="wire" d="M15 71 H195" stroke-width="3"/>
      <path class="wire" d="M55 20 V25 M85 20 V25 M55 22 H85"/>
      <text x="64" y="16">w</text>
      <path class="wire" d="M85 33 H120"/>
      <text x="98" y="27">s</text>
      <path class="wire" d="M200 40 H206 M200 70 H206 M203 40 V70"/>
      <text x="196" y="86">h</text>
    </svg>
    </div>
    <dl class="results" id="dp-out"></dl>
    <p class="note"><b>Validity: 0.1 &lt; w/h &lt; 3.0 and 0.1 &lt; s/h &lt; 3.0.</b> Empirical coupling fits &mdash; treat the result as a starting geometry and have the fabricator field-solve the real stackup before release. Z<sub>diff</sub> = 2Z<sub>0</sub>(1 &minus; k&middot;e<sup>&minus;m&middot;s/h</sup>).</p>
    <button class="reset" data-reset="dp">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-ee">
  <h2>Effective &epsilon;<sub>r</sub></h2>
  <p class="hint">What a microstrip&rsquo;s field actually sees, with dispersion.</p>
  <div class="card">
    <h3>Effective permittivity</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="ee-w">Trace width (mm)</label><input id="ee-w" inputmode="decimal" placeholder="e.g. 0.3"></div>
      <div class="field"><label for="ee-h">Dielectric height (mm)</label><input id="ee-h" inputmode="decimal" placeholder="e.g. 0.2"></div>
      <div class="field"><label for="ee-er">&epsilon;<sub>r</sub></label><input id="ee-er" inputmode="decimal" placeholder="4.3"></div>
      <div class="field"><label for="ee-f">Frequency (Hz, optional)</label><input id="ee-f" inputmode="decimal" placeholder="e.g. 1G"></div>
          <div class="field"><label for="ee-oz">Copper weight</label>
        <select id="ee-oz" data-mirror="copper"><option value="17.5">0.5 oz (17.5 &micro;m)</option><option value="35" selected>1 oz (35 &micro;m)</option><option value="70">2 oz (70 &micro;m)</option><option value="105">3 oz (105 &micro;m)</option></select>
      </div>
    </div>
    <svg class="schem" width="230" height="140" viewBox="0 0 230 140" role="img" aria-label="Microstrip cross-section: trace width W, dielectric height H, copper thickness t, with field partly in air and partly in the substrate">
      <text x="14" y="18">air, &#949;r = 1</text>
      <rect class="wire" x="14" y="56" width="196" height="34"/>
      <text x="20" y="78">substrate &#949;r</text>
      <path class="dot" d="M84 42 H140 V54 H84 Z"/>
      <path class="wire" d="M84 28 V38 M140 28 V38 M84 33 H140"/>
      <text x="106" y="24">W</text>
      <path class="wire" d="M148 42 H158 M148 54 H158 M153 42 V54"/>
      <text x="162" y="52">t</text>
      <path class="wire" d="M216 56 V90 M212 56 H220 M212 90 H220"/>
      <text x="206" y="104">H</text>
      <path class="wire" d="M14 90 H210" stroke-width="3"/>
      <text x="14" y="106">reference plane</text>
      <path class="wire opt" d="M112 42 C 70 30 46 46 40 56"/>
      <path class="wire opt" d="M112 42 C 154 30 178 46 184 56"/>
      <text x="14" y="132">some field is in air, so &#949;eff sits between (&#949;r+1)/2 and &#949;r</text>
    </svg>
    </div>
    <dl class="results" id="ee-out"></dl>
    <p class="note">Hammerstad&ndash;Jensen for the static value, with Kirschning&ndash;Jansen dispersion when a frequency is given. A microstrip&rsquo;s field is partly in air, so &epsilon;<sub>eff</sub> always lies between (&epsilon;<sub>r</sub>+1)/2 and &epsilon;<sub>r</sub>, rising towards &epsilon;<sub>r</sub> as the trace widens. Valid for 0.01 &le; w/h &le; 100.</p>
    <button class="reset" data-reset="ee">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-wl">
  <h2>Wavelength</h2>
  <p class="hint">Wavelength, knee frequency and the length beyond which a trace is a transmission line.</p>
  <div class="card">
    <h3>Wavelength &amp; critical length</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="wl-f">Frequency (Hz)</label><input id="wl-f" inputmode="decimal" placeholder="e.g. 100M"></div>
      <div class="field"><label for="wl-tr">Rise time (s)</label><input id="wl-tr" inputmode="decimal" placeholder="or e.g. 2n"></div>
      <div class="field"><label for="wl-eeff">&epsilon;<sub>eff</sub></label><input id="wl-eeff" inputmode="decimal" placeholder="3.3 (microstrip FR4)"></div>
      <div class="field"><label for="wl-period">or period (s)</label><input id="wl-period" inputmode="decimal" placeholder="e.g. 10n"></div>
      <div class="field"><label for="wl-div">Fraction of &lambda;</label>
        <select id="wl-div"><option value="1">full &lambda;</option><option value="2">&lambda;/2</option><option value="4" selected>&lambda;/4</option><option value="8">&lambda;/8</option><option value="10">&lambda;/10</option><option value="16">&lambda;/16</option><option value="20">&lambda;/20</option></select>
      </div>
    </div>
    <svg class="schem" width="235" height="120" viewBox="0 0 235 120" role="img" aria-label="A wave along a trace with the wavelength marked, and the critical length below which no termination is needed">
      <path class="wire" d="M14 50 Q 33 18 52 50 T 90 50 T 128 50 T 166 50 T 204 50"/>
      <path class="wire" d="M14 66 V78 M90 66 V78 M14 72 H90"/>
      <text x="44" y="92">&#955;</text>
      <path class="wire" d="M128 66 V78 M166 66 V78 M128 72 H166"/>
      <text x="136" y="92">&#955;/2</text>
      <path class="dot" d="M14 100 H62 V106 H14 Z"/>
      <text x="68" y="106">critical length</text>
      <text x="14" y="24">v = c / &#8730;&#949;eff</text>
    </svg>
    </div>
    <dl class="results" id="wl-out"></dl>
    <p class="note">Enter a frequency for wavelength fractions, or a rise time for the knee frequency (0.35/t<sub>r</sub>) and the critical length beyond which a trace behaves as a transmission line (t<sub>r</sub>/2 of propagation delay). &epsilon;<sub>eff</sub> defaults to 3.3; stripline in FR4 is &asymp; &epsilon;<sub>r</sub>.</p>
    <button class="reset" data-reset="wl">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-vs">
  <h2>Via Shielding</h2>
  <p class="hint">Stitching vias along a trace or around a board edge only behave as a wall while the gaps between them are small against a wavelength. Above that the fence starts to leak, and the usual rule is to keep the pitch under a tenth of the shortest wavelength you care about.</p>
  <div class="card">
    <h3>Stitching via pitch</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="vs-f">Highest frequency (Hz)</label><input id="vs-f" inputmode="decimal" placeholder="e.g. 6G"></div>
      <div class="field"><label for="vs-tr">or signal rise time (s)</label><input id="vs-tr" inputmode="decimal" placeholder="e.g. 100p"></div>
      <div class="field"><label for="vs-er">&epsilon;<sub>r</sub></label><input id="vs-er" inputmode="decimal" placeholder="4.3"></div>
      <div class="field"><label for="vs-frac">Pitch limit</label>
        <select id="vs-frac">
          <option value="20">&lambda;/20 &mdash; conservative</option>
          <option value="10" selected>&lambda;/10 &mdash; usual rule</option>
          <option value="8">&lambda;/8 &mdash; relaxed</option>
        </select>
      </div>
      <div class="field"><label for="vs-pitch">Pitch you plan to use (mm)</label><input id="vs-pitch" inputmode="decimal" placeholder="solved"></div>
      <div class="field"><label for="vs-len">Fence length (mm, optional)</label><input id="vs-len" inputmode="decimal" placeholder="e.g. 50"></div>
      <div class="field"><label for="vs-d">Via drill (mm, optional)</label><input id="vs-d" inputmode="decimal" placeholder="e.g. 0.3"></div>
    </div>
    <svg class="schem" width="240" height="170" viewBox="0 0 240 170" role="img" aria-label="A trace flanked by two rows of stitching vias, showing pitch and setback">
      <rect class="wire" x="14" y="30" width="212" height="106"/>
      <path class="dot" d="M14 78 H226 V90 H14 Z"/>
      <text x="18" y="74">trace</text>
      <circle class="wire" cx="34" cy="48" r="6"/><circle class="wire" cx="74" cy="48" r="6"/>
      <circle class="wire" cx="114" cy="48" r="6"/><circle class="wire" cx="154" cy="48" r="6"/>
      <circle class="wire" cx="194" cy="48" r="6"/>
      <circle class="wire" cx="34" cy="120" r="6"/><circle class="wire" cx="74" cy="120" r="6"/>
      <circle class="wire" cx="114" cy="120" r="6"/><circle class="wire" cx="154" cy="120" r="6"/>
      <circle class="wire" cx="194" cy="120" r="6"/>
      <path class="wire" d="M34 26 V16 M74 26 V16 M34 21 H74"/>
      <text x="44" y="13">pitch</text>
      <path class="wire" d="M204 48 H216 M204 78 H216 M210 48 V78"/>
      <text x="196" y="160">setback</text>
      <path class="wire" d="M114 54 V72"/>
      <text x="120" y="66">d</text>
    </svg>
    </div>
    <dl class="results" id="vs-out"></dl>
    <p class="note">A via fence is a waveguide wall made of holes. It leaks through the gaps once the pitch approaches a half wavelength, so the working rule keeps the pitch an order of magnitude below that. Setback from the trace matters too: too close and the fence loads the line and shifts its impedance, so keep it beyond roughly three trace widths unless you have solved the geometry.</p>
    <button class="reset" data-reset="vs">Reset</button>
  </div>
</div>
</section>

<section class="panel" id="panel-pwr">
  <h2>Power &amp; Thermal</h2>
  <p class="hint">Getting power in and heat out.</p>
  <div class="card">
    <h3>Junction temperature</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="th-p">Power dissipated (W)</label><input id="th-p" inputmode="decimal" placeholder="e.g. 5"></div>
      <div class="field"><label for="th-jc">&theta; junction&ndash;case (&deg;C/W)</label><input id="th-jc" inputmode="decimal" placeholder="e.g. 1.5"></div>
      <div class="field"><label for="th-cs">&theta; case&ndash;sink (&deg;C/W)</label><input id="th-cs" inputmode="decimal" placeholder="e.g. 0.5"></div>
      <div class="field"><label for="th-sa">&theta; sink&ndash;ambient (&deg;C/W)</label><input id="th-sa" inputmode="decimal" placeholder="e.g. 8"></div>
      <div class="field"><label for="th-ja">or &theta; junction&ndash;ambient (&deg;C/W)</label><input id="th-ja" inputmode="decimal" placeholder="single figure"></div>
      <div class="field"><label for="th-tjmax">T<sub>j</sub> max (&deg;C)</label><input id="th-tjmax" inputmode="decimal" placeholder="e.g. 150"></div>
      <div class="field"><label for="th-tjtarget">Design T<sub>j</sub> target (&deg;C)</label><input id="th-tjtarget" inputmode="decimal" placeholder="defaults to Tj max"></div>
      <div class="field"><label for="th-tj">T<sub>j</sub> (&deg;C)</label><input id="th-tj" inputmode="decimal" placeholder="solved"></div>
          <div class="field"><label for="th-ta">Ambient (&deg;C)</label><input id="th-ta" data-mirror="ta" inputmode="decimal" placeholder="25"></div>
    </div>
    <svg class="schem" width="150" height="190" viewBox="0 0 150 190" role="img" aria-label="Thermal resistance chain from junction to ambient">
      <rect class="wire" x="40" y="12" width="70" height="20"/>
      <text x="54" y="26">junction</text>
      <path class="wire" d="M75 32 V48"/>
      <rect class="wire" x="63" y="48" width="24" height="26"/>
      <text x="94" y="65">&#952;jc</text>
      <path class="wire" d="M75 74 V86"/>
      <text x="52" y="84">case</text>
      <rect class="wire" x="63" y="86" width="24" height="26"/>
      <text x="94" y="103">&#952;cs</text>
      <path class="wire" d="M75 112 V124"/>
      <text x="50" y="122">sink</text>
      <rect class="wire" x="63" y="124" width="24" height="26"/>
      <text x="94" y="141">&#952;sa</text>
      <path class="wire" d="M75 150 V164 M55 164 H95 M60 171 H90 M65 178 H85"/>
      <text x="8" y="168">ambient</text>
    </svg>
    </div>
    <dl class="results" id="th-out"></dl>
    <p class="note">Series thermal resistances add, exactly like resistors carrying power instead of current. Give the three-part chain, or a single junction&ndash;ambient figure. Note that a datasheet &theta;<sub>ja</sub> is a JEDEC board measurement, not a physical resistance you can chain, and will not match a real stackup with thermal vias.</p>
    <button class="reset" data-reset="th">Reset</button>
  </div>
  <div class="card">
    <h3>PDN target impedance</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="pdn-v">Rail voltage (V)</label><input id="pdn-v" inputmode="decimal" placeholder="e.g. 1.2"></div>
      <div class="field"><label for="pdn-ripple">Allowed ripple (%)</label><input id="pdn-ripple" inputmode="decimal" placeholder="e.g. 2"></div>
      <div class="field"><label for="pdn-i">Maximum current (A)</label><input id="pdn-i" inputmode="decimal" placeholder="e.g. 20"></div>
      <div class="field"><label for="pdn-tr">Transient fraction (%)</label><input id="pdn-tr" inputmode="decimal" placeholder="e.g. 50"></div>
      <div class="field"><label for="pdn-fmax">Bandwidth of interest (Hz)</label><input id="pdn-fmax" inputmode="decimal" placeholder="e.g. 100M"></div>
    </div>
    <svg class="schem" width="230" height="130" viewBox="0 0 230 130" role="img" aria-label="A supply rail dipping as a current step is drawn, with the allowed ripple and the transient step marked">
      <path class="wire" d="M14 34 H70 C 84 34 84 58 98 58 L 150 58 C 164 58 164 34 178 34 H216"/>
      <path class="grid opt" d="M14 34 H216"/>
      <text x="14" y="26">V rail</text>
      <path class="wire" d="M96 34 V58 M90 34 H102 M90 58 H102"/>
      <text x="104" y="50">&#916;V ripple</text>
      <path class="wire" d="M14 96 H70 V78 H150 V96 H216"/>
      <text x="14" y="118">I load</text>
      <path class="wire" d="M160 78 V96 M154 78 H166 M154 96 H166"/>
      <text x="170" y="92">&#916;I step</text>
      <text x="14" y="14">Z target = &#916;V / &#916;I</text>
    </svg>
    </div>
    <dl class="results" id="pdn-out"></dl>
    <p class="note">Z<sub>target</sub> = (V<sub>rail</sub> &middot; ripple%) / (I<sub>max</sub> &middot; transient%). The network must stay below this from DC to the bandwidth of interest, which is the hard part &mdash; see the capacitor card for what a real part does above its self-resonance.</p>
    <button class="reset" data-reset="pdn">Reset</button>
  </div>
</section>

<section class="panel" id="panel-util">
  <nav class="subtabs" role="tablist" id="subbar-util">
    <button role="tab" data-sub="awg" aria-selected="true">AWG Wire</button>
    <button role="tab" data-sub="bat" aria-selected="false">Battery</button>
    <button role="tab" data-sub="pp" aria-selected="false">Frequency Error</button>
    <button role="tab" data-sub="nb" aria-selected="false">Number Bases</button>
    <button role="tab" data-sub="rt" aria-selected="false">Ratio Units</button>
    <button role="tab" data-sub="cv" aria-selected="false">Conversions</button>
  </nav>
<div class="subpanel active" id="sub-awg">
  <h2>AWG Wire</h2>
  <p class="hint">Gauge data, and the drop over a real run.</p>
  <div class="card">
    <h3>AWG wire</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="awg-n">AWG (40 &hellip; 0000 or 4/0)</label><input id="awg-n" placeholder="e.g. 18"></div>
      <div class="field"><label for="awg-len">Run length (m)</label><input id="awg-len" inputmode="decimal" placeholder="e.g. 0.5"></div>
      <div class="field"><label for="awg-return">Conductors</label>
        <select id="awg-return"><option value="2" selected>Round trip (out and back)</option><option value="1">One way</option></select>
      </div>
      <div class="field"><label for="awg-i">Load current (A)</label><input id="awg-i" inputmode="decimal" placeholder="e.g. 40"></div>
      <div class="field"><label for="awg-temp">Conductor temp (&deg;C)</label><input id="awg-temp" inputmode="decimal" placeholder="20"></div>
      <div class="field"><label for="awg-vsupply">Supply voltage (V, optional)</label><input id="awg-vsupply" inputmode="decimal" placeholder="e.g. 22.2"></div>
    </div>
    <svg class="schem" width="230" height="120" viewBox="0 0 230 120" role="img" aria-label="A round conductor of a given diameter carrying current over a run length, showing the out and back path">
      <circle class="wire" cx="40" cy="44" r="26"/>
      <path class="wire" d="M14 44 H66"/>
      <path class="wire" d="M14 38 V50 M66 38 V50"/>
      <text x="30" y="34">d</text>
      <text x="12" y="88">A = &#960;d&#178;/4</text>
      <path class="wire" d="M104 32 H214"/>
      <path class="dot" d="M196 27 L208 32 L196 37 Z"/>
      <path class="wire" d="M104 60 H214"/>
      <path class="dot" d="M122 55 L110 60 L122 65 Z"/>
      <text x="126" y="24">out</text>
      <text x="122" y="80">return</text>
      <path class="wire" d="M104 92 V104 M214 92 V104 M104 98 H214"/>
      <text x="146" y="116">length</text>
    </svg>
    </div>
    <dl class="results" id="awg-out"></dl>
    <p class="note">Solid copper at 20 &deg;C. The two ampacities are the classic handbook rules of thumb: &ldquo;chassis wiring&rdquo; (short runs in free air) and &ldquo;power transmission&rdquo; (bundled, conservative) &mdash; insulation rating and bundling govern real limits.</p>
    <button class="reset" data-reset="awg">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-bat">
  <h2>Battery</h2>
  <p class="hint">Pack energy, C-rate and runtime.</p>
  <div class="card">
    <h3>Battery energy and runtime</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="bat-mah">Cell capacity (mAh)</label><input id="bat-mah" inputmode="decimal" placeholder="e.g. 5000"></div>
      <div class="field"><label for="bat-v">Nominal cell voltage (V)</label><input id="bat-v" inputmode="decimal" placeholder="3.7"></div>
      <div class="field"><label for="bat-s">Cells in series (S)</label><input id="bat-s" inputmode="numeric" placeholder="1"></div>
      <div class="field"><label for="bat-p">Cells in parallel (P)</label><input id="bat-p" inputmode="numeric" placeholder="1"></div>
      <div class="field"><label for="bat-load">Load (A or W)</label><input id="bat-load" inputmode="decimal" placeholder="e.g. 2"></div>
      <div class="field"><label for="bat-loadunit">Load is</label>
        <select id="bat-loadunit"><option value="A" selected>Amps</option><option value="W">Watts</option></select>
      </div>
      <div class="field"><label for="bat-usable">Usable capacity (%)</label><input id="bat-usable" inputmode="decimal" placeholder="80"></div>
    </div>
    <svg class="schem" width="215" height="125" viewBox="0 0 215 125" role="img" aria-label="A battery pack of cells in series and parallel, showing what S and P mean">
      <g>
        <rect class="wire" x="24" y="26" width="34" height="18"/><path class="wire" d="M58 31 V39 H62 V31 Z"/>
        <rect class="wire" x="72" y="26" width="34" height="18"/><path class="wire" d="M106 31 V39 H110 V31 Z"/>
        <rect class="wire" x="120" y="26" width="34" height="18"/><path class="wire" d="M154 31 V39 H158 V31 Z"/>
        <path class="wire" d="M62 35 H72 M110 35 H120"/>
      </g>
      <g>
        <rect class="wire" x="24" y="64" width="34" height="18"/><path class="wire" d="M58 69 V77 H62 V69 Z"/>
        <rect class="wire" x="72" y="64" width="34" height="18"/><path class="wire" d="M106 69 V77 H110 V69 Z"/>
        <rect class="wire" x="120" y="64" width="34" height="18"/><path class="wire" d="M154 69 V77 H158 V69 Z"/>
        <path class="wire" d="M62 73 H72 M110 73 H120"/>
      </g>
      <path class="wire" d="M14 35 V73 M14 54 H8 M158 35 V73 M158 54 H168"/>
      <path class="wire" d="M24 35 H14 M24 73 H14"/>
      <path class="wire" d="M158 35 H166 M158 73 H166"/>
      <text x="44" y="18">S cells in series raise voltage</text>
      <text x="24" y="104">P strings in parallel raise capacity</text>
      <text x="24" y="118">pack V = S &#215; cell V, pack Ah = P &#215; cell Ah</text>
    </svg>
    </div>
    <dl class="results" id="bat-out"></dl>
    <p class="note">Runtime assumes a flat discharge at the nominal voltage, which is optimistic at high C-rates and near the end of discharge. The usable fraction defaults to 80 %, a common reserve for lithium packs; set it to 100 for the nameplate figure.</p>
    <button class="reset" data-reset="bat">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-pp">
  <h2>Frequency Error</h2>
  <p class="hint">Parts per million against a centre frequency, and the drift that follows.</p>
  <div class="card">
    <h3>Frequency error (ppm)</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="pp-f">Frequency (Hz)</label><input id="pp-f" inputmode="decimal" placeholder="e.g. 16M"></div>
      <div class="field"><label for="pp-ppm">Tolerance (ppm)</label><input id="pp-ppm" inputmode="decimal" placeholder="e.g. 20"></div>
      <div class="field"><label for="pp-df">&Delta;f (Hz)</label><input id="pp-df" inputmode="decimal" placeholder="or e.g. 320"></div>
    </div>
    <svg class="schem" width="225" height="105" viewBox="0 0 225 105" role="img" aria-label="A frequency axis showing the centre frequency and the tolerance window either side of it">
      <path class="axis wire" d="M14 62 H212"/>
      <path class="wire" d="M113 50 V74"/>
      <text x="98" y="90">centre f</text>
      <path class="wire opt" d="M62 50 V74 M164 50 V74"/>
      <path class="dot" d="M62 62 H164 V64 H62 Z"/>
      <path class="wire" d="M62 40 H164 M62 36 V44 M164 36 V44"/>
      <text x="86" y="30">&#177; ppm window</text>
      <text x="40" y="90">f min</text>
      <text x="158" y="90">f max</text>
    </svg>
    </div>
    <dl class="results" id="pp-out"></dl>
    <button class="reset" data-reset="pp">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-nb">
  <h2>Number Bases</h2>
  <p class="hint">Decimal, hex, binary and octal, at any width.</p>
  <div class="card">
    <h3>Number bases</h3>
    <div class="fields">
      <div class="field"><label for="nb-dec">Decimal</label><input id="nb-dec" placeholder="e.g. 4096"></div>
      <div class="field"><label for="nb-hex">Hex</label><input id="nb-hex" placeholder="e.g. 0x1000"></div>
      <div class="field"><label for="nb-bin">Binary</label><input id="nb-bin" placeholder="e.g. 0b1010"></div>
      <div class="field"><label for="nb-oct">Octal</label><input id="nb-oct" placeholder="e.g. 0o7777"></div>
    </div>
    <dl class="results" id="nb-out"></dl>
    <p class="note">Integers of any size. Prefixes (<code>0x</code>, <code>0b</code>, <code>0o</code>) are optional, and spaces or underscores may be used as digit separators. Negative decimals are shown as two&rsquo;s complement at each standard width that can hold them.</p>
    <button class="reset" data-reset="nb">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-rt">
  <h2>Ratio Units</h2>
  <p class="hint">Percent, ppm, ppb and plain ratios.</p>
  <div class="card">
    <h3>Ratio units</h3>
    <div class="fields">
      <div class="field"><label for="rt-pct">Percent (%)</label><input id="rt-pct" inputmode="decimal" placeholder="e.g. 0.1"></div>
      <div class="field"><label for="rt-ppm">ppm</label><input id="rt-ppm" inputmode="decimal" placeholder="e.g. 1000"></div>
      <div class="field"><label for="rt-ppb">ppb</label><input id="rt-ppb" inputmode="decimal" placeholder="e.g. 1e6"></div>
      <div class="field"><label for="rt-ratio">Ratio (decimal)</label><input id="rt-ratio" inputmode="decimal" placeholder="e.g. 0.001"></div>
    </div>
    <p class="note">Edit any field and the rest follow. 1 % = 10 000 ppm = 10<sup>7</sup> ppb = 0.01 as a plain ratio.</p>
    <button class="reset" data-reset="rt">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-cv">
  <h2>Conversions</h2>
  <p class="hint">Length, temperature, gain, and rectangular/polar.</p>
  <div class="card">
    <h3>Conversions</h3>
    <div class="fields">
      <div class="field"><label for="cv-mm">mm</label><input id="cv-mm" inputmode="decimal" placeholder="e.g. 0.254"></div>
      <div class="field"><label for="cv-mil">mil</label><input id="cv-mil" inputmode="decimal" placeholder="e.g. 10"></div>
    </div>
    <div class="fields" style="margin-top:.9rem">
      <div class="field"><label for="cv-c">&deg;C</label><input id="cv-c" inputmode="decimal" placeholder="e.g. 25"></div>
      <div class="field"><label for="cv-f">&deg;F</label><input id="cv-f" inputmode="decimal" placeholder="e.g. 77"></div>
    </div>
    <div class="fields" style="margin-top:.9rem">
      <div class="field"><label for="cv-db">dB</label><input id="cv-db" inputmode="decimal" placeholder="e.g. 6"></div>
      <div class="field"><label for="cv-vr">Voltage ratio</label><input id="cv-vr" inputmode="decimal" placeholder="e.g. 2"></div>
      <div class="field"><label for="cv-pr">Power ratio</label><input id="cv-pr" inputmode="decimal" placeholder="e.g. 4"></div>
    </div>
    <div class="fields" style="margin-top:.9rem">
      <div class="field"><label for="cv-re">Real</label><input id="cv-re" inputmode="decimal" placeholder="e.g. 3"></div>
      <div class="field"><label for="cv-im">Imaginary (j)</label><input id="cv-im" inputmode="decimal" placeholder="e.g. 4"></div>
      <div class="field"><label for="cv-mag">Magnitude</label><input id="cv-mag" inputmode="decimal" placeholder="e.g. 5"></div>
      <div class="field"><label for="cv-ang">Angle (&deg;)</label><input id="cv-ang" inputmode="decimal" placeholder="e.g. 53.13"></div>
    </div>
    <div class="fields" style="margin-top:.9rem">
      <div class="field"><label for="cv-deg">Degrees</label><input id="cv-deg" inputmode="decimal" placeholder="e.g. 90"></div>
      <div class="field"><label for="cv-rad">Radians</label><input id="cv-rad" inputmode="decimal" placeholder="e.g. 1.5708"></div>
    </div>
    <p class="note">Edit either side of a pair; the rest follows. dB assumes 20&middot;log<sub>10</sub> for voltage and 10&middot;log<sub>10</sub> for power.</p>
    <button class="reset" data-reset="cv">Reset</button>
  </div>
</div>
</section>

</main>

<footer class="site"><div class="wrap">
<p class="legend"><b>Highlighted</b> fields are calculated from what you entered &mdash; type in one and it becomes an input instead.</p>
<p>EE Calculator &mdash; all calculation runs locally in this page; nothing leaves your machine.</p>
</div></footer>

<script>
"use strict";

/* ---------- value parsing & formatting ---------- */

const MULT = { p:1e-12, n:1e-9, u:1e-6, "\u00b5":1e-6, m:1e-3, k:1e3, K:1e3, M:1e6, G:1e9 };

function parseVal(s) {
  // strip ohm signs, Hz, V/F/H/W unit letters (trailing only, so m/k/M suffixes survive)
  s = String(s == null ? "" : s).trim()
      .replace(/\u03a9|ohms?|hz$/gi, "")
      .replace(/[VFHWA]$/, "")
      .replace(/\s+/g, "");
  if (!s) return NaN;
  let m = s.match(/^-?(\d+)([pnum\u00b5kKMG])(\d+)$/);           // 4k7 style
  if (m) {
    const v = parseFloat(m[1] + "." + m[3]) * MULT[m[2]];
    return s[0] === "-" ? -v : v;
  }
  m = s.match(/^([-+]?[\d.]+(?:[eE][-+]?\d+)?)([pnum\u00b5kKMG])?$/);
  if (!m) return NaN;
  const v = parseFloat(m[1]);
  return m[2] ? v * MULT[m[2]] : v;
}

function fmt(v, unit) {
  if (!isFinite(v)) return "\u2014";
  if (v === 0) return "0 " + unit;
  const neg = v < 0 ? "-" : "";
  v = Math.abs(v);
  const PRE = [[1e9,"G"],[1e6,"M"],[1e3,"k"],[1,""],[1e-3,"m"],[1e-6,"\u00b5"],[1e-9,"n"],[1e-12,"p"]];
  let f = 1e-12, p = "p";
  for (const [fac, pre] of PRE) { if (v >= fac * 0.9999995) { f = fac; p = pre; break; } }
  let n = v / f;
  let str = n.toPrecision(4);
  if (str.indexOf("e") === -1 && str.indexOf(".") !== -1) str = str.replace(/\.?0+$/, "");
  return neg + str + " " + p + unit;
}

/* Read an input; mark it red when non-empty but unparseable. Returns NaN when empty or bad. */
function val(id) {
  const el = document.getElementById(id);
  const raw = el.value.trim();
  const v = raw ? parseVal(raw) : NaN;
  el.classList.toggle("bad", raw !== "" && !isFinite(v));
  return v;
}

function render(id, rows) {
  const dl = document.getElementById(id);
  dl.innerHTML = rows.map(function (r) {
    return "<dt>" + r[0] + "</dt><dd" + (r[2] ? ' class="' + r[2] + '"' : "") + ">" + r[1] + "</dd>";
  }).join("");
}

/* ---------- solved values go back into the input boxes ----------

   A solver writes its answer into the field it solved for and tags it
   `computed`, so the page reads like a filled-in form rather than a form plus
   a separate answer sheet. Two rules keep that honest:
     - every recalculation first empties the fields still tagged `computed`,
       so a stale answer can never be mistaken for an input, and
     - typing in a field drops the tag (see the input wiring), so the value
       the user just entered survives that clearing and becomes an input.
   Derived quantities with no box of their own (ratios, powers, currents)
   still go to the results list. */

function clearComputed(ids) {
  for (const id of ids) {
    const el = document.getElementById(id);
    if (el && el.classList.contains("computed")) { el.value = ""; el.classList.remove("computed"); }
  }
}

/* Compact SI form for writing back into a field: 4286 -> "4.286k".
   Round-trips through parseVal, so a computed value can be re-read as input. */
function fmtField(v) {
  if (!isFinite(v)) return "";
  if (v === 0) return "0";
  const neg = v < 0 ? "-" : "";
  v = Math.abs(v);
  const PRE = [[1e9,"G"],[1e6,"M"],[1e3,"k"],[1,""],[1e-3,"m"],[1e-6,"u"],[1e-9,"n"],[1e-12,"p"]];
  let f = 1e-12, pre = "p";
  for (const [fac, sym] of PRE) { if (v >= fac * 0.9999995) { f = fac; pre = sym; break; } }
  let str = (v / f).toPrecision(5);
  if (str.indexOf("e") === -1 && str.indexOf(".") !== -1) str = str.replace(/\.?0+$/, "");
  return neg + str + pre;
}

/* Read a number that has a sensible default, WITHOUT silently swallowing a
   wrong entry. An empty box takes the default; a box holding something
   unparseable or outside `lo`..`hi` is marked bad and returns NaN, so the
   caller stops rather than quietly substituting the default. Entering an
   epsilon of 1 for air used to hand back FR-4 with no warning. */
function numOr(id, dflt, lo, hi) {
  const el = document.getElementById(id);
  if (!el) return dflt;
  const raw = el.value.trim();
  if (raw === "") { el.classList.remove("bad"); return dflt; }
  const v = parseVal(raw);
  const ok = isFinite(v) && (lo === undefined || v >= lo) && (hi === undefined || v <= hi);
  el.classList.toggle("bad", !ok);
  return ok ? v : NaN;
}

/* Same idea for a dimension box whose bare numbers mean micrometres.
   `via-tp` is labelled (um) but was read with the SI-suffix parser, so "35u"
   became 3.5e-5 mm of plating and the card reported nonsense confidently. */
function valDimUm(id, dflt) {
  const el = document.getElementById(id);
  if (!el) return dflt;
  const raw = el.value.trim();
  if (raw === "") { el.classList.remove("bad"); return dflt; }
  const v = parseDimMM(/[a-z"]/i.test(raw) ? raw : raw + "um");
  const ok = isFinite(v) && v > 0;
  el.classList.toggle("bad", !ok);
  return ok ? v : NaN;
}

function setComputed(id, v) {
  const el = document.getElementById(id);
  if (!el) return;
  el.value = typeof v === "string" ? v : fmtField(v);
  el.classList.add("computed");
  el.classList.remove("bad");
}

/* ---------- shared board settings ----------

   Copper weight, temperature rise and ambient describe the board, not any one
   calculation, so they live in one strip and every card reads them from here.
   Before this they were repeated on six cards and could disagree. */

/* Each of these appears on several cards, because that is where you want it
   while you are working, but there is only one value behind them: editing any
   copy writes through to the rest and recalculates everything. The first copy
   in document order is the one read. */
function mirrors(group) { return document.querySelectorAll('[data-mirror="' + group + '"]'); }
function mirrorId(group) { const m = mirrors(group)[0]; return m ? m.id : null; }

function readMirror(group, dflt, lo, hi) {
  const id = mirrorId(group);
  if (!id) return dflt;
  const v = numOr(id, dflt, lo, hi);
  const bad = document.getElementById(id).classList.contains("bad");
  mirrors(group).forEach(function (el) { el.classList.toggle("bad", bad); });
  return v;
}

function gCopperMM() {
  const id = mirrorId("copper");
  return id ? parseFloat(document.getElementById(id).value) / 1000 : 0.035;
}
function gTempRise() { return readMirror("dt", 10, 0.01); }
function gAmbient() { return readMirror("ta", 25, -273.15); }
function gSeries() { const id = mirrorId("series"); return id ? document.getElementById(id).value : "E96"; }

/* ---------- E-series ---------- */

const E12 = [1.0,1.2,1.5,1.8,2.2,2.7,3.3,3.9,4.7,5.6,6.8,8.2];
const E24 = [1.0,1.1,1.2,1.3,1.5,1.6,1.8,2.0,2.2,2.4,2.7,3.0,3.3,3.6,3.9,4.3,4.7,5.1,5.6,6.2,6.8,7.5,8.2,9.1];
const E96 = [1.00,1.02,1.05,1.07,1.10,1.13,1.15,1.18,1.21,1.24,1.27,1.30,1.33,1.37,1.40,1.43,1.47,1.50,
             1.54,1.58,1.62,1.65,1.69,1.74,1.78,1.82,1.87,1.91,1.96,2.00,2.05,2.10,2.15,2.21,2.26,2.32,
             2.37,2.43,2.49,2.55,2.61,2.67,2.74,2.80,2.87,2.94,3.01,3.09,3.16,3.24,3.32,3.40,3.48,3.57,
             3.65,3.74,3.83,3.92,4.02,4.12,4.22,4.32,4.42,4.53,4.64,4.75,4.87,4.99,5.11,5.23,5.36,5.49,
             5.62,5.76,5.90,6.04,6.19,6.34,6.49,6.65,6.81,6.98,7.15,7.32,7.50,7.68,7.87,8.06,8.25,8.45,
             8.66,8.87,9.09,9.31,9.53,9.76];
const SERIES = { E12: E12, E24: E24, E96: E96 };

/* Decade-scaled series values. toPrecision(3) clears float noise without
   destroying small decades — the base values carry at most 3 significant
   digits, so this is exact for pF as well as Mohm. */
function seriesValues(name, decMin, decMax) {
  const base = SERIES[name], out = [];
  for (let d = decMin; d <= decMax; d++)
    for (const b of base) out.push(Number((b * Math.pow(10, d)).toPrecision(3)));
  return out;
}

/* Nearest series value to x (sorted array). */
function snap(sorted, x) {
  let lo = 0, hi = sorted.length - 1;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (sorted[mid] < x) lo = mid + 1; else hi = mid; }
  if (lo > 0 && Math.abs(sorted[lo - 1] - x) <= Math.abs(sorted[lo] - x)) lo--;
  return sorted[lo];
}

/* ---------- Ohm's law ---------- */

function calcOhm() {
  clearComputed(["ohm-v","ohm-i","ohm-r","ohm-p"]);
  const V = val("ohm-v"), I = val("ohm-i"), R = val("ohm-r"), P = val("ohm-p");
  const given = [["V",V],["I",I],["R",R],["P",P]].filter(function (x) { return isFinite(x[1]); });
  if (given.length < 2) { render("ohm-out", given.length ? [["", "Enter one more value.", ""]] : []); return; }
  const rows = [];
  if (given.length > 2) rows.push(["", "More than two values entered — solving from " + given[0][0] + " and " + given[1][0] + ".", "warn"]);
  const g = solveOhm(given[0], given[1]);
  if (!isFinite(g.V) || !isFinite(g.I) || !isFinite(g.R) || !isFinite(g.P)) {
    render("ohm-out", [["", "Those values give no real solution — check for a zero or negative entry.", "err"]]);
    return;
  }
  const box = { V: "ohm-v", I: "ohm-i", R: "ohm-r", P: "ohm-p" };
  for (const k in box) if (!isFinite(val(box[k]))) setComputed(box[k], g[k]);
  render("ohm-out", rows);
}

/* Returns all four quantities from any two. */
function solveOhm(a, b) {
  const g = {}; g[a[0]] = a[1]; g[b[0]] = b[1];
  let V = g.V, I = g.I, R = g.R, P = g.P;
  if (V != null && I != null) { R = V / I; P = V * I; }
  else if (V != null && R != null) { I = V / R; P = V * V / R; }
  else if (V != null && P != null) { I = P / V; R = V * V / P; }
  else if (I != null && R != null) { V = I * R; P = I * I * R; }
  else if (I != null && P != null) { V = P / I; R = P / (I * I); }
  else if (R != null && P != null) { V = Math.sqrt(P * R); I = Math.sqrt(P / R); }
  return { V: V, I: I, R: R, P: P };
}

/* ---------- resistor divider ---------- */

/* Unified divider solver: any three of Vin, Vout, R1, R2 determine the fourth.
   Optional constant load current IL drawn out of the midpoint; KCL there gives
   I(R1) = I(R2) + IL, so with both legs fixed Vout = (Vin - R1*IL)/(1 + R1/R2),
   R2 = Vout/((Vin-Vout)/R1 - IL), R1 = (Vin-Vout)/(Vout/R2 + IL), and
   Vin = Vout + R1*(Vout/R2 + IL).
   Optional total resistance T = R1+R2: with only Vin and Vout it makes both
   legs solvable (IL=0: R1 = (Vin-Vout)*T/Vin; IL>0: IL*R1^2 - (Vin+IL*T)*R1
   + (Vin-Vout)*T = 0, physical root is the smaller one), and with one leg
   known it stands in for the other. Vin+Vout alone also trigger a search of
   E-series pairs, steered toward T when given. */
function calcDivider() {
  clearComputed(["div-vin","div-vout","div-r1","div-r2","div-rtot"]);
  const vin = val("div-vin"), vout = val("div-vout");
  let r1 = val("div-r1"), r2 = val("div-r2");
  const ilRaw = val("div-iload"), rtotRaw = val("div-rtot");
  const il = isFinite(ilRaw) ? ilRaw : 0;
  const rtot = isFinite(rtotRaw) && rtotRaw > 0 ? rtotRaw : NaN;
  const table = document.getElementById("div-table"), note = document.getElementById("div-note");
  table.hidden = true; note.textContent = ""; note.className = "note";
  if (il < 0) { render("div-out", [["", "Load current must be zero or positive.", "err"]]); return; }
  if ((isFinite(r1) && !(r1 > 0)) || (isFinite(r2) && !(r2 > 0))) { render("div-out", [["", "Resistor values must be positive.", "err"]]); return; }
  const rows = [];
  const series = gSeries();

  // Total R can stand in for a missing leg when the other is known.
  let legFromTotal = false;
  if (isFinite(rtot) && isFinite(r1) !== isFinite(r2)) {
    legFromTotal = true;
    if (isFinite(r1)) {
      if (rtot <= r1) { render("div-out", [["", "Total R must exceed R1.", "err"]]); return; }
      r2 = rtot - r1; setComputed("div-r2", r2);
    } else {
      if (rtot <= r2) { render("div-out", [["", "Total R must exceed R2.", "err"]]); return; }
      r1 = rtot - r2; setComputed("div-r1", r1);
    }
  }

  const have = { Vin: isFinite(vin), Vout: isFinite(vout), R1: isFinite(r1), R2: isFinite(r2) };
  const count = Object.values(have).filter(Boolean).length;

  // Only the two voltages: exact legs from total R (when given) + E-series pair search.
  if (count === 2 && have.Vin && have.Vout) {
    if (!(vin > 0) || !(vout > 0) || vout >= vin) { render("div-out", [["", "Needs 0 < V<sub>out</sub> < V<sub>in</sub> — a plain divider can only step down.", "err"]]); return; }
    if (isFinite(rtot)) {
      let er1;
      if (il > 0) {
        const disc = Math.pow(vin + il * rtot, 2) - 4 * il * (vin - vout) * rtot;
        er1 = (vin + il * rtot - Math.sqrt(disc)) / (2 * il);
      } else {
        er1 = (vin - vout) * rtot / vin;
      }
      const er2 = rtot - er1;
      if (!isFinite(er1) || !(er1 > 0) || !(er2 > 0)) {
        rows.push(["", "No exact solution at this total — the load current is too large for it. Lower the total R or the load.", "err"]);
      } else {
        setComputed("div-r1", er1);
        setComputed("div-r2", er2);
        const i1 = (vin - vout) / er1;
        rows.push(["Current in R1 / R2", fmt(i1, "A") + " / " + fmt(i1 - il, "A")]);
        if (il > 0) {
          const ratio = (i1 - il) / il;
          rows.push(["Bleed / load ratio", ratio.toPrecision(3) + (ratio < 10 ? " — a soft divider; V<sub>out</sub> moves if the load varies" : "")]);
        }
      }
    }
    pairSearch(vin, vout, rtot, il, series);
    render("div-out", rows);
    return;
  }

  if (count < 3) {
    render("div-out", count ? [["", "Enter " + (3 - count) + " more value" + (count === 2 ? "" : "s") + " — any three of V<sub>in</sub>, V<sub>out</sub>, R1, R2, or just the two voltages for a pair search.", ""]] : []);
    return;
  }
  if (!legFromTotal && isFinite(rtot) && have.R1 && have.R2) rows.push(["", "Total R ignored — both legs are already set.", "warn"]);
  let solve = count === 4 ? "Vout" : Object.keys(have).find(function (k) { return !have[k]; });
  if (count === 4) rows.push(["", "All four values entered — treating V<sub>out</sub> as the one to check.", "warn"]);

  // Solve the missing quantity; sr1/sr2/svin/svout become the operating point.
  let sr1 = r1, sr2 = r2, svin = vin, svout = vout;
  if (solve === "R1" || solve === "R2") {
    if (!(vin > 0) || !(vout > 0) || vout >= vin) { render("div-out", [["", "Solving a resistor needs 0 < V<sub>out</sub> < V<sub>in</sub>.", "err"]]); return; }
    let exact;
    if (solve === "R2") {
      const i2 = (vin - vout) / r1 - il;
      if (i2 <= 0) { render("div-out", [["", "The load alone drops " + fmt(il * r1, "V") + " across R1 — V<sub>out</sub> is unreachable. Use a smaller R1 or less load.", "err"]]); return; }
      exact = vout / i2;
    } else {
      exact = (vin - vout) / (vout / r2 + il);
    }
    setComputed(solve === "R1" ? "div-r1" : "div-r2", exact);
    if (solve === "R1") sr1 = exact; else sr2 = exact;
    const std = snap(seriesValues(series, -1, 7), exact);   // 100 mohm .. 97.6 Mohm
    const vStd = solve === "R1" ? (svin - std * il) / (1 + std / sr2)
                                : (svin - sr1 * il) / (1 + sr1 / std);
    rows.push(["Nearest " + series, fmt(std, "Ω") + " — gives " + fmt(vStd, "V") + " (" + ((vStd - vout) / vout * 100).toFixed(3) + " %)"]);
  } else if (solve === "Vout") {
    svout = (vin - r1 * il) / (1 + r1 / r2);
    if (svout <= 0) { render("div-out", [["", "The load pulls the midpoint to zero — V<sub>out</sub> would be negative.", "err"]]); return; }
    if (count !== 4) setComputed("div-vout", svout);
    else rows.push(["V<sub>out</sub> from R1 / R2", fmt(svout, "V") + " (entered " + fmt(vout, "V") + ")"]);
  } else {                                                  // solve Vin
    if (!(vout > 0)) { render("div-out", [["", "V<sub>out</sub> must be positive.", "err"]]); return; }
    svin = vout + r1 * (vout / r2 + il);
    setComputed("div-vin", svin);
  }

  if (!isFinite(rtot) && isFinite(sr1) && isFinite(sr2)) setComputed("div-rtot", sr1 + sr2);

  const i1 = (svin - svout) / sr1, i2 = svout / sr2;
  rows.push(["Ratio V<sub>out</sub>/V<sub>in</sub>", (svout / svin).toPrecision(4)]);
  rows.push(["Current in R1", fmt(i1, "A")]);
  rows.push(["Current in R2", fmt(i2, "A")]);
  rows.push(["P in R1 / R2", fmt(i1 * i1 * sr1, "W") + " / " + fmt(i2 * i2 * sr2, "W")]);
  rows.push(["Total power from V<sub>in</sub>", fmt(svin * i1, "W")]);
  if (il > 0) {
    const ratio = i2 / il;
    rows.push(["Bleed / load ratio", ratio.toPrecision(3) + (ratio < 10 ? " — a soft divider; V<sub>out</sub> moves if the load varies" : "")]);
  }
  render("div-out", rows);
}

/* Search E-series pairs for Vin -> Vout, honoring the load current: for each
   series R1, the ideal R2 = Vout/((Vin-Vout)/R1 - IL), snapped to the series.
   Ranked by loaded-Vout error, then log-distance of R1+R2 from the target
   total when one is given. Writes the divider card's table + note. */
function pairSearch(vin, vout, rtot, il, series) {
  const table = document.getElementById("div-table"), note = document.getElementById("div-note");
  const values = seriesValues(series, 1, 6);          // 10 ohm .. 9.76 Mohm
  const cands = [];
  for (const r1 of values) {
    const i2 = (vin - vout) / r1 - il;
    if (i2 <= 0) continue;                             // load eats all the R1 current
    const r2 = snap(values, vout / i2);
    const vo = (vin - r1 * il) / (1 + r1 / r2);
    const errRel = Math.abs(vo - vout) / vout;
    const totPenalty = isFinite(rtot) ? Math.abs(Math.log10((r1 + r2) / rtot)) : 0;
    cands.push({ r1: r1, r2: r2, vo: vo, err: errRel, score: errRel * 100 + totPenalty });
  }
  if (!cands.length) {
    note.textContent = "No workable pair \u2014 the load current is too large for this Vin/Vout in the searched range.";
    note.className = "note err";
    return;
  }
  cands.sort(function (a, b) { return a.score - b.score; });
  const seen = new Set(), top = [];
  for (const c of cands) {
    const key = c.r1 + "/" + c.r2;
    if (seen.has(key)) continue;
    seen.add(key); top.push(c);
    if (top.length === 5) break;
  }
  document.getElementById("div-body").innerHTML = top.map(function (c) {
    const i1 = (vin - c.vo) / c.r1;
    return "<tr><td>" + fmt(c.r1, "\u03a9") + "</td><td>" + fmt(c.r2, "\u03a9") + "</td><td>" +
      fmt(c.vo, "V") + "</td><td>" + (c.err * 100).toFixed(3) + " %</td><td>" +
      fmt(i1, "A") + "</td><td>" + fmt(c.r1 + c.r2, "\u03a9") + "</td></tr>";
  }).join("");
  table.hidden = false;
  note.textContent = "Best " + series + " pairs" + (il > 0 ? " (load included)" : "") + ", ranked by Vout error" +
    (isFinite(rtot) ? ", then closeness to the requested total resistance." : ". Enter a total resistance to steer divider current.");
}

/* ---------- series / parallel ---------- */

function calcSP() {
  const raw = document.getElementById("sp-list").value.trim();
  const type = document.getElementById("sp-type").value;
  const UNIT = { R: "\u03a9", C: "F", L: "H" }[type];
  if (!raw) { render("sp-out", []); return; }
  const parts = raw.split(/[\s,;]+/).filter(Boolean);
  const vals = parts.map(parseVal);
  const bad = parts.filter(function (x, i) { return !isFinite(vals[i]) || vals[i] <= 0; });
  if (bad.length) { render("sp-out", [["", "Could not read: " + bad.join(", "), "err"]]); return; }
  const sum = vals.reduce(function (a, b) { return a + b; }, 0);
  const recip = 1 / vals.reduce(function (a, b) { return a + 1 / b; }, 0);
  /* Capacitors are the mirror image of resistors and inductors: charge divides
     where current would add, so series and parallel swap. */
  const ser = type === "C" ? recip : sum;
  const par = type === "C" ? sum : recip;
  const rows = [["Values", vals.length + ""],
                ["Series", fmt(ser, UNIT)],
                ["Parallel", fmt(par, UNIT)]];
  if (type === "C") rows.push(["", "Capacitors invert: they add in parallel and divide in series.", ""]);
  const v = val("sp-v");
  if (type === "R" && isFinite(v) && v > 0) {
    const iSer = v / sum;
    rows.push(["Series string at " + fmt(v, "V"), fmt(iSer, "A") + " through every element, " + fmt(v * iSer, "W") + " total"]);
    vals.forEach(function (r, i) {
      rows.push(["&nbsp;&nbsp;element " + (i + 1) + " (" + fmt(r, "\u03a9") + ")",
                 fmt(iSer * r, "V") + ", " + fmt(iSer * iSer * r, "W")]);
    });
    rows.push(["Parallel bank at " + fmt(v, "V"), fmt(v / par, "A") + " total, " + fmt(v * v / par, "W") + " total"]);
  }
  render("sp-out", rows);
}

/* ---------- RC filter ---------- */

/* ---------- filter design ----------

   One card for RC, RL and LC in either direction. Order means n cascaded
   identical sections, buffered so they do not load each other, which is what
   an engineer actually builds when they want more rolloff from the same
   parts. That has a consequence worth surfacing: the overall -3 dB point of a
   cascade is NOT the section corner. For n identical first-order sections it
   sits at f0*sqrt(2^(1/n) - 1) for a low-pass, which for four sections is
   0.435*f0 - a factor of more than two, and a classic way to design an
   anti-alias filter with the wrong bandwidth. */

const FLT_SAMPLES = 240;

/* Which element sits in series and which shunts to ground. A low-pass passes
   lows through the series element, so that element must be the one whose
   impedance RISES with frequency. */
function fltTopology(type, resp) {
  if (type === "rc") return resp === "lp" ? ["R", "C"] : ["C", "R"];
  if (type === "rl") return resp === "lp" ? ["L", "R"] : ["R", "L"];
  return resp === "lp" ? ["L", "C"] : ["C", "L"];
}

/* Linear magnitude at x = f / f0. */
function fltMag(x, type, resp, order, Q) {
  if (type === "lc") {
    const sections = Math.max(1, Math.round(order / 2));
    const den = Math.sqrt(Math.pow(1 - x * x, 2) + Math.pow(x / Q, 2));
    const base = resp === "lp" ? 1 / den : (x * x) / den;
    return Math.pow(base, sections);
  }
  const base = resp === "lp" ? 1 / Math.sqrt(1 + x * x) : x / Math.sqrt(1 + x * x);
  return Math.pow(base, order);
}

function fltDb(x, st) { return 20 * Math.log10(Math.max(fltMag(x, st.type, st.resp, st.order, st.Q), 1e-12)); }

/* ---- topology diagram ---- */

function symSeries(kind, x0, x1, y) {
  const mid = (x0 + x1) / 2;
  if (kind === "R") {
    return '<path class="wire" d="M' + x0 + ' ' + y + ' H' + (mid - 22) + '"/>' +
           '<rect class="wire" x="' + (mid - 22) + '" y="' + (y - 8) + '" width="44" height="16"/>' +
           '<path class="wire" d="M' + (mid + 22) + ' ' + y + ' H' + x1 + '"/>';
  }
  if (kind === "C") {
    return '<path class="wire" d="M' + x0 + ' ' + y + ' H' + (mid - 5) + '"/>' +
           '<path class="wire" d="M' + (mid - 5) + ' ' + (y - 12) + ' V' + (y + 12) + '"/>' +
           '<path class="wire" d="M' + (mid + 5) + ' ' + (y - 12) + ' V' + (y + 12) + '"/>' +
           '<path class="wire" d="M' + (mid + 5) + ' ' + y + ' H' + x1 + '"/>';
  }
  let d = "M" + x0 + " " + y + " H" + (mid - 21);
  for (let k = 0; k < 3; k++) d += " A7 7 0 0 1 " + (mid - 21 + (k + 1) * 14) + " " + y;
  d += " H" + x1;
  return '<path class="wire" d="' + d + '"/>';
}

function symShunt(kind, x, y0, y1) {
  const mid = (y0 + y1) / 2;
  if (kind === "R") {
    return '<path class="wire" d="M' + x + ' ' + y0 + ' V' + (mid - 18) + '"/>' +
           '<rect class="wire" x="' + (x - 8) + '" y="' + (mid - 18) + '" width="16" height="36"/>' +
           '<path class="wire" d="M' + x + ' ' + (mid + 18) + ' V' + y1 + '"/>';
  }
  if (kind === "C") {
    return '<path class="wire" d="M' + x + ' ' + y0 + ' V' + (mid - 5) + '"/>' +
           '<path class="wire" d="M' + (x - 13) + ' ' + (mid - 5) + ' H' + (x + 13) + '"/>' +
           '<path class="wire" d="M' + (x - 13) + ' ' + (mid + 5) + ' H' + (x + 13) + '"/>' +
           '<path class="wire" d="M' + x + ' ' + (mid + 5) + ' V' + y1 + '"/>';
  }
  let d = "M" + x + " " + y0 + " V" + (mid - 21);
  for (let k = 0; k < 3; k++) d += " A7 7 0 0 1 " + x + " " + (mid - 21 + (k + 1) * 14);
  d += " V" + y1;
  return '<path class="wire" d="' + d + '"/>';
}

function drawTopology(type, resp, order) {
  const t = fltTopology(type, resp);
  const NAME = { R: "R", C: "C", L: "L" };
  const svg = [
    '<svg class="schem" width="235" height="150" viewBox="0 0 235 150" role="img" aria-label="' +
      (resp === "lp" ? "Low" : "High") + "-pass " + type.toUpperCase() + ' section: ' +
      NAME[t[0]] + ' in series, ' + NAME[t[1]] + ' to ground">',
    '<circle class="wire" cx="16" cy="40" r="3.5"/><text x="6" y="26">in</text>',
    symSeries(t[0], 19.5, 150, 40),
    '<text x="72" y="20">' + NAME[t[0]] + '</text>',
    '<circle class="dot" cx="150" cy="40" r="3"/>',
    '<path class="wire" d="M150 40 H196"/>',
    '<circle class="wire" cx="199.5" cy="40" r="3.5"/><text x="196" y="26">out</text>',
    symShunt(t[1], 150, 40, 118),
    '<text x="163" y="84">' + NAME[t[1]] + '</text>',
    '<path class="wire" d="M136 118 H164 M141 125 H159 M146 132 H154"/>'
  ];
  if (order > 1) {
    svg.push('<text x="6" y="146">\u00d7 ' + order + ' identical sections, buffered</text>');
  }
  svg.push("</svg>");
  document.getElementById("flt-diagram").innerHTML = svg.join("");
}

/* ---- magnitude plot ----

   One series, so no legend: the card heading names it. Grid and axes are
   solid hairlines a shade off the surface; the curve is the only saturated
   ink. Every value the hover shows is also in the results list below, so the
   plot enhances rather than gates. */

const fltGraph = { pts: [], st: null, box: null };

function drawGraph(st) {
  const W = 560, H = 210, ML = 46, MR = 14, MT = 12, MB = 34;
  const pw = W - ML - MR, ph = H - MT - MB;
  const DEC = 2;                                  // decades either side of f0
  const pts = [];
  let lo = 0;
  for (let i = 0; i < FLT_SAMPLES; i++) {
    const lx = -DEC + (2 * DEC) * i / (FLT_SAMPLES - 1);
    const db = fltDb(Math.pow(10, lx), st);
    pts.push([lx, db]);
    if (db < lo) lo = db;
  }
  const yMax = Math.max(5, Math.ceil(Math.max.apply(null, pts.map(function (q) { return q[1]; })) / 5) * 5 + 5);
  const yMin = Math.max(-120, Math.floor(Math.max(lo, -120) / 20) * 20);
  const X = function (lx) { return ML + (lx + DEC) / (2 * DEC) * pw; };
  const Y = function (db) { return MT + (yMax - db) / (yMax - yMin) * ph; };

  const out = ['<svg width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + " " + H + '">'];
  for (let d = -DEC; d <= DEC; d++) {
    out.push('<path class="grid" d="M' + X(d).toFixed(1) + " " + MT + " V" + (MT + ph) + '"/>');
    const f = st.f0 * Math.pow(10, d);
    out.push('<text x="' + X(d).toFixed(1) + '" y="' + (H - 18) + '" text-anchor="middle">' + fmt(f, "Hz") + "</text>");
  }
  for (let db = yMin; db <= yMax; db += 20) {
    out.push('<path class="grid" d="M' + ML + " " + Y(db).toFixed(1) + " H" + (ML + pw) + '"/>');
    out.push('<text x="' + (ML - 6) + '" y="' + (Y(db) + 3.5).toFixed(1) + '" text-anchor="end">' + db + "</text>");
  }
  out.push('<text x="' + (ML - 6) + '" y="' + (MT - 2) + '" text-anchor="end">dB</text>');
  out.push('<path class="axis" d="M' + ML + " " + MT + " V" + (MT + ph) + " H" + (ML + pw) + '"/>');
  let d2 = "M";
  pts.forEach(function (q, i) { d2 += (i ? " L" : "") + X(q[0]).toFixed(1) + " " + Y(q[1]).toFixed(1); });
  out.push('<path class="curve" d="' + d2 + '"/>');
  out.push('<g id="flt-cursor"></g>');
  out.push("</svg>");
  document.getElementById("flt-graph").innerHTML = out.join("");
  fltGraph.pts = pts;
  fltGraph.st = st;
  fltGraph.box = { W: W, H: H, ML: ML, MT: MT, pw: pw, ph: ph, DEC: DEC, yMax: yMax, yMin: yMin };
}

/* The crosshair snaps to the nearest sample, so the reader aims at a
   frequency rather than at a 2px line. */
function moveCursor(clientX) {
  const host = document.getElementById("flt-graph");
  const svg = host.querySelector("svg");
  const g = host.querySelector("#flt-cursor");
  if (!svg || !g || !fltGraph.st) return;
  const b = fltGraph.box, r = svg.getBoundingClientRect();
  const px = (clientX - r.left) * (b.W / r.width);
  let i = Math.round((px - b.ML) / b.pw * (FLT_SAMPLES - 1));
  i = Math.max(0, Math.min(FLT_SAMPLES - 1, i));
  showCursorAt(i);
}

function showCursorAt(i) {
  const host = document.getElementById("flt-graph");
  const g = host.querySelector("#flt-cursor");
  if (!g || !fltGraph.st) return;
  fltGraph.index = i;
  const b = fltGraph.box, st = fltGraph.st, q = fltGraph.pts[i];
  const x = b.ML + (q[0] + b.DEC) / (2 * b.DEC) * b.pw;
  const y = b.MT + (b.yMax - q[1]) / (b.yMax - b.yMin) * b.ph;
  const f = st.f0 * Math.pow(10, q[0]);
  const right = x > b.ML + b.pw * 0.6;
  const tx = right ? x - 8 : x + 8;
  const anchor = right ? "end" : "start";
  /* value leads, label follows - the reader has the curve and wants the number */
  g.innerHTML =
    '<path class="hair" d="M' + x.toFixed(1) + " " + b.MT + " V" + (b.MT + b.ph) + '"/>' +
    '<circle class="knob" cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="4"/>' +
    '<text class="read" x="' + tx.toFixed(1) + '" y="' + Math.max(b.MT + 12, y - 10).toFixed(1) +
      '" text-anchor="' + anchor + '">' + q[1].toFixed(1) + " dB</text>" +
    '<text class="readlabel" x="' + tx.toFixed(1) + '" y="' + Math.max(b.MT + 24, y + 3).toFixed(1) +
      '" text-anchor="' + anchor + '">at ' + fmt(f, "Hz") + "</text>";
}

function calcFilter() {
  clearComputed(["flt-r", "flt-c", "flt-l", "flt-f"]);
  const type = document.getElementById("flt-type").value;
  const resp = document.getElementById("flt-resp").value;
  let order = parseInt(document.getElementById("flt-order").value, 10) || 1;
  const R = val("flt-r"), C = val("flt-c"), L = val("flt-l"), F = val("flt-f");
  const note = document.getElementById("flt-note");
  const TAU = 2 * Math.PI;
  const rows = [];

  /* an LC section is inherently second order, so its cascade steps in twos */
  if (type === "lc" && order % 2) order += 1;

  drawTopology(type, resp, order);

  let f0 = NaN, Q = NaN;
  if (type === "rc") {
    const have = [isFinite(R), isFinite(C), isFinite(F)].filter(Boolean).length;
    if (have < 2) { render("flt-out", []); document.getElementById("flt-graph").innerHTML = ""; note.innerHTML = "Give any two of R, C and the section corner."; return; }
    let r = R, c = C;
    if (isFinite(R) && isFinite(C)) { f0 = 1 / (TAU * R * C); if (!isFinite(F)) setComputed("flt-f", f0); }
    else if (isFinite(R) && isFinite(F)) { c = 1 / (TAU * R * F); setComputed("flt-c", c); f0 = F; }
    else { r = 1 / (TAU * C * F); setComputed("flt-r", r); f0 = F; }
    if (!(r > 0) || !(c > 0) || !(f0 > 0)) { render("flt-out", [["", "R, C and the corner must all be positive.", "err"]]); return; }
    rows.push(["Time constant &tau; = RC", fmt(r * c, "s")]);
    rows.push(["Rise time 10–90 %", fmt(2.197 * r * c, "s")]);
    rows.push(["Settling to 1 %", fmt(4.6 * r * c, "s")]);
  } else if (type === "rl") {
    const have = [isFinite(R), isFinite(L), isFinite(F)].filter(Boolean).length;
    if (have < 2) { render("flt-out", []); document.getElementById("flt-graph").innerHTML = ""; note.innerHTML = "Give any two of R, L and the section corner."; return; }
    let r = R, l = L;
    if (isFinite(R) && isFinite(L)) { f0 = R / (TAU * L); if (!isFinite(F)) setComputed("flt-f", f0); }
    else if (isFinite(R) && isFinite(F)) { l = R / (TAU * F); setComputed("flt-l", l); f0 = F; }
    else { r = TAU * L * F; setComputed("flt-r", r); f0 = F; }
    if (!(r > 0) || !(l > 0) || !(f0 > 0)) { render("flt-out", [["", "R, L and the corner must all be positive.", "err"]]); return; }
    rows.push(["Time constant &tau; = L/R", fmt(l / r, "s")]);
  } else {
    if (isFinite(L) && L > 0 && isFinite(C) && C > 0) {
      f0 = 1 / (TAU * Math.sqrt(L * C));
      if (!isFinite(F)) setComputed("flt-f", f0);
    } else if (isFinite(F) && F > 0 && isFinite(L) && L > 0) {
      const c = 1 / (L * Math.pow(TAU * F, 2)); setComputed("flt-c", c); f0 = F;
    } else if (isFinite(F) && F > 0 && isFinite(C) && C > 0) {
      const l = 1 / (C * Math.pow(TAU * F, 2)); setComputed("flt-l", l); f0 = F;
    } else {
      render("flt-out", []); document.getElementById("flt-graph").innerHTML = "";
      note.innerHTML = "Give L and C, or one of them with a target frequency.";
      return;
    }
    const l = val("flt-l") || L, c = val("flt-c") || C;
    const z0 = Math.sqrt(l / c);
    /* Loaded by R across the shunt element, the section damping is set by
       how R compares with sqrt(L/C). */
    /* Both directions come out the same: a series-L shunt-C low-pass loaded
       across C, and a series-C shunt-L high-pass loaded across L, both reduce
       to s^2 + s/(RC) + 1/(LC), so Q = R/sqrt(L/C) either way. Note this is
       the LOADED filter Q, not the Q of an unloaded resonator, which is its
       reciprocal - the label says which. */
    Q = isFinite(R) && R > 0 ? R / z0 : 0.7071;
    rows.push(["Characteristic impedance &radic;(L/C)", fmt(z0, "\u03a9")]);
    rows.push([isFinite(R) && R > 0 ? "Q with " + fmt(R, "\u03a9") + " load" : "Q (assumed, no load given)",
               Q.toPrecision(4) + (Q > 1.2 ? " \u2014 peaks before rolloff" : Q < 0.5 ? " \u2014 overdamped" : "")]);
  }

  const st = { type: type, resp: resp, order: order, Q: isFinite(Q) ? Q : 0.7071, f0: f0 };

  /* The cascade's own -3 dB point, which is not the section corner. */
  const k = Math.sqrt(Math.pow(2, 1 / (type === "lc" ? Math.max(1, order / 2) : order)) - 1);
  let f3 = f0;
  if (type !== "lc") f3 = resp === "lp" ? f0 * k : f0 / k;
  else if (order > 2) f3 = resp === "lp" ? f0 * Math.sqrt(k) : f0 / Math.sqrt(k);

  rows.unshift(["Section corner f<sub>0</sub>", fmt(f0, "Hz")]);
  const perSection = type === "lc" ? 40 : 20;
  rows.push(["Overall &minus;3 dB", fmt(f3, "Hz") +
             (Math.abs(f3 / f0 - 1) > 0.01
                ? " \u2014 " + (f3 / f0).toPrecision(3) + "\u00d7 the section corner, because the sections stack"
                : "")]);
  rows.push(["Rolloff", (type === "lc" ? order / 2 * 40 : order * 20) + " dB/decade (" +
             (type === "lc" ? order / 2 * 12 : order * 6) + " dB/octave)"]);
  /* the plot is not the only way to read these */
  [0.1, 0.5, 2, 10].forEach(function (m) {
    const x = resp === "lp" ? m : 1 / m;
    rows.push(["Attenuation at " + fmt(f0 * (resp === "lp" ? m : 1 / m), "Hz"),
               (function (d) { return Math.abs(d) < 1 ? d.toFixed(2) : d.toFixed(1); })(fltDb(x, st)) + " dB"]);
  });

  note.innerHTML = "Order means n identical sections in cascade, buffered so they do not load one another. " +
    "The cascade&rsquo;s &minus;3 dB point is not the section corner: for n first-order sections it lands at " +
    "f<sub>0</sub>&radic;(2<sup>1/n</sup>&minus;1) on a low-pass, which at 4th order is 0.435 f<sub>0</sub>. " +
    "Hover or arrow-key the plot to read the response at any frequency.";
  render("flt-out", rows);
  drawGraph(st);
  showCursorAt(Math.round(FLT_SAMPLES / 2));
  document.getElementById("flt-graph").setAttribute("aria-label",
    (resp === "lp" ? "Low" : "High") + "-pass " + type.toUpperCase() + " magnitude response, order " +
    order + ", section corner " + fmt(f0, "Hz") + ", rolloff " +
    (type === "lc" ? order / 2 * 40 : order * 20) + " dB per decade");
}

/* ---------- via shielding ---------- */

/* A via fence is a waveguide wall built out of holes: it works while the gaps
   are small against a wavelength and leaks once the pitch approaches a half
   wave. The usual working rule is a tenth of a wavelength, which is what the
   default here computes. */
function calcViaShield() {
  clearComputed(["vs-pitch"]);
  const er = numOr("vs-er", 4.3, 1);
  const frac = parseFloat(document.getElementById("vs-frac").value) || 10;
  let f = val("vs-f");
  const tr = val("vs-tr"), pitch = valDim("vs-pitch"), len = valDim("vs-len"), d = valDim("vs-d");
  if (!isFinite(er)) { render("vs-out", []); return; }
  const rows = [];
  if (!isFinite(f) && isFinite(tr) && tr > 0) {
    f = 0.35 / tr;
    rows.push(["Knee frequency from rise time", fmt(f, "Hz")]);
  }
  if (!isFinite(f) || !(f > 0)) { render("vs-out", [["", "Give a highest frequency, or a rise time to derive one from.", ""]]); return; }

  const vp = 299792458 / Math.sqrt(er);
  const lam = vp / f;
  const maxPitch = lam / frac;
  rows.push(["Wavelength in the board", fmt(lam, "m")]);
  rows.push(["Maximum pitch at \u03bb/" + frac, fmt(maxPitch, "m") + " (" + (maxPitch * 1000).toPrecision(3) + " mm)"]);
  rows.push(["Half-wave leak point", fmt(lam / 2, "m") + " \u2014 pitch must stay far below this"]);

  if (isFinite(pitch) && pitch > 0) {
    const ratio = lam / (pitch / 1000);
    const ok = pitch / 1000 <= maxPitch;
    rows.push(["Your pitch", (pitch).toPrecision(3) + " mm = \u03bb/" + ratio.toPrecision(3)]);
    rows.push(["Verdict", ok
                 ? "inside the \u03bb/" + frac + " rule, with " + ((maxPitch / (pitch / 1000) - 1) * 100).toFixed(0) + " % margin"
                 : "too coarse \u2014 tighten to " + (maxPitch * 1000).toPrecision(3) + " mm or accept leakage",
               ok ? "good" : "warn"]);
    if (isFinite(len) && len > 0) {
      const n = Math.floor(len / pitch) + 1;
      rows.push(["Vias along " + (len).toPrecision(3) + " mm", n + " per row, " + (2 * n) + " for a pair of rows"]);
    }
  } else {
    setComputed("vs-pitch", +(maxPitch * 1000).toPrecision(4) + "");
  }
  if (isFinite(d) && d > 0 && isFinite(pitch) && pitch > 0) {
    rows.push(["Gap between barrels", (pitch - d).toPrecision(3) + " mm" +
               (pitch - d < 0.2 ? " \u2014 tight for fabrication, check with your vendor" : "")]);
  }
  rows.push(["Model", "\u03bb/" + frac + " rule of thumb on the in-board wavelength. It bounds the leakage, "
             + "it does not compute it; a real shielding figure needs a field solver."]);
  render("vs-out", rows);
}

/* ---------- reactance ---------- */

function calcReact() {
  const f = val("re-f"), C0 = val("re-c"), L0 = val("re-l");
  const esl = val("re-esl"), esr = val("re-esr");
  const epc = val("re-epc"), dcr = val("re-dcr");
  const n = Math.max(1, Math.round(numOr("re-n", 1, 1) || 1));
  const rows = [];
  const TAU = 2 * Math.PI;

  /* paralleling n identical capacitors: C multiplies, ESL and ESR divide */
  const C = isFinite(C0) && C0 > 0 ? C0 * n : NaN;
  const Lp = isFinite(esl) && esl > 0 ? esl / n : NaN;
  const Rp = isFinite(esr) && esr >= 0 ? esr / n : NaN;
  if (n > 1 && isFinite(C)) {
    rows.push(["Bank of " + n, fmt(C, "F") +
               (isFinite(Lp) ? ", " + fmt(Lp, "H") + " ESL" : "") +
               (isFinite(Rp) ? ", " + fmt(Rp, "\u03a9") + " ESR" : "")]);
  }

  if (isFinite(f) && f > 0) {
    const w = TAU * f;
    if (isFinite(C)) rows.push(["X<sub>C</sub> at " + fmt(f, "Hz"), fmt(1 / (w * C), "\u03a9")]);
    if (isFinite(L0) && L0 > 0) rows.push(["X<sub>L</sub> at " + fmt(f, "Hz"), fmt(w * L0, "\u03a9")]);
  }
  if (isFinite(C) && isFinite(L0) && L0 > 0) {
    rows.push(["LC resonance", fmt(1 / (TAU * Math.sqrt(L0 * C)), "Hz")]);
  }

  /* real capacitor: C, ESL and ESR in series */
  if (isFinite(C) && isFinite(Lp)) {
    const srf = 1 / (TAU * Math.sqrt(Lp * C));
    rows.push(["Capacitor self-resonance", fmt(srf, "Hz")]);
    rows.push(["|Z| at its resonance", isFinite(Rp) ? fmt(Rp, "\u03a9") + " (ESR alone)" : "equal to ESR"]);
    if (isFinite(f) && f > 0) {
      const w = TAU * f;
      const x = w * Lp - 1 / (w * C);
      rows.push(["Capacitor |Z| at " + fmt(f, "Hz"),
                 fmt(Math.sqrt((isFinite(Rp) ? Rp * Rp : 0) + x * x), "\u03a9") +
                 (f > srf ? " \u2014 inductive, past self-resonance" : " \u2014 still capacitive")]);
    }
  }

  /* real inductor: L and DCR in series, winding capacitance across both */
  if (isFinite(L0) && L0 > 0 && isFinite(epc) && epc > 0) {
    const srfL = 1 / (TAU * Math.sqrt(L0 * epc));
    rows.push(["Inductor self-resonance", fmt(srfL, "Hz")]);
    if (isFinite(f) && f > 0) {
      const w = TAU * f;
      /* Z = (Rdc + jwL) in parallel with 1/(jwCp) */
      const sr = isFinite(dcr) && dcr >= 0 ? dcr : 0, si = w * L0;
      const pi = -1 / (w * epc);
      const nr = sr * 0 - si * pi, ni = sr * pi + si * 0;   // numerator Zs*Zp
      const dr = sr, di = si + pi;                           // denominator Zs+Zp
      const den = dr * dr + di * di;
      const zr = (nr * dr + ni * di) / den, zi = (ni * dr - nr * di) / den;
      rows.push(["Inductor |Z| at " + fmt(f, "Hz"), fmt(Math.hypot(zr, zi), "\u03a9") +
                 (f > srfL ? " \u2014 capacitive, past self-resonance" : " \u2014 still inductive")]);
      if (isFinite(dcr) && dcr > 0) rows.push(["Inductor Q at " + fmt(f, "Hz"), (w * L0 / dcr).toPrecision(4)]);
    }
    rows.push(["", "Above self-resonance an inductor behaves as a capacitor \u2014 a choke stops choking.", "warn"]);
  }

  if (!rows.length) rows.push(["", "Enter a frequency with a capacitance or an inductance; add ESL or winding capacitance for self-resonance.", ""]);
  render("re-out", rows);
}

/* ---------- LED resistor ---------- */

function calcLED() {
  clearComputed(["led-if","led-r"]);
  const vs = val("led-vs"), vf = val("led-vf");
  let iF = val("led-if"), r = val("led-r");
  if (!isFinite(vs) || !isFinite(vf)) { render("led-out", []); return; }
  if (vs <= vf) { render("led-out", [["", "Supply must exceed the LED forward voltage.", "err"]]); return; }
  if (!isFinite(iF) && !isFinite(r)) { render("led-out", [["", "Enter a forward current, or a resistor to check.", ""]]); return; }
  if (isFinite(iF) && iF <= 0) { render("led-out", [["", "Forward current must be positive.", "err"]]); return; }
  if (isFinite(r) && r <= 0) { render("led-out", [["", "Resistance must be positive.", "err"]]); return; }
  const rows = [];
  if (isFinite(iF) && !isFinite(r)) { r = (vs - vf) / iF; setComputed("led-r", r); }
  else if (isFinite(r) && !isFinite(iF)) { iF = (vs - vf) / r; setComputed("led-if", iF); }
  else rows.push(["Current through " + fmt(r, "Ω"), fmt((vs - vf) / r, "A")]);
  const series = gSeries();
  const vals = seriesValues(series, -1, 7);
  let std = vals[vals.length - 1];
  for (const v of vals) if (v >= r) { std = v; break; }
  const iStd = (vs - vf) / std;
  rows.push(["Next " + series + " up", fmt(std, "Ω") + " — gives " + fmt(iStd, "A")]);
  rows.push(["Resistor power", fmt(iStd * iStd * std, "W")]);
  rows.push(["LED power", fmt(vf * iStd, "W")]);
  render("led-out", rows);
}

/* ---------- divider accuracy ----------

   A divider's ratio k = R2/(R1+R2) only moves when the two legs move
   RELATIVE to each other: to first order dk/k = (1-k)*(d2 - d1). Two
   consequences worth seeing: the (1-k) factor means a lightly-dividing
   network is inherently more accurate than a heavy one, and matched parts
   with a common TCR contribute nothing at all, because their drift cancels
   in the difference. Worst case here is exact rather than first-order --
   both legs are evaluated at their opposing extremes. */

function calcAccuracy() {
  const r1 = val("ac-r1"), r2 = val("ac-r2"), vin = val("ac-vin");
  if (!isFinite(r1) || !isFinite(r2) || !(r1 > 0) || !(r2 > 0)) { render("ac-out", []); return; }
  const num = function (id, dflt) { const v = val(id); return isFinite(v) ? v : dflt; };
  const tol1 = num("ac-tol1", 1) / 100, tol2 = num("ac-tol2", 1) / 100;
  const tcr1 = num("ac-tcr1", 100), tcr2 = num("ac-tcr2", 100);
  const tmin = num("ac-tmin", -40), tmax = num("ac-tmax", 85), tnom = num("ac-tnom", 25);
  const age = num("ac-age", 0) * 1e-6;
  if (tmax < tmin) { render("ac-out", [["", "T max must be at or above T min.", "err"]]); return; }
  const dT = Math.max(Math.abs(tmax - tnom), Math.abs(tmin - tnom));
  const drift1 = Math.abs(tcr1) * 1e-6 * dT, drift2 = Math.abs(tcr2) * 1e-6 * dT;
  const d1 = tol1 + drift1 + age, d2 = tol2 + drift2 + age;   // worst-case relative spread per leg
  const k = r2 / (r1 + r2);

  // exact worst case: legs pushed to opposing extremes
  const kLo = (r2 * (1 - d2)) / (r1 * (1 + d1) + r2 * (1 - d2));
  const kHi = (r2 * (1 + d2)) / (r1 * (1 - d1) + r2 * (1 + d2));
  const wc = Math.max(Math.abs(kHi / k - 1), Math.abs(kLo / k - 1));

  // RSS: contributions treated as independent
  const s1 = Math.sqrt(tol1 * tol1 + drift1 * drift1 + age * age);
  const s2 = Math.sqrt(tol2 * tol2 + drift2 * drift2 + age * age);
  const rss = (1 - k) * Math.sqrt(s1 * s1 + s2 * s2);

  const pc = function (x) { return (x * 100).toPrecision(3) + " %"; };
  const pm = function (x) { return (x * 1e6).toFixed(0) + " ppm"; };
  const rows = [
    ["Nominal ratio", k.toPrecision(5) + " (" + pc(k) + " of V<sub>in</sub>)"],
    ["Tolerance contribution", "±" + pc((1 - k) * (tol1 + tol2)) + " worst case"],
    ["TCR contribution over ΔT " + dT.toFixed(0) + " °C",
     "±" + pc((1 - k) * (drift1 + drift2)) + " worst case, " +
     (tcr1 === tcr2 ? "0 % if the parts truly track" : "±" + pc((1 - k) * Math.abs(tcr2 - tcr1) * 1e-6 * dT) + " if they track")]
  ];
  if (age > 0) rows.push(["Ageing contribution", "±" + pc((1 - k) * 2 * age) + " worst case"]);
  rows.push(["Total ratio error — worst case", "±" + pc(wc) + " (±" + pm(wc) + ")"]);
  rows.push(["Total ratio error — RSS", "±" + pc(rss) + " (±" + pm(rss) + ")"]);
  if (isFinite(vin) && vin > 0) {
    rows.push(["V<sub>out</sub> nominal", fmt(vin * k, "V")]);
    rows.push(["V<sub>out</sub> worst-case window", fmt(vin * kLo, "V") + " … " + fmt(vin * kHi, "V")]);
  }
  rows.push(["Effective bits", "ratio resolved to " + Math.max(0, Math.log2(1 / (2 * wc))).toFixed(1) + " bits worst case"]);
  rows.push(["R1 spread", fmt(r1 * (1 - d1), "Ω") + " … " + fmt(r1 * (1 + d1), "Ω")]);
  rows.push(["R2 spread", fmt(r2 * (1 - d2), "Ω") + " … " + fmt(r2 * (1 + d2), "Ω")]);
  render("ac-out", rows);
}

/* ---------- number bases ---------- */

/* Parse an integer in a given radix, tolerating prefixes and separators. */
function parseInt_(raw, radix) {
  let t = String(raw).trim().replace(/[_\s]/g, "");
  if (!t) return null;
  let neg = false;
  if (t[0] === "-") { neg = true; t = t.slice(1); }
  else if (t[0] === "+") t = t.slice(1);
  const pre = { 16: /^0x/i, 2: /^0b/i, 8: /^0o/i }[radix];
  if (pre) t = t.replace(pre, "");
  if (!t) return null;
  const ok = { 10: /^[0-9]+$/, 16: /^[0-9a-f]+$/i, 2: /^[01]+$/, 8: /^[0-7]+$/ }[radix];
  if (!ok.test(t)) return null;
  let v;
  try { v = radix === 10 ? BigInt(t) : BigInt((radix === 16 ? "0x" : radix === 8 ? "0o" : "0b") + t); }
  catch (e) { return null; }
  return neg ? -v : v;
}

const NB_FIELDS = [["nb-dec", 10], ["nb-hex", 16], ["nb-bin", 2], ["nb-oct", 8]];

function showBases(v, fromId) {
  for (const [id, radix] of NB_FIELDS) {
    if (id === fromId) continue;
    const el = document.getElementById(id);
    const neg = v < 0n;
    const body = (neg ? -v : v).toString(radix);
    el.value = (neg ? "-" : "") + (radix === 16 ? "0x" + body.toUpperCase() : radix === 2 ? "0b" + body : radix === 8 ? "0o" + body : body);
    el.classList.add("computed");
  }
  const mag = v < 0n ? -v : v;
  const bits = mag === 0n ? 1 : mag.toString(2).length;
  const rows = [["Magnitude needs", bits + (bits === 1 ? " bit" : " bits") + (v < 0n ? ", plus a sign" : "")]];
  for (const w of [8, 16, 32, 64]) {
    const lim = 1n << BigInt(w);
    const fits = v < 0n ? (v >= -(lim >> 1n)) : (v < lim);
    if (!fits) continue;
    const tc = v < 0n ? lim + v : v;
    const hex = tc.toString(16).toUpperCase().padStart(w / 4, "0");
    rows.push([w + "-bit" + (v < 0n ? " two’s complement" : ""), "0x" + hex.replace(/(.{4})(?=.)/g, "$1 ")]);
    if (v >= 0n) break;
  }
  render("nb-out", rows);
}

/* ---------- PCB power ---------- */

const MIL = 0.0254;                                    // mm per mil
const RHO20 = 1.724e-8, ALPHA = 0.00393;               // copper, SI

/* Dimension fields: plain numbers are mm; mil / um / in suffixes accepted. */
function parseDimMM(s) {
  s = String(s == null ? "" : s).trim();
  const m = s.match(/^([-+]?[\d.]+(?:[eE][-+]?\d+)?)\s*(mm|mils?|um|µm|in(?:ch)?|")?$/i);
  if (!m) return NaN;
  const unit = (m[2] || "mm").toLowerCase();
  const mult = { mm: 1, mil: MIL, mils: MIL, um: 1e-3, "µm": 1e-3, "in": 25.4, inch: 25.4, '"': 25.4 };
  return parseFloat(m[1]) * mult[unit];
}

function valDim(id) {
  const el = document.getElementById(id);
  const raw = el.value.trim();
  const v = raw ? parseDimMM(raw) : NaN;
  el.classList.toggle("bad", raw !== "" && !isFinite(v));
  return v;
}

/* IPC-2221: I = k * dT^0.44 * A^0.725, A in mil^2 */
function ipcCurrent(aMil2, dT, k) { return k * Math.pow(dT, 0.44) * Math.pow(aMil2, 0.725); }
function ipcArea(i, dT, k) { return Math.pow(i / (k * Math.pow(dT, 0.44)), 1 / 0.725); }

function traceR(wMM, tMM, lenMM, tempC) {
  const rho = RHO20 * (1 + ALPHA * (tempC - 20));
  return rho * (lenMM / 1000) / ((wMM / 1000) * (tMM / 1000));
}

function calcTrace() {
  clearComputed(["tw-i","tw-w"]);
  const i = val("tw-i"), w = valDim("tw-w"), lenMM = valDim("tw-len"), f = val("tw-f");
  const dT = gTempRise();
  const ta = gAmbient();
  if (!isFinite(dT) || !isFinite(ta)) { render("tw-out", []); return; }
  const tMM = gCopperMM();
  const k = document.getElementById("tw-layer").value === "ext" ? 0.048 : 0.024;
  if (!isFinite(i) && !isFinite(w)) { render("tw-out", []); return; }
  const rows = [];
  let wMM = w, iVal = i, required = NaN;

  if (isFinite(i) && !isFinite(w)) {
    if (!(i > 0)) { render("tw-out", [["", "Current must be positive.", "err"]]); return; }
    const aMil2 = ipcArea(i, dT, k);
    wMM = (aMil2 / (tMM / MIL)) * MIL;
    setComputed("tw-w", +wMM.toPrecision(4) + "");
    rows.push(["Required width", (wMM / MIL).toFixed(1) + " mil"]);
  } else if (isFinite(w) && !isFinite(i)) {
    if (!(w > 0)) { render("tw-out", [["", "Width must be positive.", "err"]]); return; }
    iVal = ipcCurrent((w / MIL) * (tMM / MIL), dT, k);
    setComputed("tw-i", iVal);
    rows.push(["Width", (w / MIL).toFixed(1) + " mil"]);
  } else {
    required = i;
  }

  const aMil2 = (wMM / MIL) * (tMM / MIL);
  const aMM2 = wMM * tMM;
  const achievable = ipcCurrent(aMil2, dT, k);

  /* Showing what the design draws next to what the geometry can carry is the
     one presentation idea worth taking wholesale from Saturn: an undersized
     trace becomes obvious without doing the comparison in your head. */
  if (isFinite(required)) {
    const margin = (achievable / required - 1) * 100;
    rows.push(["Current required", fmt(required, "A")]);
    rows.push(["Current the copper can carry", fmt(achievable, "A") + " at \u0394T " + dT + " \u00b0C"]);
    rows.push(["Verdict", margin >= 0
                 ? margin.toFixed(0) + " % headroom"
                 : Math.abs(margin).toFixed(0) + " % short \u2014 undersized, widen the trace or accept a bigger rise",
               margin < 0 ? "err" : (margin < 20 ? "warn" : "good")]);
    if (margin < 0) {
      const need = (ipcArea(required, dT, k) / (tMM / MIL)) * MIL;
      rows.push(["Width needed for " + fmt(required, "A"), (need / MIL).toFixed(1) + " mil (" + need.toPrecision(3) + " mm)"]);
    }
    iVal = required;
  }

  rows.push(["Cross-section", aMil2.toFixed(1) + " mil&sup2; (" + aMM2.toPrecision(3) + " mm&sup2;)"]);
  if (isFinite(iVal) && iVal > 0) {
    rows.push(["Current density", (iVal / aMM2).toPrecision(4) + " A/mm&sup2; (" +
               (iVal / aMil2).toPrecision(3) + " A/mil&sup2;)"]);
  }

  if (isFinite(f) && f > 0) {
    /* Skin depth as a fraction of the copper is the useful form: it answers
       whether the thickness is being wasted at this frequency. */
    const delta = Math.sqrt(RHO20 / (Math.PI * f * 4e-7 * Math.PI));
    const pc = delta / (tMM * 1e-3) * 100;
    rows.push(["Skin depth at " + fmt(f, "Hz"), fmt(delta, "m")]);
    rows.push(["As a fraction of the copper", pc.toFixed(1) + " %" +
               (pc >= 100 ? " \u2014 the whole thickness conducts" : " \u2014 the centre of the copper carries little current, so extra thickness buys less than it appears")]);
  }

  if (isFinite(lenMM) && lenMM > 0 && isFinite(iVal) && iVal > 0 && isFinite(wMM)) {
    const r = traceR(wMM, tMM, lenMM, ta + dT);
    rows.push(["Resistance at " + (ta + dT).toFixed(0) + " \u00b0C", fmt(r, "\u03a9")]);
    rows.push(["Voltage drop / power", fmt(iVal * r, "V") + " / " + fmt(iVal * iVal * r, "W")]);
  }
  rows.push(["Model", "IPC-2221: I = k\u00b7\u0394T^0.44\u00b7A^0.725, k = " + k + " for an " +
             (k === 0.048 ? "external" : "internal") + " layer. IPC-2152 allows somewhat more; this is the conservative classic."]);
  render("tw-out", rows);
}

function calcVia() {
  const d = valDim("via-d");
  const tp = valDimUm("via-tp", 0.025);
  const h = numOr("via-h", 1.6, 1e-6);
  const dT = gTempRise();
  const er = numOr("via-er", 4.3, 1);
  if (!isFinite(d) || !(d > 0)) { render("via-out", []); return; }
  if (![tp, h, dT, er].every(isFinite)) { render("via-out", []); return; }
  const aMM2 = Math.PI * tp * (d + tp);                            // barrel cross-section
  const aMil2 = aMM2 / (MIL * MIL);
  const iCap = ipcCurrent(aMil2, dT, 0.024);
  const r = RHO20 * (h / 1000) / (aMM2 * 1e-6);
  const lNH = 5.08 * (h / 25.4) * (Math.log(4 * h / d) + 1);
  const theta = (h / 1000) / (390 * aMM2 * 1e-6);
  const rows = [
    ["Barrel cross-section", aMM2.toPrecision(3) + " mm&sup2;"],
    ["Current at &Delta;T " + dT + " &deg;C", fmt(iCap, "A")],
    ["DC resistance", fmt(r, "Ω")],
    ["Inductance", lNH.toPrecision(3) + " nH"],
    ["Thermal resistance", theta.toFixed(1) + " K/W"]
  ];
  /* L and C are already in hand, so the lumped figures are arithmetic. They are
     labelled as lumped deliberately: a through via is electrically short well
     past 10 GHz, so √(L/C) is a number to compare against the trace impedance,
     not a characteristic impedance the structure really has. */
  const nVia = Math.max(1, Math.round(numOr("via-n", 1, 1) || 1));
  const iVia = val("via-i");
  const arLimit = numOr("via-arlimit", 10, 0.1);
  const stub = valDim("via-stub");
  const ar = h / d;
  rows.push(["Aspect ratio", ar.toFixed(2) + " : 1" +
             (isFinite(arLimit) && ar > arLimit ? " — above the " + arLimit + ":1 limit, ask your fabricator" : ""),
             isFinite(arLimit) && ar > arLimit ? "warn" : ""]);
  if (nVia > 1) {
    rows.push([nVia + " vias in parallel",
               fmt(r / nVia, "Ω") + ", " + (theta / nVia).toFixed(1) + " K/W, " + fmt(iCap * nVia, "A")]);
    rows.push(["", "Resistance and thermal resistance divide by n, but inductance does not — mutual coupling between nearby vias means loop inductance falls far more slowly.", ""]);
  }
  if (isFinite(iVia) && iVia > 0) {
    const rEff = r / nVia;
    rows.push(["At " + fmt(iVia, "A"), fmt(iVia * rEff, "V") + " drop, " + fmt(iVia * iVia * rEff, "W") + " dissipated"]);
  }
  if (isFinite(stub) && stub > 0) {
    rows.push(["Stub quarter-wave null", fmt(299792458 / (4 * (stub / 1000) * Math.sqrt(er)), "Hz") +
               " — keep the signal's usable bandwidth well below this"]);
  }
  const pad = valDim("via-pad"), anti = valDim("via-anti");
  if (isFinite(pad) && isFinite(anti)) {
    if (anti > pad && pad > 0) {
      const cPF = 1.41 * er * (h / 25.4) * (pad / 25.4) / ((anti - pad) / 25.4);
      rows.push(["Capacitance", cPF.toPrecision(3) + " pF"]);
      const cF = cPF * 1e-12, lH = lNH * 1e-9;
      rows.push(["Lumped √(L/C)", Math.sqrt(lH / cF).toFixed(1) + " Ω — compare with your trace impedance; below it the via looks capacitive, above it inductive"]);
      rows.push(["Lumped-model limit", fmt(1 / (2 * Math.PI * Math.sqrt(lH * cF)), "Hz") +
                 " — treat the via as a discontinuity above roughly a third of this"]);
    } else {
      rows.push(["", "Antipad must be larger than pad for the capacitance estimate.", "warn"]);
    }
  }
  render("via-out", rows);
}

/* Onderdonk: 33*(I/A_cmil)^2 * t = log10(1 + (Tm-Ta)/(234+Ta)), Tm = 1083 C */
function calcFuse() {
  const w = valDim("fu-w"), t = val("fu-t");
  if (!isFinite(w) || !isFinite(t)) { render("fu-out", []); return; }
  if (!(w > 0) || !(t > 0)) { render("fu-out", [["", "Width and duration must be positive.", "err"]]); return; }
  const ta = gAmbient();
  const tMM = gCopperMM();
  const aMil2 = (w / MIL) * (tMM / MIL);
  const aCmil = aMil2 * 4 / Math.PI;
  const kOn = numOr("fu-k", 1, 0.01);
  if (!isFinite(kOn)) { render("fu-out", []); return; }
  const iFuse = kOn * aCmil * Math.sqrt(Math.log10(1 + (1083 - ta) / (234 + ta)) / (33 * t));
  render("fu-out", [
    ["Cross-section", aMil2.toFixed(1) + " mil&sup2; (" + (aMil2 * MIL * MIL).toPrecision(3) + " mm&sup2;)"],
    ["Fusing current for " + fmt(t, "s"), fmt(iFuse, "A")],
    ["", "Design fault currents well below this — the trace is at its melting point.", "warn"],
    ["", t > 5 ? "Onderdonk is adiabatic and is not meant for faults beyond about 5 seconds; over longer events the trace sheds heat and survives more current than this figure suggests." : "",
     t > 5 ? "warn" : ""]
  ]);
}

/* IPC-2221 Table 6-1, spacing in mm per voltage band; last entry is mm/V above 500 V. */
const SPACING = {
  B1: { name: "B1 — internal layers", v: [0.05, 0.05, 0.1, 0.1, 0.2, 0.2, 0.2, 0.2, 0.25], perV: 0.0025 },
  B2: { name: "B2 — external, uncoated, &le;3050 m", v: [0.1, 0.1, 0.6, 0.6, 0.6, 1.25, 1.25, 1.25, 2.5], perV: 0.005 },
  B3: { name: "B3 — external, uncoated, &gt;3050 m", v: [0.1, 0.1, 0.6, 1.5, 3.2, 3.2, 6.4, 12.5, 12.5], perV: 0.025 },
  B4: { name: "B4 — external, polymer coated", v: [0.05, 0.05, 0.13, 0.13, 0.4, 0.4, 0.4, 0.4, 0.8], perV: 0.00305 },
  A5: { name: "A5 — external, conformal coated", v: [0.13, 0.13, 0.13, 0.13, 0.4, 0.4, 0.4, 0.4, 0.8], perV: 0.00305 },
  A6: { name: "A6 — component leads, uncoated", v: [0.13, 0.25, 0.4, 0.5, 0.5, 0.8, 0.8, 0.8, 1.5], perV: 0.00305 },
  A7: { name: "A7 — component leads, conformal coated", v: [0.13, 0.13, 0.13, 0.13, 0.4, 0.4, 0.4, 0.4, 0.8], perV: 0.00305 }
};
const SPACING_BANDS = [15, 30, 50, 100, 150, 170, 250, 300, 500];

function calcSpacing() {
  const v = val("spc-v");
  if (!isFinite(v) || !(v > 0)) { render("spc-out", []); return; }
  const rows = [];
  let band = SPACING_BANDS.findIndex(function (b) { return v <= b; });
  for (const key in SPACING) {
    const e = SPACING[key];
    const mm = band === -1 ? e.v[8] + (v - 500) * e.perV : e.v[band];
    rows.push([e.name, mm.toFixed(2) + " mm (" + (mm / MIL).toFixed(0) + " mil)"]);
  }
  render("spc-out", rows);
}

/* ---------- impedance ---------- */

/* Hilberg's approximation to K(k)/K(k'), accurate to about 2e-6 and
   continuous across the branch at k = 1/sqrt(2). Used by the coplanar model,
   which needs elliptic integrals and would otherwise need a library. */
function kkRatio(k) {
  const kp = Math.sqrt(Math.max(0, 1 - k * k));
  if (k <= Math.SQRT1_2) return Math.PI / Math.log(2 * (1 + Math.sqrt(kp)) / (1 - Math.sqrt(kp)));
  return Math.log(2 * (1 + Math.sqrt(k)) / (1 - Math.sqrt(k))) / Math.PI;
}

/* Hammerstad-Jensen with the upper half-space filled by ercov instead of air.
   ercov = 1 gives plain H-J and ercov = er gives a homogeneous medium, both
   exactly, so it is well behaved at the limits that matter. */
function hjEeffCovered(u, er, ercov) {
  const a = 1 + Math.log((Math.pow(u, 4) + Math.pow(u / 52, 2)) / (Math.pow(u, 4) + 0.432)) / 49
              + Math.log1p(Math.pow(u / 18.1, 3)) / 18.7;
  const b = 0.564 * Math.pow((er - 0.9) / (er + 3), 0.053);
  return (er + ercov) / 2 + (er - ercov) / 2 * Math.pow(1 + 10 / u, -a * b);
}

function calcZ() {
  const struct = document.getElementById("z-struct").value;
  const w = valDim("z-w"), h = valDim("z-h"), c = valDim("z-c"), gap = valDim("z-s");
  const er = numOr("z-er", 4.3, 1);
  const ercov = numOr("z-ermask", 3.8, 1);
  const f = val("z-f");
  const t = gCopperMM();
  const lbl = document.getElementById("z-hlabel");
  if (lbl) {
    lbl.innerHTML = struct === "sl" ? "Plane-to-plane b (mm)"
                  : struct === "asym" ? "Distance to near plane (mm)"
                  : "Dielectric height h (mm)";
  }
  if (!isFinite(er) || !isFinite(w) || !isFinite(h) || !(w > 0) || !(h > 0)) { render("z-out", []); return; }

  const rows = [];
  let z0 = NaN, eeff = NaN, validity = "";

  if (struct === "ms" || struct === "mscov") {
    const u = w / h + hjDeltaU(t / h);
    validity = "Hammerstad\u2013Jensen, valid for 0.01 \u2264 w/h \u2264 100. Here w/h = " + u.toPrecision(3) + ".";
    if (u < HJ_U_MIN || u > HJ_U_MAX) {
      render("z-out", [["", "w/h of " + u.toPrecision(3) + " is outside Hammerstad\u2013Jensen's range of " +
                        HJ_U_MIN + " to " + HJ_U_MAX + "; the formula breaks down there rather than merely losing accuracy.", "err"]]);
      return;
    }
    const z01 = hjZ01(u);
    const eeBare = hjEeff(u, er);
    if (struct === "ms") {
      eeff = eeBare;
      z0 = z01 / Math.sqrt(eeff);
    } else {
      if (!isFinite(ercov)) { render("z-out", []); return; }
      const eeFull = hjEeffCovered(u, er, ercov);
      const zFull = z01 / Math.sqrt(eeFull);
      const zBare = z01 / Math.sqrt(eeBare);
      eeff = eeFull;
      z0 = zFull;
      rows.push(["Bare, for comparison", zBare.toFixed(1) + " \u03a9 at \u03b5<sub>eff</sub> " + eeBare.toFixed(3)]);
      rows.push(["", "This is the <em>fully covered</em> limit, with the cover filling the space above the trace. " +
                 "A real solder mask is thin, so the true impedance lies between " + zFull.toFixed(1) + " and " +
                 zBare.toFixed(1) + " \u03a9, nearer the bare figure for a 25\u201350 \u00b5m mask. No interpolation is " +
                 "offered because any curve between these two would be invented rather than sourced.", "warn"]);
      validity += " Cover \u03b5<sub>r</sub> " + ercov + ".";
    }
    if (isFinite(f) && f > 0) {
      const ee0 = eeff;
      eeff = kjEeff(u, er, ee0, h, f);
      z0 = z01 / Math.sqrt(eeff);
      rows.push(["Dispersion at " + fmt(f, "Hz"), "\u03b5<sub>eff</sub> " + ee0.toFixed(4) + " \u2192 " + eeff.toFixed(4) +
                 " (Kirschning\u2013Jansen)"]);
    }
  } else if (struct === "sl") {
    validity = "IPC-2141 symmetric stripline, valid for w/b < 0.35 and t/b < 0.25. Here w/b = " +
               (w / h).toPrecision(3) + ", t/b = " + (t / h).toPrecision(3) + ".";
    const arg = 1.9 * h / (0.8 * w + t);
    if (arg <= 1) { render("z-out", [["", "The trace is too wide for this plane spacing \u2014 the formula gives no real impedance.", "err"]]); return; }
    eeff = er;
    z0 = 60 / Math.sqrt(er) * Math.log(arg);
    if (w / h > 0.35 || t / h > 0.25) rows.push(["", "Outside the stated validity range \u2014 treat with suspicion.", "warn"]);
  } else if (struct === "asym") {
    if (!isFinite(c) || !(c > 0)) { render("z-out", [["", "Enter the distance to the far plane.", ""]]); return; }
    const b = h + c + t;
    /* The IPC asymmetric expression uses an 80 coefficient where the symmetric
       one uses 60, so the two disagree by about 17 % at the centred limit and
       the raw formula can report a HIGHER impedance for an offset trace than a
       centred one, which is backwards. Normalising against the same formula
       evaluated at the centred position removes the mismatch and makes h = c
       reproduce the symmetric result exactly. */
    const raw = function (hh, cc) {
      const a = 1.9 * (2 * hh + t) / (0.8 * w + t);
      if (a <= 1) return NaN;
      return 80 / Math.sqrt(er) * Math.log(a) * (1 - hh / (4 * (hh + cc + t)));
    };
    const half = (b - t) / 2;
    const rawHere = raw(h, c), rawMid = raw(half, half);
    const argSym = 1.9 * b / (0.8 * w + t);
    if (!isFinite(rawHere) || !isFinite(rawMid) || argSym <= 1) {
      render("z-out", [["", "The trace is too wide, or too close to a plane, for this formula.", "err"]]);
      return;
    }
    const zSym = 60 / Math.sqrt(er) * Math.log(argSym);
    eeff = er;
    z0 = zSym * rawHere / rawMid;
    validity = "IPC-2141 offset stripline, normalised so a centred trace reproduces the symmetric result. " +
               "Plane-to-plane " + b.toPrecision(4) + " mm; the trace sits " + (h / b * 100).toFixed(0) + " % of the way across.";
    rows.push(["Centred, for comparison", zSym.toFixed(1) + " \u03a9"]);
  } else if (struct === "cpwg") {
    if (!isFinite(gap) || !(gap > 0)) { render("z-out", [["", "Enter the gap between the track and the surrounding ground.", ""]]); return; }
    const k = w / (w + 2 * gap);
    const k3 = Math.tanh(Math.PI * w / (4 * h)) / Math.tanh(Math.PI * (w + 2 * gap) / (4 * h));
    const r1 = kkRatio(k), r3 = kkRatio(k3);
    eeff = (1 + er * (r3 / r1)) / (1 + r3 / r1);
    z0 = 60 * Math.PI / (Math.sqrt(eeff) * (r1 + r3));
    validity = "Grounded coplanar waveguide (Ghione &amp; Naldi), zero-thickness conductor assumed \u2014 " +
               (t / gap > 0.1 ? "your copper is " + (t / gap * 100).toFixed(0) + " % of the gap, which this model ignores."
                              : "copper thickness is small against the gap here, so that assumption holds.");
  }

  if (!isFinite(z0) || z0 <= 0) { render("z-out", [["", "That geometry gives no real impedance.", "err"]]); return; }

  const tpd = Math.sqrt(eeff) / 299792458;          // seconds per metre
  rows.unshift(["Z<sub>0</sub>", z0.toFixed(1) + " \u03a9"]);
  rows.push(["&epsilon;<sub>eff</sub>", eeff.toFixed(4)]);
  rows.push(["Propagation delay", (tpd * 1e12).toFixed(1) + " ps/m (" + (tpd * 1e12 * 0.0254).toFixed(2) + " ps/in)"]);
  /* L and C follow from Zo and Tpd under one model, so sqrt(L/C) returns Zo
     exactly - which the previous mix of IPC impedance and Hammerstad eps_eff
     could not do. */
  rows.push(["Inductance", (z0 * tpd * 1e9).toFixed(1) + " nH/m (" + (z0 * tpd * 1e9 * 0.0254).toFixed(3) + " nH/in)"]);
  rows.push(["Capacitance", (tpd / z0 * 1e12).toFixed(1) + " pF/m (" + (tpd / z0 * 1e12 * 0.0254).toFixed(3) + " pF/in)"]);
  if (validity) rows.push(["Model", validity]);
  render("z-out", rows);
}

function calcWave() {
  const period = val("wl-period");
  let f = val("wl-f");
  const tr = val("wl-tr");
  const eeff = numOr("wl-eeff", 3.3, 1);
  if (!isFinite(eeff)) { render("wl-out", []); return; }
  const rows = [];
  if (!isFinite(f) && isFinite(period) && period > 0) {
    f = 1 / period;
    rows.push(["Frequency from period", fmt(f, "Hz")]);
  }
  const vp = 299792458 / Math.sqrt(eeff);
  if (isFinite(f) && f > 0) {
    const lam = vp / f;
    const div = parseFloat(document.getElementById("wl-div").value) || 1;
    rows.push(["Wavelength λ", fmt(lam, "m")]);
    rows.push([div === 1 ? "Full λ" : "λ/" + div, fmt(lam / div, "m")]);
    rows.push(["Propagation speed", fmt(vp, "m/s") + " (" + (0.1 / vp * 1e12).toFixed(1) + " ps per 100 mm)"]);
  }
  if (isFinite(tr) && tr > 0) {
    rows.push(["Knee frequency 0.35/t<sub>r</sub>", fmt(0.35 / tr, "Hz")]);
    rows.push(["Critical length", fmt(tr * vp / 2, "m") + " — shorter traces need no termination"]);
  }
  render("wl-out", rows);
}

/* ---------- crystal ---------- */

function calcXtal() {
  clearComputed(["xc-cl","xc-c1","xc-c2"]);
  const cl = val("xc-cl"), c1 = val("xc-c1"), c2 = val("xc-c2"), csRaw = val("xc-cs");
  const cs = isFinite(csRaw) && csRaw >= 0 ? csRaw : 3e-12;
  const rows = [];
  if (isFinite(c1) && isFinite(c2) && c1 > 0 && c2 > 0) {
    const clAct = c1 * c2 / (c1 + c2) + cs;
    if (!isFinite(cl)) setComputed("xc-cl", clAct);
    else {
      const err = (clAct - cl) / cl * 100;
      rows.push(["Load the crystal sees", fmt(clAct, "F")]);
      rows.push(["vs. spec " + fmt(cl, "F"), err.toFixed(1) + " %" + (Math.abs(err) > 10 ? " — retune C1/C2" : ""), Math.abs(err) > 10 ? "warn" : ""]);
    }
  } else if (isFinite(cl) && cl > 0) {
    /* The series pair must present CL - Cs. With neither leg chosen, the
       symmetric answer C1 = C2 = 2(CL - Cs) is the usual starting point; with
       one leg already chosen the other is NOT the same value, and writing it
       as though it were is how this card used to report 18 pF where 15.23 pF
       was needed. */
    const need = cl - cs;
    if (need <= 0) { render("xc-out", [["", "Stray capacitance already exceeds the C<sub>L</sub> spec.", "err"]]); return; }
    const known = isFinite(c1) && c1 > 0 ? c1 : (isFinite(c2) && c2 > 0 ? c2 : NaN);
    let c;
    if (isFinite(known)) {
      if (known <= need) {
        render("xc-out", [["", "That leg is too small: on its own it already presents " + fmt(known, "F") + " or less in series, so no partner can reach the C<sub>L</sub> spec. Use a larger value.", "err"]]);
        return;
      }
      c = need * known / (known - need);
      setComputed(isFinite(c1) && c1 > 0 ? "xc-c2" : "xc-c1", c);
      rows.push(["Partner for " + fmt(known, "F"), fmt(c, "F")]);
    } else {
      c = 2 * need;
      setComputed("xc-c1", c);
      setComputed("xc-c2", c);
    }
    rows.push(["Nearest E12 value", fmt(snap(seriesValues("E12", -12, -10), c), "F")]);
  }
  if (isFinite(cs) && rows.length === 0 && !isFinite(cl) && !isFinite(c1)) { render("xc-out", []); return; }
  render("xc-out", rows);
}

function calcPPM() {
  clearComputed(["pp-ppm","pp-df"]);
  const f = val("pp-f"), ppm = val("pp-ppm"), df = val("pp-df");
  let p = ppm;
  if (isFinite(f) && f > 0 && isFinite(ppm) && !isFinite(df)) setComputed("pp-df", f * ppm * 1e-6);
  else if (isFinite(f) && f > 0 && isFinite(df) && !isFinite(ppm)) { p = df / f * 1e6; setComputed("pp-ppm", p); }
  else if (isFinite(f) && f > 0 && isFinite(df) && isFinite(ppm)) p = ppm;
  if (!isFinite(p)) { render("pp-out", []); return; }
  const ppmRows = [];
  if (isFinite(f) && f > 0) {
    /* fmt() carries four significant figures, which cannot resolve a window of
       a few ppm - 16 MHz ± 20 ppm would print as "16 MHz … 16 MHz". Show the
       endpoints in whole hertz instead, where the difference is visible. */
    const lo = f * (1 - p * 1e-6), hi = f * (1 + p * 1e-6);
    const hz = function (x) { return Math.round(x).toLocaleString("en-US"); };
    ppmRows.push(["Frequency window", hz(lo) + " … " + hz(hi) + " Hz"]);
    ppmRows.push(["Deviation", "±" + fmt(f * p * 1e-6, "Hz")]);
  }
  render("pp-out", ppmRows.concat([
    ["Clock drift", "±" + (p * 0.0864).toPrecision(3) + " s/day, ±" + (p * 0.0864 * 365.25 / 60).toPrecision(3) + " min/year"],
    ["Worst-case pair separation", "±" + (2 * p).toPrecision(3) + " ppm between two such parts"]
  ]));
}

/* ---------- utilities ---------- */

const AWG_CHASSIS = { "-3": 380, "-2": 328, "-1": 283, 0: 245, 1: 211, 2: 181, 3: 158, 4: 135, 5: 118, 6: 101, 7: 89, 8: 73, 9: 64, 10: 55, 11: 47, 12: 41, 13: 35, 14: 32, 15: 28, 16: 22, 17: 19, 18: 16, 19: 14, 20: 11, 21: 9, 22: 7, 23: 4.7, 24: 3.5, 25: 2.7, 26: 2.2, 27: 1.7, 28: 1.4, 29: 1.2, 30: 0.86, 31: 0.7, 32: 0.53, 33: 0.43, 34: 0.33, 35: 0.27, 36: 0.21, 37: 0.17, 38: 0.13, 39: 0.11, 40: 0.09 };
const AWG_POWER = { "-3": 302, "-2": 239, "-1": 190, 0: 150, 1: 119, 2: 94, 3: 75, 4: 60, 5: 47, 6: 37, 7: 30, 8: 24, 9: 19, 10: 15, 11: 12, 12: 9.3, 13: 7.4, 14: 5.9, 15: 4.7, 16: 3.7, 17: 2.9, 18: 2.3, 19: 1.8, 20: 1.5, 21: 1.2, 22: 0.92, 23: 0.729, 24: 0.577, 25: 0.457, 26: 0.361, 27: 0.288, 28: 0.226, 29: 0.182, 30: 0.142, 31: 0.113, 32: 0.091, 33: 0.072, 34: 0.056, 35: 0.044, 36: 0.035, 37: 0.0289, 38: 0.0228, 39: 0.0175, 40: 0.0137 };

function calcAWG() {
  const raw = document.getElementById("awg-n").value.trim();
  if (!raw) { render("awg-out", []); return; }
  let n;
  let m = raw.match(/^(\d)\/0$/);                       // 2/0, 3/0, 4/0
  if (m) n = 1 - parseInt(m[1], 10);
  else if (/^0+$/.test(raw)) n = 1 - raw.length;        // 0, 00, 000, 0000
  else n = parseInt(raw, 10);
  const el = document.getElementById("awg-n");
  const ok = Number.isInteger(n) && n >= -3 && n <= 40;
  el.classList.toggle("bad", !ok);
  if (!ok) { render("awg-out", [["", "AWG 40 down to 0000 (4/0).", "err"]]); return; }
  const dMM = 0.127 * Math.pow(92, (36 - n) / 39);
  const aMM2 = Math.PI / 4 * dMM * dMM;
  const rPerM = RHO20 / (aMM2 * 1e-6);
  const rows = [
    ["Diameter", dMM.toFixed(3) + " mm (" + (dMM / MIL).toFixed(1) + " mil)"],
    ["Area", aMM2.toPrecision(3) + " mm&sup2;"],
    ["Resistance at 20 °C", fmt(rPerM, "Ω") + "/m (" + fmt(rPerM * 1000, "Ω") + "/km)"],
    ["Ampacity — chassis wiring", fmt(AWG_CHASSIS[n], "A")],
    ["Ampacity — power transmission", fmt(AWG_POWER[n], "A")]
  ];
  const len = val("awg-len"), cur = val("awg-i"), vsup = val("awg-vsupply");
  const temp = numOr("awg-temp", 20, -273.15);
  const trips = parseFloat(document.getElementById("awg-return").value) || 2;
  if (isFinite(len) && len > 0 && isFinite(temp)) {
    const rHot = rPerM * (1 + ALPHA * (temp - 20));
    const rLoop = rHot * len * trips;
    if (Math.abs(temp - 20) > 1e-9) {
      rows.push(["Resistance at " + temp + " °C",
                 fmt(rHot, "Ω") + "/m (" + ((rHot / rPerM - 1) * 100).toFixed(1) + " % higher)"]);
    }
    rows.push([(trips === 2 ? "Loop" : "One-way") + " resistance over " + fmt(len, "m"), fmt(rLoop, "Ω")]);
    if (isFinite(cur) && cur > 0) {
      const drop = cur * rLoop;
      rows.push(["Voltage drop at " + fmt(cur, "A"), fmt(drop, "V")]);
      rows.push(["Power lost in the wire", fmt(cur * cur * rLoop, "W")]);
      if (isFinite(vsup) && vsup > 0) {
        const pc = drop / vsup * 100;
        rows.push(["As a fraction of " + fmt(vsup, "V"),
                   pc.toFixed(2) + " %" + (pc > 5 ? " — over 5 %, consider heavier wire" : ""),
                   pc > 5 ? "warn" : ""]);
      }
      if (cur > AWG_CHASSIS[n]) {
        rows.push(["", "That current exceeds even the chassis-wiring rating for this gauge.", "err"]);
      }
    }
  }
  render("awg-out", rows);
}

/* Conversion pairs: editing either field fills the other(s). */
function wirePair(specs) {
  // specs: [[id, toCanonical, fromCanonical], ...] sharing one canonical value
  specs.forEach(function (s) {
    document.getElementById(s[0]).addEventListener("input", function () {
      const v = parseVal(this.value);
      this.classList.toggle("bad", this.value.trim() !== "" && !isFinite(v));
      if (!isFinite(v)) return;
      const canon = s[1](v);
      specs.forEach(function (o) {
        if (o[0] !== s[0]) document.getElementById(o[0]).value = +o[2](canon).toPrecision(6);
      });
    });
  });
}

/* ---------- power and thermal ---------- */

/* Series thermal resistances add, so a package on a heatsink is a divider
   carrying power instead of current. Tj is written back into its own box; the
   figures with no box of their own - headroom, maximum power, the heatsink you
   would need - go to the results list. */
function calcThermal() {
  clearComputed(["th-tj"]);
  const P = val("th-p");
  const ta = gAmbient();
  const jc = val("th-jc"), cs = val("th-cs"), sa = val("th-sa"), ja = val("th-ja");
  const tjmax = val("th-tjmax");
  const target = isFinite(val("th-tjtarget")) ? val("th-tjtarget") : tjmax;
  if (!isFinite(P) || !isFinite(ta)) { render("th-out", []); return; }
  if (P < 0) { render("th-out", [["", "Power dissipated cannot be negative.", "err"]]); return; }
  const parts = [jc, cs, sa].filter(isFinite);
  const chain = parts.length ? parts.reduce(function (a, b) { return a + b; }, 0) : NaN;
  if (parts.some(function (x) { return x < 0; })) { render("th-out", [["", "Thermal resistances cannot be negative.", "err"]]); return; }
  let theta = isFinite(chain) ? chain : ja;
  const rows = [];
  if (isFinite(chain) && isFinite(ja)) {
    rows.push(["", "Both a chain and a single \u03b8(junction\u2013ambient) given \u2014 using the chain. They differ by " +
               (Math.abs(ja - chain) / chain * 100).toFixed(0) + " %.", "warn"]);
  }
  if (!isFinite(theta) || theta <= 0) { render("th-out", [["", "Enter at least one thermal resistance.", ""]]); return; }
  const rise = P * theta;
  const tj = ta + rise;
  setComputed("th-tj", tj);
  rows.push(["Total \u03b8", theta.toPrecision(4) + " \u00b0C/W"]);
  rows.push(["Temperature rise", rise.toPrecision(4) + " K"]);
  if (isFinite(jc)) rows.push(["Case temperature", (tj - P * jc).toPrecision(4) + " \u00b0C"]);
  if (isFinite(sa)) rows.push(["Sink temperature", (ta + P * sa).toPrecision(4) + " \u00b0C"]);
  if (isFinite(tjmax)) {
    const head = tjmax - tj;
    rows.push(["Headroom to T<sub>j</sub> max", head.toPrecision(4) + " K" + (head < 0 ? " \u2014 over temperature" : ""), head < 0 ? "err" : (head < 20 ? "warn" : "")]);
    rows.push(["Maximum power for T<sub>j</sub> max", fmt((tjmax - ta) / theta, "W")]);
  }
  if (isFinite(target) && P > 0) {
    const fixed = (isFinite(jc) ? jc : 0) + (isFinite(cs) ? cs : 0);
    const need = (target - ta) / P - fixed;
    rows.push(["\u03b8 sink\u2013ambient needed for " + target.toPrecision(4) + " \u00b0C",
               need > 0 ? need.toPrecision(4) + " \u00b0C/W"
                        : "impossible \u2014 the package alone already exceeds the target, so the part or the ambient must change",
               need > 0 ? "" : "err"]);
  }
  render("th-out", rows);
}

/* A real capacitor is C, ESL and ESR in series: capacitive below self
   resonance, resistive at it, inductive above. */
/* Superseded by calcReact, which covers capacitors and inductors together. */
function calcCapSRF() {
  const c = val("cs-c"), esl = val("cs-esl"), esr = val("cs-esr"), f = val("cs-f");
  const n = Math.max(1, Math.round(numOr("cs-n", 1, 1) || 1));
  if (!isFinite(c) || c <= 0) { render("cs-out", []); return; }
  const C = c * n;
  const L = isFinite(esl) && esl > 0 ? esl / n : NaN;
  const R = isFinite(esr) && esr >= 0 ? esr / n : NaN;
  const rows = [];
  if (n > 1) rows.push(["Bank of " + n, fmt(C, "F") + " total" + (isFinite(L) ? ", " + fmt(L, "H") + " ESL" : "") + (isFinite(R) ? ", " + fmt(R, "\u03a9") + " ESR" : "")]);
  if (isFinite(L)) {
    const srf = 1 / (2 * Math.PI * Math.sqrt(L * C));
    rows.push(["Self-resonant frequency", fmt(srf, "Hz")]);
    rows.push(["|Z| at resonance", isFinite(R) ? fmt(R, "\u03a9") + " (ESR alone)" : "equal to ESR"]);
  }
  if (isFinite(f) && f > 0) {
    const xc = 1 / (2 * Math.PI * f * C);
    const xl = isFinite(L) ? 2 * Math.PI * f * L : 0;
    const react = xl - xc;
    const z = Math.sqrt((isFinite(R) ? R * R : 0) + react * react);
    rows.push(["X<sub>C</sub> at " + fmt(f, "Hz"), fmt(xc, "\u03a9")]);
    if (isFinite(L)) rows.push(["X<sub>L</sub> at " + fmt(f, "Hz"), fmt(xl, "\u03a9")]);
    rows.push(["|Z| at " + fmt(f, "Hz"), fmt(z, "\u03a9") +
               (isFinite(L) ? (react > 0 ? " \u2014 inductive, past self-resonance" : " \u2014 capacitive") : "")]);
  }
  if (!rows.length) rows.push(["", "Add an ESL for self-resonance, or a frequency for impedance.", ""]);
  render("cs-out", rows);
}

/* Disabled: the card is hidden. Kept so it can be restored in one edit. */
function calcPlaneC() {
  const EPS0 = 8.8541878128e-12;
  const a = val("pc-a"), d = val("pc-d"), f = val("pc-f");
  const er = numOr("pc-er", 4.3, 1);
  if (!isFinite(a) || !isFinite(d) || !isFinite(er)) { render("pc-out", []); return; }
  if (!(a > 0) || !(d > 0)) { render("pc-out", [["", "Area and separation must be positive.", "err"]]); return; }
  const C = EPS0 * er * (a * 1e-6) / (d * 1e-3);
  const rows = [["Plane capacitance", fmt(C, "F")],
                ["Capacitance per area", fmt(C / (a * 1e-6) * 1e-4, "F") + " per cm\u00b2"]];
  if (isFinite(f) && f > 0) rows.push(["X<sub>C</sub> at " + fmt(f, "Hz"), fmt(1 / (2 * Math.PI * f * C), "\u03a9")]);
  render("pc-out", rows);
}

function calcPDN() {
  const v = val("pdn-v"), i = val("pdn-i"), fmax = val("pdn-fmax");
  const ripple = val("pdn-ripple"), tr = val("pdn-tr");
  if (![v, i, ripple, tr].every(isFinite)) { render("pdn-out", []); return; }
  if (!(v > 0) || !(i > 0) || !(ripple > 0) || !(tr > 0)) { render("pdn-out", [["", "All four values must be positive.", "err"]]); return; }
  if (ripple > 100 || tr > 100) { render("pdn-out", [["", "Percentages cannot exceed 100.", "err"]]); return; }
  const dv = v * ripple / 100, di = i * tr / 100;
  const z = dv / di;
  const rows = [["Allowed ripple", fmt(dv, "V")],
                ["Transient current step", fmt(di, "A")],
                ["Target impedance", fmt(z, "\u03a9")]];
  if (isFinite(fmax) && fmax > 0) {
    rows.push(["Must hold from DC to", fmt(fmax, "Hz")]);
    rows.push(["Total loop inductance budget", fmt(z / (2 * Math.PI * fmax), "H") +
               " \u2014 above this the network exceeds target at the top frequency"]);
  }
  render("pdn-out", rows);
}

/* ---------- attenuator pads ---------- */

function calcPad() {
  const a = val("pad-a");
  const z0 = numOr("pad-z0", 50, 1e-9);
  const z2 = val("pad-z2");
  if (!isFinite(a) || !isFinite(z0)) { render("pad-out", []); return; }
  if (a <= 0) { render("pad-out", [["", "Attenuation must be greater than 0 dB.", "err"]]); return; }
  const K = Math.pow(10, a / 20);
  const piSh = z0 * (K + 1) / (K - 1);
  const piSe = z0 * (K * K - 1) / (2 * K);
  const tSe = z0 * (K - 1) / (K + 1);
  const tSh = 2 * K * z0 / (K * K - 1);
  const series = gSeries();
  const vals = seriesValues(series, -1, 7);
  const near = function (x) { return snap(vals, x); };
  const rows = [
    ["PI pad", "shunt " + fmt(piSh, "\u03a9") + " \u00b7 series " + fmt(piSe, "\u03a9") + " \u00b7 shunt " + fmt(piSh, "\u03a9")],
    ["T pad", "series " + fmt(tSe, "\u03a9") + " \u00b7 shunt " + fmt(tSh, "\u03a9") + " \u00b7 series " + fmt(tSe, "\u03a9")]
  ];
  // what the nearest stock values actually deliver
  const nPiSh = near(piSh), nPiSe = near(piSe);
  const aPi = padLossPi(nPiSh, nPiSe, z0);
  const aT = padLossT(near(tSe), near(tSh), z0);
  rows.push(["Nearest " + series + " PI", fmt(nPiSh, "\u03a9") + " / " + fmt(nPiSe, "\u03a9") +
             " \u2014 gives " + aPi.toFixed(2) + " dB"]);
  rows.push(["Nearest " + series + " T", fmt(near(tSe), "\u03a9") + " / " + fmt(near(tSh), "\u03a9") +
             " \u2014 gives " + aT.toFixed(2) + " dB"]);
  if (isFinite(z2) && z2 > 0 && Math.abs(z2 - z0) > 1e-12) {
    const hi = Math.max(z0, z2), lo = Math.min(z0, z2);
    const ratio = hi / lo;
    const aMin = 20 * Math.log10(Math.sqrt(ratio) + Math.sqrt(ratio - 1));
    const rs = hi * Math.sqrt(1 - lo / hi);
    const rp = lo / Math.sqrt(1 - lo / hi);
    rows.push(["L pad, " + fmt(hi, "\u03a9") + " to " + fmt(lo, "\u03a9"),
               "series " + fmt(rs, "\u03a9") + " on the " + fmt(hi, "\u03a9") + " side, shunt " + fmt(rp, "\u03a9") + " across the " + fmt(lo, "\u03a9") + " side"]);
    rows.push(["L pad minimum loss", aMin.toFixed(2) + " dB" +
               (a < aMin ? " \u2014 more than the " + a + " dB asked for; an L pad cannot do better between these impedances" : ""),
               a < aMin ? "warn" : ""]);
  }
  render("pad-out", rows);
}

/* What a pad built from real parts actually attenuates. For a matched pad this
   is just the voltage division through it, and with exact values it returns the
   design figure to the last decimal - which is the test. */
function padLossPi(rp, rs, z0) {
  const par = rp * z0 / (rp + z0);
  return -20 * Math.log10(par / (rs + par));
}

function padLossT(rs, rp, z0) {
  const zA = rp * (rs + z0) / (rp + rs + z0);
  return -20 * Math.log10((zA / (rs + zA)) * (z0 / (rs + z0)));
}

/* ---------- Hammerstad-Jensen microstrip, shared by several cards ---------- */

const HJ_U_MIN = 0.01, HJ_U_MAX = 100;

/* Hammerstad thickness correction, expressed as an addition to w/h. */
function hjDeltaU(tOverH) {
  if (!(tOverH > 0)) return 0;
  return (tOverH / Math.PI) * (1 + Math.log(2 / tOverH));
}

function hjEeff(u, er) {
  const a = 1 + Math.log((Math.pow(u, 4) + Math.pow(u / 52, 2)) / (Math.pow(u, 4) + 0.432)) / 49
              + Math.log1p(Math.pow(u / 18.1, 3)) / 18.7;
  const b = 0.564 * Math.pow((er - 0.9) / (er + 3), 0.053);
  return (er + 1) / 2 + (er - 1) / 2 * Math.pow(1 + 10 / u, -a * b);
}

function hjZ01(u) {
  const f = 6 + (2 * Math.PI - 6) * Math.exp(-Math.pow(30.666 / u, 0.7528));
  return 376.730313 / (2 * Math.PI) * Math.log(f / u + Math.sqrt(1 + Math.pow(2 / u, 2)));
}

/* Kirschning-Jansen dispersion. h in mm, f in Hz. */
function kjEeff(u, er, ee0, hMM, fHz) {
  const fn = fHz / 1e9 * hMM;
  if (!(fn > 0)) return ee0;
  const p1 = 0.27488 + (0.6315 + 0.525 / Math.pow(1 + 0.0157 * fn, 20)) * u - 0.065683 * Math.exp(-8.7513 * u);
  const p2 = 0.33622 * (1 - Math.exp(-0.03442 * er));
  const p3 = 0.0363 * Math.exp(-4.6 * u) * (1 - Math.exp(-Math.pow(fn / 38.7, 4.97)));
  const p4 = 1 + 2.751 * (1 - Math.exp(-Math.pow(er / 15.916, 8)));
  const P = p1 * p2 * Math.pow((0.1844 + p3 * p4) * fn, 1.5763);
  return er - (er - ee0) / (1 + P);
}

function calcEreff() {
  const w = valDim("ee-w"), h = valDim("ee-h"), f = val("ee-f");
  const er = numOr("ee-er", 4.3, 1);
  const t = gCopperMM();
  if (!isFinite(w) || !isFinite(h) || !isFinite(er) || !(w > 0) || !(h > 0)) { render("ee-out", []); return; }
  const u = w / h + hjDeltaU(t / h);
  const rows = [];
  if (u < HJ_U_MIN || u > HJ_U_MAX) {
    render("ee-out", [["", "w/h of " + u.toPrecision(3) + " is outside Hammerstad\u2013Jensen's validity range of " +
                       HJ_U_MIN + " to " + HJ_U_MAX + "; the formula is not just inaccurate there, it breaks down.", "err"]]);
    return;
  }
  const ee0 = hjEeff(u, er);
  rows.push(["w/h, corrected for copper", u.toPrecision(4)]);
  rows.push(["&epsilon;<sub>eff</sub> (static)", ee0.toFixed(4)]);
  rows.push(["Bounded by", ((er + 1) / 2).toFixed(3) + " \u2026 " + er.toFixed(3)]);
  let ee = ee0;
  if (isFinite(f) && f > 0) {
    ee = kjEeff(u, er, ee0, h, f);
    rows.push(["&epsilon;<sub>eff</sub> at " + fmt(f, "Hz"), ee.toFixed(4) +
               " (" + ((ee / ee0 - 1) * 100).toFixed(2) + " % dispersion)"]);
  }
  rows.push(["Propagation delay", (Math.sqrt(ee) / 299792458 * 1e12).toFixed(1) + " ps/m (" +
             (Math.sqrt(ee) / 299792458 * 1e12 * 0.0254).toFixed(1) + " ps/in)"]);
  render("ee-out", rows);
}

/* ---------- differential pair ---------- */

function calcDiff() {
  const w = valDim("dp-w"), sp = valDim("dp-s"), h = valDim("dp-h");
  const er = numOr("dp-er", 4.3, 1);
  const t = gCopperMM();
  const ms = document.getElementById("dp-struct").value === "ms";
  if (![w, sp, h, er].every(isFinite) || !(w > 0) || !(sp > 0) || !(h > 0)) { render("dp-out", []); return; }
  const rows = [];
  const wh = w / h, sh = sp / h;
  if (wh <= 0.1 || wh >= 3 || sh <= 0.1 || sh >= 3) {
    rows.push(["", "Outside the fit's validity range (w/h = " + wh.toPrecision(3) + ", s/h = " + sh.toPrecision(3) +
               "; both must be between 0.1 and 3.0) \u2014 treat the number below as indicative only.", "warn"]);
  }
  let z0, ee;
  if (ms) {
    const u = wh + hjDeltaU(t / h);
    ee = hjEeff(u, er);
    z0 = hjZ01(u) / Math.sqrt(ee);
  } else {
    ee = er;
    z0 = 60 / Math.sqrt(er) * Math.log(1.9 * h / (0.8 * w + t));
  }
  const k = ms ? 0.48 : 0.347, m = ms ? 0.96 : 2.9;
  const zdiff = 2 * z0 * (1 - k * Math.exp(-m * sh));
  rows.push(["Single-ended Z<sub>0</sub>", z0.toFixed(1) + " \u03a9"]);
  rows.push(["Differential Z<sub>diff</sub>", zdiff.toFixed(1) + " \u03a9"]);
  /* Zdiff = 2*Zodd by definition, and for a symmetric pair the isolated-line
     impedance is the geometric mean of the two modes, so Zeven = Z0^2/Zodd. */
  const zodd = zdiff / 2, zeven = z0 * z0 / zodd;
  rows.push(["Odd / even mode", zodd.toFixed(1) + " \u03a9 / " + zeven.toFixed(1) + " \u03a9"]);
  rows.push(["Common-mode Z", (zeven / 2).toFixed(1) + " \u03a9"]);
  rows.push(["Coupling factor", (k * Math.exp(-m * sh) * 100).toFixed(1) + " %"]);
  const tsel = document.getElementById("dp-target").value;
  const target = parseFloat(tsel);
  if (isFinite(target)) {
    const err = (zdiff - target) / target * 100;
    const within = Math.abs(err) <= 10;
    rows.push(["vs. target " + target + " \u03a9",
               (err >= 0 ? "+" : "") + err.toFixed(1) + " % \u2014 " + (within ? "inside the \u00b110 % band" : "outside the \u00b110 % band"),
               within ? "good" : "warn"]);
  }
  rows.push(["Propagation delay", (Math.sqrt(ee) / 299792458 * 1e12 * 0.0254).toFixed(1) + " ps/in"]);
  render("dp-out", rows);
}

/* ---------- battery ---------- */

function calcBattery() {
  const mah = val("bat-mah");
  const vc = numOr("bat-v", 3.7, 0.1);
  const S = Math.max(1, Math.round(numOr("bat-s", 1, 1) || 1));
  const P = Math.max(1, Math.round(numOr("bat-p", 1, 1) || 1));
  const load = val("bat-load");
  const usable = numOr("bat-usable", 80, 1, 100);
  if (!isFinite(mah) || !(mah > 0) || !isFinite(vc) || !isFinite(usable)) { render("bat-out", []); return; }
  const packV = vc * S;
  const packAh = mah / 1000 * P;
  const wh = packV * packAh;
  const rows = [
    ["Pack", S + "S" + P + "P at " + fmt(packV, "V") + " nominal"],
    ["Capacity", packAh.toPrecision(4) + " Ah"],
    ["Energy", wh.toPrecision(4) + " Wh (" + (wh * usable / 100).toPrecision(4) + " Wh usable at " + usable + " %)"]
  ];
  if (isFinite(load) && load > 0) {
    const watts = document.getElementById("bat-loadunit").value === "W";
    const amps = watts ? load / packV : load;
    const power = watts ? load : load * packV;
    const hours = packAh * usable / 100 / amps;
    rows.push(["Load", fmt(amps, "A") + " at " + fmt(power, "W")]);
    rows.push(["C-rate", (amps / packAh).toPrecision(3) + " C"]);
    rows.push(["Runtime", hours >= 1 ? hours.toPrecision(3) + " h (" + (hours * 60).toPrecision(3) + " min)"
                                     : (hours * 60).toPrecision(3) + " min"]);
  }
  render("bat-out", rows);
}

/* ---------- dBm chain (disabled: card hidden) ---------- */

function calcDbm() {
  const lin = val("db-in"), g = val("db-gain"), att = val("db-att");
  const z = numOr("db-z", 50, 1e-9);
  if (!isFinite(lin) || !isFinite(z)) { render("db-out", []); return; }
  const out = lin + (isFinite(g) ? g : 0) - (isFinite(att) ? att : 0);
  const volts = function (dbm) { return Math.sqrt(Math.pow(10, dbm / 10) * 1e-3 * z); };
  const watts = function (dbm) { return Math.pow(10, dbm / 10) * 1e-3; };
  render("db-out", [
    ["Output level", out.toFixed(2) + " dBm"],
    ["Net gain", (out - lin >= 0 ? "+" : "") + (out - lin).toFixed(2) + " dB"],
    ["Input", fmt(volts(lin), "V") + " rms, " + fmt(watts(lin), "W") + " into " + fmt(z, "Ω")],
    ["Output", fmt(volts(out), "V") + " rms, " + fmt(watts(out), "W") + " into " + fmt(z, "Ω")],
    ["Peak-to-peak out", fmt(volts(out) * 2 * Math.SQRT2, "V")]
  ]);
}

/* ---------- wiring ---------- */

const CALCS = {
  th:  { calc: calcThermal, inputs: ["th-p","th-jc","th-cs","th-sa","th-ja","th-tjmax","th-tjtarget","th-tj","th-ta"] },
  pdn: { calc: calcPDN, inputs: ["pdn-v","pdn-ripple","pdn-i","pdn-tr","pdn-fmax"] },
  pad: { calc: calcPad, inputs: ["pad-a","pad-z0","pad-z2","pad-series"] },
  ee:  { calc: calcEreff, inputs: ["ee-w","ee-h","ee-er","ee-f","ee-oz"] },
  dp:  { calc: calcDiff, inputs: ["dp-struct","dp-w","dp-s","dp-h","dp-er","dp-target","dp-oz"] },
  bat: { calc: calcBattery, inputs: ["bat-mah","bat-v","bat-s","bat-p","bat-load","bat-loadunit","bat-usable"] },
  ohm: { calc: calcOhm, inputs: ["ohm-v","ohm-i","ohm-r","ohm-p"] },
  div: { calc: calcDivider, inputs: ["div-vin","div-vout","div-r1","div-r2","div-rtot","div-iload","div-series"] },
  sp:  { calc: calcSP, inputs: ["sp-list","sp-type","sp-v"] },
  led: { calc: calcLED, inputs: ["led-vs","led-vf","led-if","led-r","led-series"] },
  ac:  { calc: calcAccuracy, inputs: ["ac-r1","ac-r2","ac-vin","ac-tol1","ac-tol2","ac-tcr1","ac-tcr2","ac-tmin","ac-tmax","ac-tnom","ac-age"] },
  flt: { calc: calcFilter, inputs: ["flt-type","flt-resp","flt-order","flt-r","flt-c","flt-l","flt-f"] },
  re:  { calc: calcReact, inputs: ["re-f","re-c","re-l","re-esl","re-esr","re-n","re-epc","re-dcr"] },
  tw:  { calc: calcTrace, inputs: ["tw-i","tw-w","tw-layer","tw-len","tw-f","tw-oz","tw-dt","tw-ta"] },
  via: { calc: calcVia, inputs: ["via-d","via-tp","via-h","via-pad","via-anti","via-er","via-i","via-n","via-arlimit","via-stub","via-dt"] },
  fu:  { calc: calcFuse, inputs: ["fu-w","fu-t","fu-k","fu-oz","fu-ta"] },
  spc: { calc: calcSpacing, inputs: ["spc-v"] },
  z:   { calc: calcZ, inputs: ["z-struct","z-w","z-h","z-er","z-ermask","z-c","z-s","z-f","z-oz"] },
  vs:  { calc: calcViaShield, inputs: ["vs-f","vs-tr","vs-er","vs-frac","vs-pitch","vs-len","vs-d"] },
  wl:  { calc: calcWave, inputs: ["wl-f","wl-tr","wl-eeff","wl-period","wl-div"] },
  xc:  { calc: calcXtal, inputs: ["xc-cl","xc-c1","xc-c2","xc-cs"] },
  pp:  { calc: calcPPM, inputs: ["pp-f","pp-ppm","pp-df"] },
  awg: { calc: calcAWG, inputs: ["awg-n","awg-len","awg-return","awg-i","awg-temp","awg-vsupply"] },
  nb:  { calc: function () { render("nb-out", []); }, inputs: ["nb-dec","nb-hex","nb-bin","nb-oct"] },
  rt:  { calc: function () {}, inputs: ["rt-pct","rt-ppm","rt-ppb","rt-ratio"] },
  cv:  { calc: function () {}, inputs: ["cv-mm","cv-mil","cv-c","cv-f","cv-db","cv-vr","cv-pr","cv-re","cv-im","cv-mag","cv-ang","cv-deg","cv-rad"] }
};

/* Typing in a field makes it an input again: the `computed` tag comes off
   before the calculator runs, so the value survives the clearing pass. */
for (const key in CALCS) {
  const c = CALCS[key];
  for (const fid of c.inputs) {
    const el = document.getElementById(fid);
    if (!el) continue;
    const handler = function () { el.classList.remove("computed"); c.calc(); };
    el.addEventListener("input", handler);
    el.addEventListener("change", handler);
  }
}

// the E-series setting feeds every calculator that suggests standard values
/* Editing any copy of a shared control writes through to its twins and
   recalculates every card, so two tabs can never disagree about the board. */
["copper", "dt", "ta", "series"].forEach(function (group) {
  mirrors(group).forEach(function (el) {
    ["input", "change"].forEach(function (ev) {
      el.addEventListener(ev, function () {
        mirrors(group).forEach(function (other) { if (other !== el) other.value = el.value; });
        for (const key in CALCS) CALCS[key].calc();
      });
    });
  });
});

const idf = function (x) { return x; };
wirePair([["cv-mm", idf, idf], ["cv-mil", function (v) { return v * MIL; }, function (c) { return c / MIL; }]]);
wirePair([["cv-c", idf, idf],
          ["cv-f", function (v) { return (v - 32) * 5 / 9; }, function (c) { return c * 9 / 5 + 32; }]]);
wirePair([["cv-db", idf, idf],
          ["cv-vr", function (v) { return 20 * Math.log10(v); }, function (c) { return Math.pow(10, c / 20); }],
          ["cv-pr", function (v) { return 10 * Math.log10(v); }, function (c) { return Math.pow(10, c / 10); }]]);
// ratio units share one canonical: the plain decimal ratio
wirePair([["rt-ratio", idf, idf],
          ["rt-pct", function (v) { return v / 100; }, function (c) { return c * 100; }],
          ["rt-ppm", function (v) { return v * 1e-6; }, function (c) { return c * 1e6; }],
          ["rt-ppb", function (v) { return v * 1e-9; }, function (c) { return c * 1e9; }]]);

// rectangular <-> polar: two values in, two out, so wirePair does not fit
function wireRectPolar() {
  const ids = ["cv-re", "cv-im", "cv-mag", "cv-ang"];
  const g = function (id) { return parseVal(document.getElementById(id).value); };
  const put = function (id, v) {
    const el = document.getElementById(id);
    el.value = isFinite(v) ? +v.toPrecision(6) : "";
  };
  ids.forEach(function (id) {
    document.getElementById(id).addEventListener("input", function () {
      const polar = id === "cv-mag" || id === "cv-ang";
      if (polar) {
        const m = g("cv-mag"), a = g("cv-ang");
        if (!isFinite(m) || !isFinite(a)) return;
        put("cv-re", m * Math.cos(a * Math.PI / 180));
        put("cv-im", m * Math.sin(a * Math.PI / 180));
      } else {
        const re = g("cv-re"), im = g("cv-im");
        if (!isFinite(re) || !isFinite(im)) return;
        put("cv-mag", Math.hypot(re, im));
        put("cv-ang", Math.atan2(im, re) * 180 / Math.PI);
      }
    });
  });
}
wireRectPolar();
wirePair([["cv-deg", idf, idf],
          ["cv-rad", function (v) { return v * 180 / Math.PI; }, function (c) { return c * Math.PI / 180; }]]);

// number bases drive each other directly, in BigInt so nothing is rounded
for (const nbf of NB_FIELDS) {
  const nid = nbf[0], radix = nbf[1];
  const el = document.getElementById(nid);
  el.addEventListener("input", function () {
    el.classList.remove("computed");
    const raw = el.value.trim();
    if (!raw) {
      for (const o of NB_FIELDS) {
        if (o[0] === nid) continue;
        const oe = document.getElementById(o[0]);
        oe.value = ""; oe.classList.remove("computed");
      }
      el.classList.remove("bad"); render("nb-out", []); return;
    }
    const v = parseInt_(raw, radix);
    el.classList.toggle("bad", v === null);
    if (v === null) return;
    showBases(v, nid);
  });
}

/* The plot's hover layer. Listeners live on the container, which persists,
   so redrawing the chart never has to re-attach them. Keyboard focus gets the
   same readout as the pointer. */
(function () {
  const host = document.getElementById("flt-graph");
  if (!host) return;
  host.addEventListener("pointermove", function (e) { moveCursor(e.clientX); });
  host.addEventListener("keydown", function (e) {
    if (fltGraph.index === undefined) return;
    let step = 0;
    if (e.key === "ArrowRight") step = 1;
    else if (e.key === "ArrowLeft") step = -1;
    else if (e.key === "Home") { showCursorAt(0); e.preventDefault(); return; }
    else if (e.key === "End") { showCursorAt(FLT_SAMPLES - 1); e.preventDefault(); return; }
    else return;
    if (e.shiftKey) step *= 10;
    showCursorAt(Math.max(0, Math.min(FLT_SAMPLES - 1, fltGraph.index + step)));
    e.preventDefault();
  });
})();

/* ---------- copy results to the clipboard ----------

   One handler serves every card: it reads that card's own inputs and results
   back out of the DOM, so a card gains a working Copy button just by
   existing, and the text always matches what is on screen. */

function cardText(card) {
  const holder = card.closest(".panel, .subpanel");
  const title = card.querySelector("h3") || (holder && holder.querySelector("h2"));
  const lines = title ? [title.textContent.trim()] : [];
  const inputs = [];
  card.querySelectorAll(".field").forEach(function (f) {
    const el = f.querySelector("input, select, textarea");
    const lab = f.querySelector("label");
    if (!el || !lab) return;
    const v = el.tagName === "SELECT" ? el.options[el.selectedIndex].textContent.trim() : el.value.trim();
    if (!v) return;
    inputs.push("  " + lab.textContent.trim().replace(/\s+/g, " ") + ": " + v +
                (el.classList.contains("computed") ? "   [calculated]" : ""));
  });
  if (inputs.length) lines.push("", "Inputs", inputs.join("\n"));
  const out = [];
  card.querySelectorAll("dl.results").forEach(function (dl) {
    const dts = dl.querySelectorAll("dt"), dds = dl.querySelectorAll("dd");
    for (let i = 0; i < dts.length; i++) {
      const k = dts[i].textContent.trim(), v = dds[i] ? dds[i].textContent.trim() : "";
      if (!k && !v) continue;
      out.push("  " + (k ? k + ": " : "") + v);
    }
  });
  card.querySelectorAll("table").forEach(function (t) {
    if (t.hidden) return;
    t.querySelectorAll("tr").forEach(function (tr) {
      const cells = [];
      tr.querySelectorAll("th, td").forEach(function (c) { cells.push(c.textContent.trim()); });
      if (cells.length) out.push("  " + cells.join("\t"));
    });
  });
  if (out.length) lines.push("", "Results", out.join("\n"));
  return lines.join("\n") + "\n";
}

function copyText(text, btn) {
  const was = btn.dataset.label;
  const done = function (ok) {
    btn.textContent = ok ? "Copied" : "Copy failed";
    btn.classList.toggle("copied", ok);
    setTimeout(function () { btn.textContent = was; btn.classList.remove("copied"); }, 1600);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(function () { done(true); },
                                            function () { done(legacyCopy(text)); });
  } else {
    done(legacyCopy(text));
  }
}

/* A file:// page has no async clipboard in some browsers; fall back. */
function legacyCopy(text) {
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.setAttribute("readonly", "");
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.select();
  let ok = false;
  try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
  document.body.removeChild(ta);
  return ok;
}

// every Reset button gains a Copy sibling; the pair becomes the card's footer
document.querySelectorAll("button.reset").forEach(function (btn) {
  const card = btn.closest(".card");
  const foot = document.createElement("div");
  foot.className = "cardfoot";
  btn.parentNode.insertBefore(foot, btn);
  const copy = document.createElement("button");
  copy.type = "button";
  copy.textContent = "Copy results";
  copy.dataset.label = "Copy results";
  copy.addEventListener("click", function () { copyText(cardText(card), copy); });
  foot.appendChild(copy);
  foot.appendChild(btn);
  btn.addEventListener("click", function () {
    const c = CALCS[btn.dataset.reset];
    if (!c) return;
    for (const fid of c.inputs) {
      const el = document.getElementById(fid);
      if (!el) continue;
      if (el.tagName === "SELECT") {
        const marked = el.querySelector("[selected]");
        el.selectedIndex = marked ? Array.prototype.indexOf.call(el.options, marked) : 0;
      } else {
        el.value = "";
      }
      el.classList.remove("bad");
      el.classList.remove("computed");
    }
    c.calc();
  });
});

/* ---------- tabs ---------- */

/* Sub-tabs are looked up per panel rather than hard-coded to one bar, so any
   panel can carry them. Deep links are "#panel" or "#panel-sub". */

const tabbar = document.getElementById("tabbar");

function subbarOf(panelId) {
  const pnl = document.getElementById("panel-" + panelId);
  return pnl ? pnl.querySelector("nav.subtabs") : null;
}

/* Remember where the user was. localStorage can be unavailable or throw
   outright (a private window, a browser set to block site data, a file://
   origin treated as opaque), so every access is guarded and the page simply
   opens on the first tab when it cannot read or write. */
const LAST_TAB_KEY = "eecalc.lastTab";

function remember(tabName) {
  try {
    const sub = currentSub(tabName);
    localStorage.setItem(LAST_TAB_KEY, sub ? tabName + "-" + sub : tabName);
  } catch (e) { /* nothing to do; the tool works fine without it */ }
}

function recall() {
  try { return localStorage.getItem(LAST_TAB_KEY) || ""; } catch (e) { return ""; }
}

function showTab(name) {
  let found = false;
  tabbar.querySelectorAll("button[data-tab]").forEach(function (b) {
    const on = b.dataset.tab === name;
    if (on) found = true;
    b.setAttribute("aria-selected", on ? "true" : "false");
  });
  if (!found) return false;
  document.querySelectorAll(".panel").forEach(function (pnl) {
    pnl.classList.toggle("active", pnl.id === "panel-" + name);
  });
  return true;
}

function showSub(panelId, name) {
  const bar = subbarOf(panelId);
  if (!bar) return false;
  let found = false;
  bar.querySelectorAll("button[data-sub]").forEach(function (b) {
    const on = b.dataset.sub === name;
    if (on) found = true;
    b.setAttribute("aria-selected", on ? "true" : "false");
  });
  if (!found) return false;
  document.querySelectorAll("#panel-" + panelId + " .subpanel").forEach(function (sp) {
    sp.classList.toggle("active", sp.id === "sub-" + name);
  });
  return true;
}

function currentSub(panelId) {
  const bar = subbarOf(panelId);
  if (!bar) return null;
  const on = bar.querySelector('button[aria-selected="true"]');
  return on ? on.dataset.sub : null;
}

function hashFor(panelId) {
  const sub = currentSub(panelId);
  return sub ? panelId + "-" + sub : panelId;
}

tabbar.addEventListener("click", function (e) {
  const btn = e.target.closest("button[data-tab]");
  if (!btn) return;
  showTab(btn.dataset.tab);
  try { location.hash = hashFor(btn.dataset.tab); } catch (err) {}
  remember(btn.dataset.tab);
});

document.querySelectorAll("nav.subtabs").forEach(function (bar) {
  const panelId = bar.closest(".panel").id.replace("panel-", "");
  bar.addEventListener("click", function (e) {
    const btn = e.target.closest("button[data-sub]");
    if (!btn) return;
    showSub(panelId, btn.dataset.sub);
    try { location.hash = panelId + "-" + btn.dataset.sub; } catch (err) {}
    remember(panelId);
  });
});

/* Deep links, including the pre-regrouping ones so old links keep working. */
const LEGACY_HASH = {
  ohm: "fund", sp: "fund", div: "res-div", led: "res-led", acc: "res-acc",
  rc: "filt", react: "filt", xtal: "filt", pcb: "copper", z: "signal", util: "util"
};
(function () {
  /* An explicit link wins over the remembered tab, which wins over the
     default. */
  let h = location.hash.replace("#", "") || recall();
  if (!h) return;
  if (LEGACY_HASH[h]) h = LEGACY_HASH[h];
  const dash = h.indexOf("-");
  if (dash > 0 && showTab(h.slice(0, dash))) { showSub(h.slice(0, dash), h.slice(dash + 1)); return; }
  showTab(h);
})();

// first paint: a browser may have restored values into the fields
for (const key in CALCS) CALCS[key].calc();
</script>
</body>
</html>
"""


def main() -> None:
    html = HTML
    try:
        from theme_inline import inline_into
        html = inline_into(html)
    except ImportError:
        print("build_page: theme_inline not found - writing page without house styling", file=sys.stderr)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
