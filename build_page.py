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
  /* the 2-9 lines inside each decade: bunching towards the next decade is
     what makes a log axis legible at a glance, so they are always drawn */
  .chart .gridmin { stroke: var(--a-line); stroke-width: 1; fill: none; opacity: .45; }
  .chart .axis { stroke: var(--a-line-strong); stroke-width: 1; fill: none; }
  .chart .curve { stroke: var(--a-link); stroke-width: 2; fill: none; stroke-linejoin: round; }
  .chart .hair { stroke: var(--a-ink-muted); stroke-width: 1; }
  /* a second series is told apart by dash and by its own direct label, never
     by hue alone, so it survives any colour vision and a monochrome print */
  .chart .curve.alt { stroke-dasharray: 5 4; }
  .chart .band { fill: var(--a-link); opacity: .13; stroke: none; }
  .chart text.tag { fill: var(--a-ink-secondary); font-size: 10px; }
  .chart .knob { fill: var(--a-link); stroke: var(--a-bg-panel); stroke-width: 2; }
  .chart text { fill: var(--a-ink-muted); font-size: 10px; font-family: var(--a-font-mono); }
  .chart text.read { fill: var(--a-ink); font-size: 11px; }
  .chart text.readlabel { fill: var(--a-ink-secondary); font-size: 10px; }
  svg.schem .wire { fill: none; stroke: currentColor; stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; }
  svg.schem .dot { fill: currentColor; stroke: none; }
  svg.schem .opt { stroke-dasharray: 4 3; }
  /* the governing equation, beside the drawing rather than buried in a note */
  .plate { margin: .5rem 0 0; padding: .4rem .6rem; max-width: 16rem; background: var(--a-bg-subtle); border: var(--a-border) solid var(--a-line); border-radius: var(--a-radius-sm); font-family: var(--a-font-mono); font-size: var(--a-text-xs); color: var(--a-ink-secondary); }
  /* a cross-section is monochrome, so the key maps line style to material */
  .key { margin: .4rem 0 0; max-width: 16rem; font-size: var(--a-text-xs); color: var(--a-ink-muted); line-height: 1.5; }
  svg.schem text { fill: currentColor; stroke: none; font-family: var(--a-font-mono); font-size: 11px; }
  .fields { display: flex; flex-wrap: wrap; gap: .9rem 1.2rem; }
  .field { display: flex; flex-direction: column; gap: .25rem; }
  /* an author display rule beats the UA default for [hidden], so say it again */
  .field[hidden] { display: none; }
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
  /* the explain button sits at the far end of the same row as copy and reset */
  .cardfoot .explain { margin-left: auto; }
  dialog.help { width: min(46rem, calc(100% - 2rem)); padding: 0; color: var(--a-ink); background: var(--a-bg-panel); border: var(--a-border) solid var(--a-line); border-radius: var(--a-radius-sm); }
  dialog.help::backdrop { background: rgb(0 0 0 / .45); }
  .help-head { display: flex; align-items: baseline; gap: 1rem; padding: 1rem 1.2rem .7rem; border-bottom: var(--a-border) solid var(--a-line); }
  .help-head h3 { margin: 0; flex: 1 1 auto; font-size: var(--a-text-h3); }
  .help-head button { font: inherit; font-size: var(--a-text-xs); color: var(--a-link); background: none; border: none; cursor: pointer; padding: 0; }
  .help-head button:hover { color: var(--a-link-hover); text-decoration: underline; }
  .help-body { padding: 1rem 1.2rem 1.3rem; max-height: 70vh; overflow-y: auto; font-size: var(--a-text-sm); line-height: 1.65; }
  .help-body p { margin: 0 0 .85rem; }
  .help-body ul { margin: 0 0 .85rem; padding-left: 1.15rem; }
  .help-body li { margin: 0 0 .4rem; }
  .help-body code { font-family: var(--a-font-mono); font-size: .95em; }
  .help-body .eq { display: block; margin: .75rem 0; padding: .55rem .75rem; font-family: var(--a-font-mono); font-size: var(--a-text-xs); line-height: 1.9; color: var(--a-ink); background: var(--a-bg-subtle); border-radius: var(--a-radius-sm); overflow-x: auto; }
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
  <button role="tab" data-tab="tol" aria-selected="false">Tolerance</button>
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
    <svg class="schem" width="240" height="240" viewBox="0 0 240 240" role="img" aria-label="Ohm and power law wheel: the four quantities at the hub, each surrounded by the three ways of computing it from the other two">
      <path class="wire" d="M120.0 68.0 L120.0 8.0 A112 112 0 0 1 176.0 23.0 L146.0 75.0 A52 52 0 0 0 120.0 68.0 Z"/>
      <text x="135.3" y="63.0" font-size="9" dominant-baseline="middle" transform="rotate(-75.0 135.3 63.0)">V=I&middot;R</text>
      <path class="wire" d="M146.0 75.0 L176.0 23.0 A112 112 0 0 1 217.0 64.0 L165.0 94.0 A52 52 0 0 0 146.0 75.0 Z"/>
      <text x="161.7" y="78.3" font-size="9" dominant-baseline="middle" transform="rotate(-45.0 161.7 78.3)">V=P/I</text>
      <path class="wire" d="M165.0 94.0 L217.0 64.0 A112 112 0 0 1 232.0 120.0 L172.0 120.0 A52 52 0 0 0 165.0 94.0 Z"/>
      <text x="177.0" y="104.7" font-size="9" dominant-baseline="middle" transform="rotate(-15.0 177.0 104.7)">V&sup2;=P&middot;R</text>
      <path class="wire" d="M172.0 120.0 L232.0 120.0 A112 112 0 0 1 217.0 176.0 L165.0 146.0 A52 52 0 0 0 172.0 120.0 Z"/>
      <text x="177.0" y="135.3" font-size="9" dominant-baseline="middle" transform="rotate(15.0 177.0 135.3)">R=V/I</text>
      <path class="wire" d="M165.0 146.0 L217.0 176.0 A112 112 0 0 1 176.0 217.0 L146.0 165.0 A52 52 0 0 0 165.0 146.0 Z"/>
      <text x="161.7" y="161.7" font-size="9" dominant-baseline="middle" transform="rotate(45.0 161.7 161.7)">R=V&sup2;/P</text>
      <path class="wire" d="M146.0 165.0 L176.0 217.0 A112 112 0 0 1 120.0 232.0 L120.0 172.0 A52 52 0 0 0 146.0 165.0 Z"/>
      <text x="135.3" y="177.0" font-size="9" dominant-baseline="middle" transform="rotate(75.0 135.3 177.0)">R=P/I&sup2;</text>
      <path class="wire" d="M120.0 172.0 L120.0 232.0 A112 112 0 0 1 64.0 217.0 L94.0 165.0 A52 52 0 0 0 120.0 172.0 Z"/>
      <text x="92.8" y="221.4" font-size="9" dominant-baseline="middle" transform="rotate(285.0 92.8 221.4)">P=V&middot;I</text>
      <path class="wire" d="M94.0 165.0 L64.0 217.0 A112 112 0 0 1 23.0 176.0 L75.0 146.0 A52 52 0 0 0 94.0 165.0 Z"/>
      <text x="45.8" y="194.2" font-size="9" dominant-baseline="middle" transform="rotate(315.0 45.8 194.2)">P=I&sup2;&middot;R</text>
      <path class="wire" d="M75.0 146.0 L23.0 176.0 A112 112 0 0 1 8.0 120.0 L68.0 120.0 A52 52 0 0 0 75.0 146.0 Z"/>
      <text x="18.6" y="147.2" font-size="9" dominant-baseline="middle" transform="rotate(345.0 18.6 147.2)">P=V&sup2;/R</text>
      <path class="wire" d="M68.0 120.0 L8.0 120.0 A112 112 0 0 1 23.0 64.0 L75.0 94.0 A52 52 0 0 0 68.0 120.0 Z"/>
      <text x="18.6" y="92.8" font-size="9" dominant-baseline="middle" transform="rotate(375.0 18.6 92.8)">I=V/R</text>
      <path class="wire" d="M75.0 94.0 L23.0 64.0 A112 112 0 0 1 64.0 23.0 L94.0 75.0 A52 52 0 0 0 75.0 94.0 Z"/>
      <text x="45.8" y="45.8" font-size="9" dominant-baseline="middle" transform="rotate(405.0 45.8 45.8)">I=P/V</text>
      <path class="wire" d="M94.0 75.0 L64.0 23.0 A112 112 0 0 1 120.0 8.0 L120.0 68.0 A52 52 0 0 0 94.0 75.0 Z"/>
      <text x="92.8" y="18.6" font-size="9" dominant-baseline="middle" transform="rotate(435.0 92.8 18.6)">I&sup2;=P/R</text>
      <circle class="wire" cx="120" cy="120" r="50"/>
      <path class="wire" d="M120.0 70.0 L120.0 170.0 M170.0 120.0 L70.0 120.0"/>
      <text x="139.4" y="100.6" text-anchor="middle" dominant-baseline="middle" font-size="13">V</text>
      <text x="139.4" y="139.4" text-anchor="middle" dominant-baseline="middle" font-size="13">R</text>
      <text x="100.6" y="139.4" text-anchor="middle" dominant-baseline="middle" font-size="13">P</text>
      <text x="100.6" y="100.6" text-anchor="middle" dominant-baseline="middle" font-size="13">I</text>
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
    <div class="diagram" id="sp-diagram"></div>
    </div>
    <dl class="results" id="sp-out"></dl>
    <button class="reset" data-reset="sp">Reset</button>
  </div>
</section>

<section class="panel" id="panel-res">
  <h2>Resistors</h2>
  <p class="hint">Dividers and LED bias. Both solve in whichever direction you have the numbers for.</p>
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



</section>

<section class="panel" id="panel-tol">
  <h2>Tolerance</h2>
  <p class="hint">What initial tolerance, temperature and time drift do to a part&rsquo;s value &mdash; and, separately, what they do to a divider&rsquo;s <em>ratio</em>, which is a different question because a divider only cares how its two legs move relative to each other.</p>
<div class="card">
    <h3>Component tolerance budget</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="ec-type">Component</label>
        <select id="ec-type">
          <option value="R" selected>Resistor</option>
          <option value="C">Capacitor</option>
          <option value="L">Inductor</option>
          <option value="X">Crystal / oscillator</option>
          <option value="V">Voltage reference</option>
        </select>
      </div>
      <div class="field"><label for="ec-val" id="ec-vallabel">Nominal value (&Omega;)</label><input id="ec-val" inputmode="decimal" placeholder="e.g. 10k"></div>
      <div class="field" id="ec-f-diel" hidden><label for="ec-diel">Dielectric</label>
        <select id="ec-diel">
          <option value="C0G">C0G / NP0 &mdash; class 1</option>
          <option value="X5R" selected>X5R</option>
          <option value="X7R">X7R</option>
          <option value="X6S">X6S</option>
          <option value="X7S">X7S</option>
          <option value="X8R">X8R</option>
          <option value="Y5V">Y5V</option>
          <option value="Z5U">Z5U</option>
          <option value="other">Other EIA code&hellip;</option>
        </select>
      </div>
      <div class="field" id="ec-f-code" hidden><label for="ec-code">EIA code</label><input id="ec-code" placeholder="e.g. X6T"></div>
      <div class="field"><label for="ec-tol" id="ec-tollabel">Initial tolerance (%)</label><input id="ec-tol" inputmode="decimal" placeholder="1"></div>
      <div class="field" id="ec-f-tc"><label for="ec-tc" id="ec-tclabel">Temperature coefficient (ppm/&deg;C)</label><input id="ec-tc" inputmode="decimal" placeholder="100"></div>
      <div class="field"><label for="ec-tmin">T min (&deg;C)</label><input id="ec-tmin" inputmode="decimal" placeholder="-40"></div>
      <div class="field"><label for="ec-tmax">T max (&deg;C)</label><input id="ec-tmax" inputmode="decimal" placeholder="85"></div>
      <div class="field"><label for="ec-tnom">T nominal (&deg;C)</label><input id="ec-tnom" inputmode="decimal" placeholder="25"></div>
      <div class="field"><label for="ec-age" id="ec-agelabel">Ageing (ppm/year)</label><input id="ec-age" inputmode="decimal" placeholder="0"></div>
      <div class="field"><label for="ec-life" id="ec-lifelabel">Service life (years)</label><input id="ec-life" inputmode="decimal" placeholder="10"></div>
      <div class="field" id="ec-f-bias" hidden><label for="ec-bias">DC bias loss at the working voltage (%)</label><input id="ec-bias" inputmode="decimal" placeholder="e.g. 40"></div>
      <div class="field" id="ec-f-hyst" hidden><label for="ec-hyst">Thermal hysteresis (ppm)</label><input id="ec-hyst" inputmode="decimal" placeholder="e.g. 75"></div>
    </div>
    <div class="diagram">
      <svg class="schem" width="250" height="140" viewBox="0 0 250 140" role="img" aria-label="A tolerance band about a nominal value, stepping wider as temperature and then time are added">
      <text x="6" y="84">nominal</text>
      <path class="wire" d="M56 80 H235"/>
      <path class="dot" d="M64 64 H121 V54 H178 V44 H235 V116 H178 V106 H121 V96 H64 Z" opacity="0.16"/>
      <path class="wire opt" d="M121 40 V120 M178 40 V120"/>
      <text x="70" y="34">initial</text>
      <text x="130" y="34">+ temp</text>
      <text x="187" y="34">+ time</text>
    </svg>
      <p class="plate">worst case = &Sigma;|e<sub>i</sub>| &middot; RSS = &radic;(&Sigma;e<sub>i</sub>&sup2;)</p>
      <p class="key">Each contribution widens the band; none of them cancel.</p>
    </div>
    </div>
    <dl class="results" id="ec-out"></dl>
    <p class="note">Worst case adds every contribution at its limit, which is what a screened build must survive. RSS treats them as independent random variables, which is the realistic spread across a production run &mdash; but it assumes independence, and a reel of parts from one lot is <em>not</em> independent, so RSS understates lot-to-lot risk. Class 2 ceramics are the awkward case: their temperature figure is a bound over the dielectric&rsquo;s whole rated range and the curve is not linear, so it cannot be scaled to a narrower range, and DC bias commonly costs more than every other contribution combined.</p>
    <button class="reset" data-reset="ec">Reset</button>
  </div>
  <div class="card">
    <h3>Divider ratio error</h3>
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
    <div id="ac-graph" class="chart" tabindex="0" role="img" aria-label="Ratio error across temperature"></div>
    <dl class="results" id="ac-out"></dl>
    <p class="note">Worst case is exact (both legs at their opposing extremes); RSS treats the contributions as independent random variables, which is the realistic figure for a production run but assumes the two TCRs are uncorrelated. Blank fields default to 1 %, 100 ppm/&deg;C, and &minus;40/+85/25 &deg;C.</p>
    <button class="reset" data-reset="ac">Reset</button>
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
    <div class="diagram">
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
      <p class="plate">X<sub>C</sub> = 1/2&pi;fC &middot; X<sub>L</sub> = 2&pi;fL &middot; f<sub>SRF</sub> = 1/2&pi;&radic;(LC)</p>
    </div>
    </div>
    <div id="re-graph" class="chart" tabindex="0" role="img" aria-label="Impedance against frequency"></div>
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
  <p class="hint">Five resistive topologies, between equal or unequal impedances. The E-series suggestion shows what stock parts would actually deliver.</p>
  <div class="card">
    <h3>Attenuator pad</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="pad-topo">Topology</label>
        <select id="pad-topo">
          <option value="pi" selected>PI</option>
          <option value="t">T</option>
          <option value="bridge">Bridged T</option>
          <option value="l">L</option>
          <option value="split">Resistive splitter</option>
        </select>
      </div>
      <div class="field"><label for="pad-a">Attenuation (dB)</label><input id="pad-a" inputmode="decimal" placeholder="e.g. 6"></div>
      <div class="field"><label for="pad-zin">Source Z<sub>in</sub> (&Omega;)</label><input id="pad-zin" inputmode="decimal" placeholder="50"></div>
      <div class="field"><label for="pad-zout">Load Z<sub>out</sub> (&Omega;)</label><input id="pad-zout" inputmode="decimal" placeholder="50"></div>
          <div class="field"><label for="pad-series">E-series</label>
        <select id="pad-series" data-mirror="series"><option value="E12">E12 (10 %)</option><option value="E24">E24 (5 %)</option><option value="E96" selected>E96 (1 %)</option></select>
      </div>
    </div>
    <div class="diagram" id="pad-diagram"></div>
    </div>
    <dl class="results" id="pad-out"></dl>
    <p class="note">PI and T match <em>any</em> two impedances, not just equal ones, and reduce to the familiar symmetric formulas when Z<sub>in</sub> = Z<sub>out</sub>. Between unequal impedances every topology has a minimum attenuation set by their ratio, 10&middot;log<sub>10</sub>(2r &minus; 1 + 2&radic;(r(r&minus;1))) with r the larger over the smaller; ask for less and no resistive network can match both ends, so use a transformer. A bridged T and a splitter are symmetric only. The delivered attenuation for stock parts is a full transducer-loss calculation against the actual source and load, so it stays right when the impedances differ.</p>
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
    <div class="diagram" id="tw-diagram"></div>
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
      <div class="field"><label for="via-tr">Signal rise time (s, optional)</label><input id="via-tr" inputmode="decimal" placeholder="e.g. 200p"></div>
      <div class="field"><label for="via-z0">Trace Z<sub>0</sub> (&Omega;, optional)</label><input id="via-z0" inputmode="decimal" placeholder="50"></div>
          <div class="field"><label for="via-dt">Temp rise (&deg;C)</label><input id="via-dt" data-mirror="dt" inputmode="decimal" placeholder="10"></div>
    </div>
    <div class="diagram" id="via-diagram"></div>
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
    <div class="diagram">
      <svg class="schem" width="215" height="130" viewBox="0 0 215 130" role="img" aria-label="Trace cross-section showing width and copper thickness, the two dimensions that set the fusing current">
      <rect class="wire" x="18" y="62" width="180" height="30"/>
      <text x="22" y="82">substrate</text>
      <path class="dot" d="M62 44 H154 V60 H62 Z"/>
      <path class="wire" d="M62 30 V40 M154 30 V40 M62 35 H154"/>
      <text x="100" y="26">w</text>
      <path class="wire" d="M162 44 H172 M162 60 H172 M167 44 V60"/>
      <text x="176" y="56">t</text>
      <text x="18" y="112">cross-section = w &#215; t</text>
    </svg>
      <p class="key">the fuse is the copper, not the current.</p>
      <p class="plate">I = A &middot; &radic;( log<sub>10</sub>(1 + (T<sub>m</sub>&minus;T<sub>a</sub>) / (234+T<sub>a</sub>)) / 33t ), A in circular mils</p>
    </div>
    </div>
    <div id="fu-graph" class="chart" tabindex="0" role="img" aria-label="Fusing current against fault duration"></div>
    <dl class="results" id="fu-out"></dl>
    <p class="note">Copper is treated as a rectangle of w &times; t; real etched copper is a trapezoid with slightly less metal, so a narrow trace fuses a little sooner than this. Onderdonk&rsquo;s equation, copper melting at 1083 &deg;C, adiabatic &mdash; valid for events up to a few seconds; longer events shed heat and survive more.</p>
    <button class="reset" data-reset="fu">Reset</button>
  </div>
</div>
<div class="subpanel" id="sub-spc">
  <h2>Conductor Spacing</h2>
  <p class="hint">Two standards, because they answer different questions. IPC-2221 gives a bare minimum clearance by environment; IEC 60664-1 gives the clearance <em>and</em> the creepage that a mains- or high-voltage-connected product is actually assessed against.</p>
  <div class="card">
    <h3>Conductor spacing (IPC-2221 Table 6-1)</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="spc-v">Peak voltage between conductors (V)</label><input id="spc-v" inputmode="decimal" placeholder="e.g. 48"></div>
    </div>
    <div class="diagram">
      <svg class="schem" width="225" height="130" viewBox="0 0 225 130" role="img" aria-label="Two conductors on a substrate separated by a gap, with an optional coating over them">
      <rect class="wire" x="14" y="58" width="196" height="30"/>
      <path class="dot" d="M40 40 H86 V56 H40 Z"/>
      <path class="dot" d="M138 40 H184 V56 H138 Z"/>
      <path class="wire" d="M86 48 H138"/>
      <path class="wire" d="M86 34 V44 M138 34 V44"/>
      <text x="102" y="30">S</text>
      <path class="wire opt" d="M30 34 H194 V58"/>
      <text x="120" y="24">coating, if any</text>
    </svg>
      <p class="key">S is the gap between copper edges, and the. minimum depends on coating and altitude.</p>
      <p class="plate">IPC-2221 Table 6-1, by environment &mdash; above 500 V, a per-volt slope</p>
    </div>
    </div>
    <dl class="results" id="spc-out"></dl>
    <p class="note">Minimum spacing per environment. B1 internal layers; B2 external uncoated &le;3050 m; B3 external uncoated &gt;3050 m; B4 external with permanent polymer coating; A5 external conformal coated; A6 external component leads uncoated; A7 component leads conformal coated.</p>
    <button class="reset" data-reset="spc">Reset</button>
  </div>
  <div class="card">
    <h3>Clearance and creepage (IEC 60664-1)</h3>
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="iec-ins">Insulation</label>
        <select id="iec-ins">
          <option value="functional">Functional</option>
          <option value="basic" selected>Basic</option>
          <option value="reinforced">Reinforced</option>
        </select>
      </div>
      <div class="field"><label for="iec-vrms">Working voltage (V rms or DC)</label><input id="iec-vrms" inputmode="decimal" placeholder="230"></div>
      <div class="field"><label for="iec-vpeak">Peak working voltage (V)</label><input id="iec-vpeak" inputmode="decimal" placeholder="1.41 &times; rms"></div>
      <div class="field"><label for="iec-ovc">Overvoltage category</label>
        <select id="iec-ovc">
          <option value="1">I &mdash; protected, inside equipment</option>
          <option value="2" selected>II &mdash; appliance on a fixed installation</option>
          <option value="3">III &mdash; fixed installation, distribution</option>
          <option value="4">IV &mdash; origin of the installation</option>
        </select>
      </div>
      <div class="field"><label for="iec-vmains">Supply voltage to earth (V)</label><input id="iec-vmains" inputmode="decimal" placeholder="230"></div>
      <div class="field"><label for="iec-pd">Pollution degree</label>
        <select id="iec-pd">
          <option value="1">1 &mdash; sealed, no pollution</option>
          <option value="2" selected>2 &mdash; normal, occasional condensation</option>
          <option value="3">3 &mdash; conductive pollution</option>
        </select>
      </div>
      <div class="field"><label for="iec-mg">Material group</label>
        <select id="iec-mg">
          <option value="1">I &mdash; CTI &ge; 600</option>
          <option value="2" selected>II &mdash; CTI 400 to 599</option>
          <option value="3">IIIa &mdash; CTI 175 to 399</option>
          <option value="4">IIIb &mdash; CTI 100 to 174</option>
        </select>
      </div>
      <div class="field"><label for="iec-pcb">Construction</label>
        <select id="iec-pcb">
          <option value="1" selected>Printed board</option>
          <option value="0">Other insulation</option>
        </select>
      </div>
      <div class="field"><label for="iec-field">Field</label>
        <select id="iec-field">
          <option value="inhomogeneous" selected>Inhomogeneous &mdash; any real layout</option>
          <option value="homogeneous">Homogeneous &mdash; deliberately rounded electrodes</option>
        </select>
      </div>
      <div class="field"><label for="iec-alt">Altitude (m)</label><input id="iec-alt" inputmode="decimal" placeholder="2000"></div>
    </div>
    <div class="diagram">
      <svg class="schem" width="250" height="150" viewBox="0 0 250 150" role="img" aria-label="Two conductors on a board, with clearance measured through the air between them and creepage measured along the surface, around a groove">
      <rect class="wire" x="14" y="76" width="222" height="40"/>
      <text x="20" y="102">insulator</text>
      <path class="dot" d="M24 56 H86 V74 H24 Z"/>
      <path class="dot" d="M164 56 H226 V74 H164 Z"/>
      <path class="wire" d="M110 76 V96 H140 V76"/>
      <path class="wire opt" d="M86 40 H164"/>
      <path class="wire" d="M86 36 V44 M164 36 V44"/>
      <text x="110" y="32">clearance</text>
      <path class="wire" d="M86 74 H110 V94 H140 V74 H164" stroke-dasharray="3 2"/>
      <text x="112" y="136">creepage</text>
      <text x="112" y="70">groove</text>
    </svg>
      <p class="plate">clearance &times; altitude factor &middot; creepage &times; 2 if reinforced</p>
      <p class="key">Clearance is the shortest path <b>through air</b>; creepage follows the <b>surface</b>, so a groove wider than the minimum adds to it. The card reports that minimum groove width.</p>
    </div>
    </div>
    <dl class="results" id="iec-out"></dl>
    <p class="note">IEC 60664-1:2020-05, the standard IPC-2221 does not cover. Clearance is set by the transient the insulation must survive &mdash; derived from the overvoltage category and the supply voltage &mdash; and by the working peak; creepage is set by the working rms voltage, the pollution degree and the material group, and doubles for reinforced insulation. Creepage is never reported below the clearance, since the surface path cannot be shorter than the air path. <b>Outside its scope:</b> above 30 kHz (that is IEC 60664-3), conformal coating or potting (60664-4), pollution degree 4, and insulation through anything other than air. Material group comes from the laminate&rsquo;s CTI, which the fabricator states &mdash; most FR-4 is IIIa, which is worse than people assume.</p>
    <button class="reset" data-reset="iec">Reset</button>
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
      <div class="field"><label for="z-tand">Loss tangent tan&nbsp;&delta;</label><input id="z-tand" inputmode="decimal" placeholder="0.02 (FR-4)"></div>
      <div class="field"><label for="z-rough">Copper roughness (&micro;m rms)</label><input id="z-rough" inputmode="decimal" placeholder="0.4 (VLP) to 2 (standard)"></div>
          <div class="field"><label for="z-oz">Copper weight</label>
        <select id="z-oz" data-mirror="copper"><option value="17.5">0.5 oz (17.5 &micro;m)</option><option value="35" selected>1 oz (35 &micro;m)</option><option value="70">2 oz (70 &micro;m)</option><option value="105">3 oz (105 &micro;m)</option></select>
      </div>
    </div>
    <div class="diagram" id="z-diagram"></div>
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
    <div class="diagram" id="dp-diagram"></div>
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
    <div class="diagram">
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
    </svg>
      <p class="key">some field is in air, so &#949;eff sits between (&#949;r+1)/2 and &#949;r.</p>
      <p class="plate">&epsilon;<sub>eff</sub> = (&epsilon;<sub>r</sub>+1)/2 + (&epsilon;<sub>r</sub>&minus;1)/2 &middot; (1 + 10h/w)<sup>&minus;ab</sup> &mdash; Hammerstad&ndash;Jensen</p>
    </div>
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
    <div class="diagram">
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
      <p class="plate">&lambda; = c / (f &middot; &radic;&epsilon;<sub>eff</sub>) &middot; f<sub>knee</sub> = 0.35 / t<sub>r</sub></p>
    </div>
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
    <div class="diagram">
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
      <text x="176" y="160">setback</text>
      <path class="wire" d="M114 54 V72"/>
      <text x="120" y="66">d</text>
    </svg>
      <p class="plate">pitch &le; &lambda;/10, &lambda; = c / (f &middot; &radic;&epsilon;<sub>r</sub>)</p>
    </div>
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
    <div class="diagram">
      <svg class="schem" width="150" height="190" viewBox="0 0 150 190" role="img" aria-label="Thermal resistance chain from junction to ambient">
      <rect class="wire" x="40" y="12" width="70" height="20"/>
      <text x="54" y="26">junction</text>
      <path class="wire" d="M75 32 V48"/>
      <rect class="wire" x="63" y="48" width="24" height="26"/>
      <text x="94" y="65">&#952;jc</text>
      <path class="wire" d="M75 74 V86"/>
      <text x="58" y="84" text-anchor="end">case</text>
      <rect class="wire" x="63" y="86" width="24" height="26"/>
      <text x="94" y="103">&#952;cs</text>
      <path class="wire" d="M75 112 V124"/>
      <text x="58" y="122" text-anchor="end">sink</text>
      <rect class="wire" x="63" y="124" width="24" height="26"/>
      <text x="94" y="141">&#952;sa</text>
      <path class="wire" d="M75 150 V164 M55 164 H95 M60 171 H90 M65 178 H85"/>
      <text x="8" y="168">ambient</text>
    </svg>
      <p class="plate">T<sub>j</sub> = T<sub>a</sub> + P &middot; &Sigma;&theta;</p>
    </div>
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
      <text x="14" y="30">V rail</text>
      <path class="wire" d="M96 34 V58 M90 34 H102 M90 58 H102"/>
      <text x="104" y="50">&#916;V ripple</text>
      <path class="wire" d="M14 96 H70 V78 H150 V96 H216"/>
      <text x="14" y="118">I load</text>
      <path class="wire" d="M160 78 V96 M154 78 H166 M154 96 H166"/>
      <text x="170" y="92">&#916;I step</text>
      <text x="14" y="12">Z target = &#916;V / &#916;I</text>
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
      <div class="field"><label for="bat-chem">Cell chemistry</label>
        <select id="bat-chem">
          <option value="lipo" selected>LiPo</option>
          <option value="lihv">LiHV</option>
          <option value="liion">Li-ion</option>
          <option value="lifepo4">LiFePO4 / LiFe</option>
          <option value="nimh">NiMH</option>
          <option value="lead">Lead-acid</option>
          <option value="custom">Custom</option>
        </select>
      </div>
      <div class="field"><label for="bat-mah">Cell capacity (mAh)</label><input id="bat-mah" inputmode="decimal" placeholder="e.g. 5000"></div>
      <div class="field"><label for="bat-vfull">Cell full (V)</label><input id="bat-vfull" inputmode="decimal" placeholder="4.2"></div>
      <div class="field"><label for="bat-v">Cell nominal (V)</label><input id="bat-v" inputmode="decimal" placeholder="3.7"></div>
      <div class="field"><label for="bat-vmin">Cell minimum (V)</label><input id="bat-vmin" inputmode="decimal" placeholder="3.0"></div>
      <div class="field"><label for="bat-s">Cells in series (S)</label><input id="bat-s" inputmode="numeric" placeholder="1"></div>
      <div class="field"><label for="bat-p">Cells in parallel (P)</label><input id="bat-p" inputmode="numeric" placeholder="1"></div>
      <div class="field"><label for="bat-load">Load (A or W)</label><input id="bat-load" inputmode="decimal" placeholder="e.g. 2"></div>
      <div class="field"><label for="bat-loadunit">Load is</label>
        <select id="bat-loadunit"><option value="A" selected>Amps</option><option value="W">Watts</option></select>
      </div>
      <div class="field"><label for="bat-usable">Usable capacity (%)</label><input id="bat-usable" inputmode="decimal" placeholder="80"></div>
      <div class="field"><label for="bat-crate">Cell discharge rating (C, optional)</label><input id="bat-crate" inputmode="decimal" placeholder="e.g. 25"></div>
    </div>
    <div class="diagram">
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
    </svg>
      <p class="key">S cells in series raise voltage. P strings in parallel raise capacity. pack V = S &#215; cell V, pack Ah = P &#215; cell Ah.</p>
    </div>
    </div>
    <div id="bat-graph" class="chart" tabindex="0" role="img" aria-label="Typical discharge curve"></div>
    <dl class="results" id="bat-out"></dl>
    <p class="note">Pick a chemistry and its three cell voltages fill in, highlighted; they are used from that moment and typing over one makes it yours, so Custom is for a cell that matches none of the presets. Full is the <em>resting</em> voltage of a charged cell, which is why lead-acid shows a separate charging setpoint. Charge rates are the ordinary rate for the chemistry; maximum discharge is not tabulated because it varies a hundredfold within one chemistry, so it comes from the cell&rsquo;s own C rating. Runtime assumes a flat load and ignores temperature, cable loss and cell ageing.</p>
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


<div class="subpanel" id="sub-cv">
  <h2>Conversions</h2>
  <p class="hint">Units, ratios and number bases. Every card here works both ways: edit any field and the rest follow.</p>
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
  drawSP(document.getElementById("sp-type").value);
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
  const W = 560, H = 216, ML = 46, MR = 20, MT = 20, MB = 34;
  const pw = W - ML - MR, ph = H - MT - MB;
  /* Ticks land on round decades - 10 Hz, 1 kHz - rather than on multiples of
     f0, so the range is snapped outward to whole powers of ten. x is stored as
     log10 of the absolute frequency. */
  const d0 = Math.floor(Math.log10(st.f0) - 2), d1 = Math.ceil(Math.log10(st.f0) + 2);
  const pts = [];
  let lo = 0;
  for (let i = 0; i < FLT_SAMPLES; i++) {
    const lx = d0 + (d1 - d0) * i / (FLT_SAMPLES - 1);
    const db = fltDb(Math.pow(10, lx) / st.f0, st);
    pts.push([lx, db]);
    if (db < lo) lo = db;
  }
  const yMax = Math.max(5, Math.ceil(Math.max.apply(null, pts.map(function (q) { return q[1]; })) / 5) * 5 + 5);
  const yMin = Math.max(-120, Math.floor(Math.max(lo, -120) / 20) * 20);
  const X = function (lx) { return ML + (lx - d0) / (d1 - d0) * pw; };
  const Y = function (db) { return MT + (yMax - db) / (yMax - yMin) * ph; };

  const out = ['<svg width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + " " + H + '">'];
  for (let d = d0; d <= d1; d++) {
    if (d < d1) {
      for (let k = 2; k <= 9; k++) {
        out.push('<path class="gridmin" d="M' + X(d + Math.log10(k)).toFixed(1) + " " + MT +
                 " V" + (MT + ph) + '"/>');
      }
    }
    out.push('<path class="grid" d="M' + X(d).toFixed(1) + " " + MT + " V" + (MT + ph) + '"/>');
    const anchor = d === d0 ? "start" : d === d1 ? "end" : "middle";
    out.push('<text x="' + X(d).toFixed(1) + '" y="' + (H - 18) + '" text-anchor="' + anchor + '">' +
             fmt(Math.pow(10, d), "Hz") + "</text>");
  }
  for (let db = yMin; db <= yMax; db += 20) {
    out.push('<path class="grid" d="M' + ML + " " + Y(db).toFixed(1) + " H" + (ML + pw) + '"/>');
    out.push('<text x="' + (ML - 6) + '" y="' + (Y(db) + 3.5).toFixed(1) + '" text-anchor="end">' + db + "</text>");
  }
  out.push('<text x="' + ML + '" y="' + (MT - 7) + '">dB</text>');
  out.push('<path class="axis" d="M' + ML + " " + MT + " V" + (MT + ph) + " H" + (ML + pw) + '"/>');
  let d2 = "M";
  pts.forEach(function (q, i) { d2 += (i ? " L" : "") + X(q[0]).toFixed(1) + " " + Y(q[1]).toFixed(1); });
  out.push('<path class="curve" d="' + d2 + '"/>');
  out.push('<g id="flt-cursor"></g>');
  out.push("</svg>");
  document.getElementById("flt-graph").innerHTML = out.join("");
  fltGraph.pts = pts;
  fltGraph.st = st;
  fltGraph.box = { W: W, H: H, ML: ML, MT: MT, pw: pw, ph: ph, d0: d0, d1: d1, yMax: yMax, yMin: yMin };
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
  const x = b.ML + (q[0] - b.d0) / (b.d1 - b.d0) * b.pw;
  const y = b.MT + (b.yMax - q[1]) / (b.yMax - b.yMin) * b.ph;
  const f = Math.pow(10, q[0]);
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

/* ---------- cross-section drawing ----------

   Saturn's most useful habit is a drawing whose every symbol is also a field
   label, redrawn when the structure selector moves so it can never describe
   a geometry you are not solving. These primitives give all the cross-sections
   one dimension-line convention, so the reader learns to read one drawing
   rather than five. */

function svgOpen(w, h, label) {
  return '<svg class="schem" width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + ' ' + h +
         '" role="img" aria-label="' + label + '">';
}
function dimH(x0, x1, y, label) {
  return '<path class="wire" d="M' + x0 + ' ' + (y - 4) + ' V' + (y + 4) + ' M' + x1 + ' ' + (y - 4) +
         ' V' + (y + 4) + ' M' + x0 + ' ' + y + ' H' + x1 + '"/>' +
         '<text x="' + ((x0 + x1) / 2 - 4) + '" y="' + (y - 8) + '">' + label + '</text>';
}
function dimV(x, y0, y1, label) {
  return '<path class="wire" d="M' + (x - 4) + ' ' + y0 + ' H' + (x + 4) + ' M' + (x - 4) + ' ' + y1 +
         ' H' + (x + 4) + ' M' + x + ' ' + y0 + ' V' + y1 + '"/>' +
         '<text x="' + (x + 7) + '" y="' + ((y0 + y1) / 2 + 4) + '">' + label + '</text>';
}
function plane(x0, x1, y) { return '<path class="wire" d="M' + x0 + ' ' + y + ' H' + x1 + '" stroke-width="3"/>'; }
function copper(x0, x1, y0, y1) {
  return '<path class="dot" d="M' + x0 + ' ' + y0 + ' H' + x1 + ' V' + y1 + ' H' + x0 + ' Z"/>';
}

const XSEC_KEY = '<p class="key">filled = copper &middot; outline = dielectric &middot; ' +
                 'heavy line = reference plane &middot; dashed = optional</p>';
/* The trace cross-sections are rectangles because the formulas are. Saturn
   draws the etched trapezoid because it models an etch factor; we do not, so
   drawing one would claim an accuracy the maths does not have. */
const ETCH_KEY = '<p class="key">Copper is drawn rectangular because that is what the model assumes. Real etched copper is a trapezoid, so a narrow trace has slightly less metal than this.</p>';

/* ---- single-ended impedance ---- */

const Z_LABEL = {
  ms:    "Bare microstrip cross-section: trace of width w and thickness t on a dielectric of height h over a reference plane",
  mscov: "Covered microstrip cross-section: as bare microstrip, with a cover of its own permittivity over the trace",
  sl:    "Centred stripline cross-section: trace midway between two reference planes separated by b",
  asym:  "Offset stripline cross-section: trace between two planes, nearer one than the other",
  cpwg:  "Grounded coplanar cross-section: trace with a ground pour either side across a gap, over a reference plane"
};
const Z_PLATE = {
  ms:    "Z<sub>0</sub> = Z<sub>01</sub>(u) / &radic;&epsilon;<sub>eff</sub>, u = w/h &mdash; Hammerstad&ndash;Jensen",
  mscov: "Z<sub>0</sub> = Z<sub>01</sub>(u) / &radic;&epsilon;<sub>eff</sub>(&epsilon;<sub>r</sub>, cover) &mdash; fully covered limit",
  sl:    "Z<sub>0</sub> = (60/&radic;&epsilon;<sub>r</sub>) &middot; ln(1.9b / (0.8w + t))",
  asym:  "Z<sub>0</sub> = Z<sub>0,centred</sub> &middot; f(h, c) / f(b/2, b/2)",
  cpwg:  "Z<sub>0</sub> = 60&pi; / (&radic;&epsilon;<sub>eff</sub> &middot; (K/K&prime;|<sub>k</sub> + K/K&prime;|<sub>k3</sub>))"
};

function drawZ(struct) {
  const W = 250, H = 170, L = 16, R = 206;
  const x0 = 96, x1 = 154;                       // the trace
  const g = [svgOpen(W, H, Z_LABEL[struct])];

  if (struct === "ms" || struct === "mscov" || struct === "cpwg") {
    g.push('<text x="' + L + '" y="22">air, εr = 1</text>');
    /* The plane sits 3 px clear of the dielectric outline. Drawn on top of it
       the heavy stroke is indistinguishable from the rectangle edge and the
       key's "heavy line = reference plane" means nothing; drawn inside it, the
       rectangle edge moves onto the w dimension label. Outside is the only
       place that is clear of both. */
    g.push('<rect class="wire" x="' + L + '" y="70" width="' + (R - L) + '" height="44"/>');
    g.push('<text x="' + (L + 6) + '" y="98">\u03b5r</text>');
    g.push(plane(L, R, 117));
    g.push('<text x="' + L + '" y="136">reference plane</text>');
    g.push(copper(x0, x1, 56, 68));
    g.push(dimH(x0, x1, 44, "w"));
    g.push(dimV(222, 70, 117, "h"));
    g.push('<path class="wire" d="M' + (x1 + 6) + ' 56 H' + (x1 + 14) + ' M' + (x1 + 6) + ' 68 H' + (x1 + 14) +
           ' M' + (x1 + 10) + ' 56 V68"/><text x="' + (x1 + 17) + '" y="66">t</text>');
    if (struct === "mscov") {
      g.push('<path class="wire opt" d="M' + (x0 - 40) + ' 70 V50 H' + (x1 + 40) + ' V70"/>');
      /* clear of the w dimension line, which starts at x0 */
      g.push('<text x="' + (x0 - 40) + '" y="38">cover \u03b5r</text>');
    }
    if (struct === "cpwg") {
      g.push(copper(L + 2, x0 - 30, 56, 68));
      g.push(copper(x1 + 30, R - 2, 56, 68));
      g.push(dimH(x1, x1 + 30, 44, "s"));
      g.push('<text x="' + (L + 4) + '" y="52">ground pour</text>');
    }
  } else {
    const top = 44, bot = 130;
    const ty = struct === "sl" ? 81 : 74;        // trace top edge
    g.push('<rect class="wire" x="' + L + '" y="' + top + '" width="' + (R - L) + '" height="' + (bot - top) + '"/>');
    g.push(plane(L, R, top - 3));
    g.push(plane(L, R, bot + 3));
    g.push('<text x="' + (L + 6) + '" y="' + (bot - 10) + '">\u03b5r</text>');
    g.push(copper(x0, x1, ty, ty + 12));
    g.push(dimH(x0, x1, ty - 10, "w"));
    if (struct === "sl") {
      g.push(dimV(222, top, bot, "b"));
    } else {
      g.push(dimV(222, top, ty, "h"));
      g.push(dimV(222, ty + 12, bot, "c"));
    }
  }
  g.push("</svg>");
  /* SVG text cannot wrap, so anything longer than a symbol goes in a
     paragraph underneath where the browser can break it */
  const caption = struct === "sl" ? '<p class="key">Planes above and below, trace centred; b is the plane-to-plane spacing.</p>'
                : struct === "asym" ? '<p class="key">h is the distance to the near plane, c to the far one.</p>'
                : struct === "cpwg" ? '<p class="key">s is the gap between the track and the ground pour either side of it.</p>'
                : "";
  document.getElementById("z-diagram").innerHTML =
    g.join("") + '<p class="plate">' + Z_PLATE[struct] + "</p>" + caption + XSEC_KEY + ETCH_KEY;
}

/* ---- differential pair ---- */

function drawDiff(struct) {
  const W = 250, H = 160, L = 16, R = 206;
  const a0 = 74, a1 = 118, b0 = 146, b1 = 190;   // the two traces
  const ms = struct === "ms";
  const g = [svgOpen(W, H, ms
      ? "Edge-coupled microstrip: two traces of width w separated by a gap s, on a dielectric of height h over one plane"
      : "Edge-coupled stripline: two traces of width w separated by a gap s, midway between two planes")];
  if (ms) {
    g.push('<rect class="wire" x="' + L + '" y="72" width="' + (R - L) + '" height="42"/>');
    g.push('<text x="' + (L + 6) + '" y="98">\u03b5r</text>');
    g.push(plane(L, R, 117));
    g.push('<text x="' + L + '" y="136">reference plane</text>');
    g.push(copper(a0, a1, 58, 70));
    g.push(copper(b0, b1, 58, 70));
    g.push(dimH(a0, a1, 46, "w"));
    g.push(dimH(b0, b1, 46, "w"));
    g.push(dimH(a1, b0, 30, "s"));
    g.push(dimV(222, 72, 117, "h"));
  } else {
    const top = 40, bot = 124, ty = 76;
    g.push('<rect class="wire" x="' + L + '" y="' + top + '" width="' + (R - L) + '" height="' + (bot - top) + '"/>');
    g.push(plane(L, R, top - 3));
    g.push(plane(L, R, bot + 3));
    g.push('<text x="' + (L + 6) + '" y="' + (bot - 10) + '">\u03b5r</text>');
    g.push(copper(a0, a1, ty, ty + 12));
    g.push(copper(b0, b1, ty, ty + 12));
    g.push(dimH(a1, b0, ty - 10, "s"));
    g.push(dimH(a0, a1, ty - 10, "w"));
    g.push(dimH(b0, b1, ty - 10, "w"));
    g.push(dimV(222, top, bot, "h"));
  }
  g.push("</svg>");
  document.getElementById("dp-diagram").innerHTML = g.join("") +
    '<p class="plate">Z<sub>diff</sub> = 2Z<sub>0</sub>(1 &minus; k&middot;e<sup>&minus;m&middot;s/h</sup>)</p>' +
    (ms ? "" : '<p class="key">Planes above and below, pair centred between them.</p>') +
    XSEC_KEY + ETCH_KEY;
}

/* ---- trace current ----

   External and internal are not a cosmetic distinction: the IPC constant
   halves, because a buried trace sheds heat only through the laminate. The
   drawing says which one you are solving. */

function drawTrace(layer) {
  const W = 250, H = 155, L = 18, R = 210;
  const x0 = 92, x1 = 156;
  const ext = layer !== "int";
  const g = [svgOpen(W, H, ext
      ? "External trace: copper of width w and thickness t on top of the board, one face exposed to air"
      : "Internal trace: copper of width w and thickness t buried in the laminate, with no exposed face")];
  if (ext) {
    g.push('<text x="' + L + '" y="24">air</text>');
    g.push('<rect class="wire" x="' + L + '" y="66" width="' + (R - L) + '" height="42"/>');
    g.push('<text x="' + (L + 6) + '" y="92">substrate</text>');
    g.push(copper(x0, x1, 52, 64));
    g.push(dimH(x0, x1, 40, "w"));
    g.push('<path class="wire" d="M' + (x1 + 6) + ' 52 H' + (x1 + 14) + ' M' + (x1 + 6) + ' 64 H' + (x1 + 14) +
           ' M' + (x1 + 10) + ' 52 V64"/><text x="' + (x1 + 17) + '" y="62">t</text>');
    g.push('<text x="' + L + '" y="132">k = 0.048</text>');
  } else {
    g.push('<rect class="wire" x="' + L + '" y="40" width="' + (R - L) + '" height="76"/>');
    g.push('<text x="' + (L + 6) + '" y="58">laminate</text>');
    g.push(copper(x0, x1, 72, 84));
    g.push(dimH(x0, x1, 62, "w"));
    g.push('<path class="wire" d="M' + (x1 + 6) + ' 72 H' + (x1 + 14) + ' M' + (x1 + 6) + ' 84 H' + (x1 + 14) +
           ' M' + (x1 + 10) + ' 72 V84"/><text x="' + (x1 + 17) + '" y="82">t</text>');
    g.push('<text x="' + L + '" y="140">k = 0.024</text>');
  }
  g.push("</svg>");
  document.getElementById("tw-diagram").innerHTML = g.join("") +
    '<p class="plate">I = k &middot; &Delta;T<sup>0.44</sup> &middot; A<sup>0.725</sup>, A = w&middot;t in mil&sup2;</p>' +
    '<p class="key">' + (ext ? "One face is in air, so the trace convects."
                             : "Buried, so heat leaves only through the board.") + "</p>" +
    ETCH_KEY + '<p class="key">A rectangular model therefore reads a little optimistic on a narrow trace.</p>';
}

/* ---- via ----

   Four of this card's fields name a diameter or a length that words cannot
   pin down: pad, antipad, aspect ratio and stub. Saturn answers all four with
   a section and a plan view, and so does this. */

function drawVia(hasStub) {
  const W = 272, H = 208;
  const bx0 = 14, bx1 = 150, by0 = 34, by1 = 152;
  const h0 = 70, h1 = 94;                          // the drilled hole
  const g = [svgOpen(W, H, "Via section showing drill, plating, board thickness and the unused stub, "
                         + "beside a plan view of the concentric drill, plating, pad and antipad")];
  g.push('<rect class="wire" x="' + bx0 + '" y="' + by0 + '" width="' + (bx1 - bx0) + '" height="' + (by1 - by0) + '"/>');
  g.push(copper(h0 - 5, h0, by0, by1));            // barrel plating, both walls
  g.push(copper(h1, h1 + 5, by0, by1));
  g.push(copper(h0 - 22, h1 + 22, by0 - 5, by0));  // pads, top and bottom
  g.push(copper(h0 - 22, h1 + 22, by1, by1 + 5));
  g.push(dimH(h0, h1, by0 + 30, "d"));
  /* H runs inside the board on the left, where nothing else does - put it
     outside on the right and it lands on the plating label */
  g.push(dimV(30, by0, by1, "H"));
  g.push('<text x="' + bx0 + '" y="24">pad</text>');
  g.push('<text x="' + (h1 + 12) + '" y="' + (by0 + 64) + '">plating</text>');
  g.push('<text x="' + bx0 + '" y="' + (H - 8) + '">aspect ratio = H / d</text>');
  if (hasStub) {
    g.push('<path class="wire opt" d="M' + (h1 + 9) + ' ' + (by1 - 44) + ' V' + by1 + '"/>');
    g.push('<path class="wire" d="M' + (h0 - 26) + ' ' + (by1 - 44) + ' H' + (h1 + 26) + '"/>');
    g.push('<text x="' + (h1 + 12) + '" y="' + (by1 - 18) + '">stub</text>');
  } else {
    g.push('<text x="' + bx0 + '" y="' + (H - 24) + '">stub: none given</text>');
  }
  const cx = 212, cy = 88;
  g.push('<circle class="wire opt" cx="' + cx + '" cy="' + cy + '" r="46"/>');
  g.push('<circle class="wire" cx="' + cx + '" cy="' + cy + '" r="32"/>');
  g.push('<circle class="wire" cx="' + cx + '" cy="' + cy + '" r="19"/>');
  g.push('<circle class="wire" cx="' + cx + '" cy="' + cy + '" r="13"/>');
  g.push('<text x="' + (cx - 44) + '" y="' + (cy + 60) + '">plan view</text>');
  g.push('<text x="' + (cx - 44) + '" y="' + (cy + 76) + '">drill, plating,</text>');
  g.push('<text x="' + (cx - 44) + '" y="' + (cy + 92) + '">pad, antipad</text>');
  g.push("</svg>");
  document.getElementById("via-diagram").innerHTML = g.join("") +
    '<p class="plate">C &asymp; 1.41&middot;&epsilon;<sub>r</sub>&middot;H&middot;d<sub>pad</sub> / (d<sub>anti</sub> &minus; d<sub>pad</sub>)</p>' +
    '<p class="key">The antipad is the clearance in the plane, so it is drawn dashed &mdash; it is absence of copper, not copper.' +
    (hasStub ? ' The bar across the barrel is the layer the signal leaves on; everything below it is the stub.' : "") + "</p>";
}

/* ---- series and parallel ----

   The selector switches the arithmetic between resistors, capacitors and
   inductors, so the symbols switch with it. */

function drawSP(kind) {
  const NAME = { R: "resistors", C: "capacitors", L: "inductors" };
  const g = [svgOpen(258, 128, "Two " + NAME[kind] + " in series, and two in parallel")];
  g.push(symSeries(kind, 10, 68, 40));
  g.push(symSeries(kind, 68, 126, 40));
  g.push('<text x="30" y="20">1</text><text x="88" y="20">2</text>');
  g.push('<text x="40" y="76">Series</text>');
  g.push('<path class="wire" d="M204 12 V24 M204 24 H176 M204 24 H232"/>');
  g.push('<circle class="dot" cx="204" cy="24" r="2.5"/>');
  g.push(symShunt(kind, 176, 24, 88));
  g.push(symShunt(kind, 232, 24, 88));
  g.push('<path class="wire" d="M176 88 H232 M204 88 V102"/>');
  g.push('<circle class="dot" cx="204" cy="88" r="2.5"/>');
  g.push('<text x="180" y="122">Parallel</text>');
  g.push("</svg>");
  document.getElementById("sp-diagram").innerHTML = g.join("") + '<p class="plate">' +
    (kind === "C"
      ? "series: 1/C = &Sigma;1/C<sub>i</sub> &middot; parallel: C = &Sigma;C<sub>i</sub>"
      : "series: X = &Sigma;X<sub>i</sub> &middot; parallel: 1/X = &Sigma;1/X<sub>i</sub>") + "</p>";
}

/* ---- attenuator pads ----

   Three topologies, because the second-impedance field only makes sense
   against the L pad and that was the one the drawing left out. */

function drawPad(topo) {
  /* One topology at a time, chosen by the selector, so the picture can never
     describe a network you are not designing. symSeries and symShunt stop the
     wire at the component body; branch a shunt clear of a series body or the
     junction dot lands inside the resistor. */
  const W = 250, H = 150;
  const gnd = function (x, y) {
    return '<path class="wire" d="M' + (x - 14) + ' ' + y + ' H' + (x + 14) +
           ' M' + (x - 9) + ' ' + (y + 5) + ' H' + (x + 9) +
           ' M' + (x - 4) + ' ' + (y + 10) + ' H' + (x + 4) + '"/>';
  };
  /* dy lets a label drop below the port, for the bridged T where the bridging
     arm rises out of the rail exactly where the label would otherwise sit */
  const port = function (x, y, label, anchor, dy) {
    return '<circle class="wire" cx="' + x + '" cy="' + y + '" r="3.5"/>' +
           '<text x="' + (anchor === "end" ? x - 6 : x + 6) + '" y="' + (y + (dy || -8)) +
           '" text-anchor="' + (anchor || "start") + '">' + label + "</text>";
  };
  const LABEL = { pi: "PI pad", t: "T pad", bridge: "Bridged T", l: "L pad", split: "Resistive splitter" };
  const g = [svgOpen(W, H, LABEL[topo] + " topology")];
  const rail = 44;

  if (topo === "pi") {
    g.push(port(14, rail, "in"));
    g.push('<path class="wire" d="M17.5 ' + rail + ' H44 M116 ' + rail + ' H206"/>');
    g.push(symSeries("R", 44, 116, rail));
    g.push('<circle class="dot" cx="44" cy="' + rail + '" r="2.5"/><circle class="dot" cx="116" cy="' + rail + '" r="2.5"/>');
    g.push(symShunt("R", 44, rail, 100));
    g.push(symShunt("R", 116, rail, 100));
    g.push('<path class="wire" d="M44 100 H116 M80 100 V108"/>');
    g.push(gnd(80, 108));
    g.push(port(209.5, rail, "out", "end"));
  } else if (topo === "t") {
    g.push(port(14, rail, "in"));
    g.push('<path class="wire" d="M17.5 ' + rail + ' H22 M188 ' + rail + ' H206"/>');
    g.push(symSeries("R", 22, 80, rail));
    g.push(symSeries("R", 100, 188, rail));
    g.push('<path class="wire" d="M80 ' + rail + ' H100"/>');
    g.push('<circle class="dot" cx="90" cy="' + rail + '" r="2.5"/>');
    g.push(symShunt("R", 90, rail, 100));
    g.push('<path class="wire" d="M90 100 V108"/>');
    g.push(gnd(90, 108));
    g.push(port(209.5, rail, "out", "end"));
  } else if (topo === "bridge") {
    /* two Z0 arms in series, one resistor bridging them, one shunt at the
       midpoint - the bridging element is what makes it a bridged T */
    g.push(port(14, 64, "in", "start", 18));
    g.push('<path class="wire" d="M17.5 64 H22 M188 64 H206"/>');
    g.push(symSeries("R", 22, 80, 64));
    g.push(symSeries("R", 100, 188, 64));
    g.push('<path class="wire" d="M80 64 H100"/>');
    g.push('<circle class="dot" cx="24" cy="64" r="2.5"/><circle class="dot" cx="186" cy="64" r="2.5"/>');
    g.push('<circle class="dot" cx="90" cy="64" r="2.5"/>');
    g.push('<path class="wire" d="M24 64 V26 M186 64 V26"/>');
    g.push(symSeries("R", 24, 186, 26));
    g.push('<text x="96" y="13">bridging</text>');
    g.push(symShunt("R", 90, 64, 118));
    g.push('<path class="wire" d="M90 118 V124"/>');
    g.push(gnd(90, 124));
    g.push(port(209.5, 64, "out", "end", 18));
  } else if (topo === "split") {
    /* a Y of three equal resistors: one per port */
    g.push(port(14, 74, "in"));
    g.push('<path class="wire" d="M17.5 74 H22"/>');
    g.push(symSeries("R", 22, 96, 74));
    g.push('<circle class="dot" cx="106" cy="74" r="2.5"/>');
    g.push('<path class="wire" d="M96 74 H106 M106 74 V34 M106 74 V114"/>');
    g.push(symSeries("R", 120, 194, 34));
    g.push(symSeries("R", 120, 194, 114));
    g.push('<path class="wire" d="M106 34 H120 M106 114 H120 M194 34 H206 M194 114 H206"/>');
    g.push(port(209.5, 34, "out 1", "end"));
    g.push(port(209.5, 114, "out 2", "end"));
  } else {
    g.push(port(14, rail, "in"));
    g.push('<path class="wire" d="M17.5 ' + rail + ' H22 M110 ' + rail + ' H206"/>');
    g.push(symSeries("R", 22, 100, rail));
    g.push('<path class="wire" d="M100 ' + rail + ' H110"/>');
    g.push('<circle class="dot" cx="110" cy="' + rail + '" r="2.5"/>');
    g.push(symShunt("R", 110, rail, 100));
    g.push('<path class="wire" d="M110 100 V108"/>');
    g.push(gnd(110, 108));
    g.push(port(209.5, rail, "out", "end"));
  }
  g.push("</svg>");

  const KEY = {
    pi: "Both shunt legs differ when the impedances differ; they are equal only in a matched pad.",
    t: "Both series arms differ when the impedances differ; they are equal only in a matched pad.",
    bridge: "Symmetric only. The two series arms are exactly Z0, so only the bridging and shunt resistors set the attenuation.",
    l: "The only asymmetric topology here, and the only one that cannot be matched at both ends at an arbitrary attenuation.",
    split: "Fixed at 6 dB per output. Its ports are only 6 dB isolated from each other, which is its real limitation."
  };
  document.getElementById("pad-diagram").innerHTML = g.join("") +
    '<p class="plate">L = 10<sup>A/10</sup> (power) &middot; A&prime; = (L+1)/(L&minus;1)</p>' +
    '<p class="key">' + KEY[topo] + "</p>";
}

/* ---------- explanatory plots ----------

   Three cards turn on a relationship rather than a geometry, and a curve says
   in one glance what a results row says in a sentence. Same conventions as
   the filter response: hairline grid, 2px curves, a crosshair that snaps to
   the nearest sample, no legend box - each series carries its own direct
   label - and every value the hover shows also appears in the results list,
   so the plot enhances and never gates. */

const MINI = {};

function miniPlot(hostId, spec) {
  /* MT leaves a line above the plot for the unit, which otherwise lands on
     top of the highest y tick label */
  const W = 520, H = 198, ML = 54, MR = 62, MT = 26, MB = 32;
  const pw = W - ML - MR, ph = H - MT - MB;
  const all = [];
  spec.series.forEach(function (se) { se.pts.forEach(function (q) { all.push(q); }); });
  const xs = all.map(function (q) { return q[0]; }), ys = all.map(function (q) { return q[1]; });
  const x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs);
  const y0 = spec.yMin !== undefined ? spec.yMin : Math.min.apply(null, ys);
  const y1 = spec.yMax !== undefined ? spec.yMax : Math.max.apply(null, ys);
  const X = function (v) { return ML + (v - x0) / ((x1 - x0) || 1) * pw; };
  const Y = function (v) { return MT + (y1 - v) / ((y1 - y0) || 1) * ph; };

  const out = ['<svg width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + ' ' + H + '">'];
  (spec.xMinor || []).forEach(function (at) {
    if (at < x0 || at > x1) return;
    out.push('<path class="gridmin" d="M' + X(at).toFixed(1) + " " + MT + " V" + (MT + ph) + '"/>');
  });
  spec.xTicks.forEach(function (t, i) {
    /* the end labels are anchored inwards so they cannot hang off the SVG */
    const anchor = i === 0 ? "start" : i === spec.xTicks.length - 1 ? "end" : "middle";
    out.push('<path class="grid" d="M' + X(t.at).toFixed(1) + " " + MT + " V" + (MT + ph) + '"/>');
    out.push('<text x="' + X(t.at).toFixed(1) + '" y="' + (H - 14) + '" text-anchor="' + anchor + '">' + t.label + "</text>");
  });
  spec.yTicks.forEach(function (t) {
    out.push('<path class="grid" d="M' + ML + " " + Y(t.at).toFixed(1) + " H" + (ML + pw) + '"/>');
    out.push('<text x="' + (ML - 6) + '" y="' + (Y(t.at) + 3.5).toFixed(1) + '" text-anchor="end">' + t.label + "</text>");
  });
  out.push('<text x="' + ML + '" y="' + (MT - 9) + '">' + spec.yUnit + "</text>");
  out.push('<path class="axis" d="M' + ML + " " + MT + " V" + (MT + ph) + " H" + (ML + pw) + '"/>');

  if (spec.band) {
    let d = "M";
    spec.band[0].forEach(function (q, i) { d += (i ? " L" : "") + X(q[0]).toFixed(1) + " " + Y(q[1]).toFixed(1); });
    for (let i = spec.band[1].length - 1; i >= 0; i--) {
      const q = spec.band[1][i];
      d += " L" + X(q[0]).toFixed(1) + " " + Y(q[1]).toFixed(1);
    }
    out.push('<path class="band" d="' + d + ' Z"/>');
  }
  spec.series.forEach(function (se) {
    let d = "M";
    se.pts.forEach(function (q, i) { d += (i ? " L" : "") + X(q[0]).toFixed(1) + " " + Y(q[1]).toFixed(1); });
    out.push('<path class="curve' + (se.alt ? " alt" : "") + '" d="' + d + '"/>');
    const last = se.pts[se.pts.length - 1];
    out.push('<text class="tag" x="' + (X(last[0]) + 6).toFixed(1) + '" y="' + (Y(last[1]) + 3.5).toFixed(1) +
             '">' + se.name + "</text>");
  });
  (spec.hlines || []).forEach(function (m) {
    out.push('<path class="hair" d="M' + ML + " " + Y(m.at).toFixed(1) + " H" + (ML + pw) + '"/>');
    out.push('<text class="tag" x="' + (ML + 5) + '" y="' + (Y(m.at) - 4).toFixed(1) + '">' + m.label + "</text>");
  });
  (spec.marks || []).forEach(function (m) {
    out.push('<path class="hair" d="M' + X(m.at).toFixed(1) + " " + MT + " V" + (MT + ph) + '"/>');
    out.push('<text class="tag" x="' + (X(m.at) + 5).toFixed(1) + '" y="' + (MT + 11) + '">' + m.label + "</text>");
  });
  out.push('<g id="' + hostId + '-cursor"></g></svg>');

  const host = document.getElementById(hostId);
  host.innerHTML = out.join("") + (spec.note ? '<p class="key">' + spec.note + "</p>" : "");
  host.setAttribute("aria-label", spec.label);
  MINI[hostId] = { spec: spec, X: X, Y: Y, ML: ML, MT: MT, pw: pw, ph: ph, W: W };
}

function miniClear(hostId) {
  const host = document.getElementById(hostId);
  if (host) { host.innerHTML = ""; delete MINI[hostId]; }
}

function miniCursor(hostId, clientX) {
  const st = MINI[hostId];
  if (!st) return;
  const host = document.getElementById(hostId);
  const svg = host.querySelector("svg");
  if (!svg) return;
  const r = svg.getBoundingClientRect();
  const px = (clientX - r.left) * (st.W / (r.width || st.W));
  const n = st.spec.series[0].pts.length;
  let i = Math.round((px - st.ML) / st.pw * (n - 1));
  miniCursorAt(hostId, Math.max(0, Math.min(n - 1, i)));
}

function miniCursorAt(hostId, i) {
  const st = MINI[hostId];
  if (!st) return;
  const host = document.getElementById(hostId);
  const g = host.querySelector("#" + hostId + "-cursor");
  if (!g) return;
  st.index = i;
  const x = st.X(st.spec.series[0].pts[i][0]);
  const right = x > st.ML + st.pw * 0.6;
  const tx = right ? x - 8 : x + 8, anchor = right ? "end" : "start";
  const parts = ['<path class="hair" d="M' + x.toFixed(1) + " " + st.MT + " V" + (st.MT + st.ph) + '"/>'];
  st.spec.series.forEach(function (se) {
    const y = st.Y(se.pts[i][1]);
    parts.push('<circle class="knob" cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="4"/>');
  });
  /* value leads, label follows - the reader has the curve and wants the number */
  st.spec.read(i).forEach(function (line, k) {
    parts.push('<text class="' + (k ? "readlabel" : "read") + '" x="' + tx.toFixed(1) + '" y="' +
               (st.MT + 14 + k * 13) + '" text-anchor="' + anchor + '">' + line + "</text>");
  });
  g.innerHTML = parts.join("");
}

/* Whole-decade ticks, labelled with the round value, plus the 2-9 lines
   inside each decade. Callers snap their range to whole decades so the first
   and last tick land on the axis ends. */
function decadeTicks(loDec, hiDec, unit) {
  const ticks = [];
  for (let d = loDec; d <= hiDec; d++) ticks.push({ at: d, label: fmt(Math.pow(10, d), unit) });
  return ticks;
}

function decadeMinors(loDec, hiDec) {
  const at = [];
  for (let d = loDec; d < hiDec; d++) {
    for (let k = 2; k <= 9; k++) at.push(d + Math.log10(k));
  }
  return at;
}

/* ---- self-resonance: the V that every real part traces ---- */

function drawReactPlot(cap, ind) {
  if (!cap && !ind) { miniClear("re-graph"); return; }
  const centre = cap ? cap.srf : ind.srf;
  const lo = Math.floor(Math.log10(centre) - 2.5), hi = Math.ceil(Math.log10(centre) + 2.5);
  const N = 121;
  const series = [];
  const zc = [], zl = [];
  for (let i = 0; i < N; i++) {
    const lx = lo + (hi - lo) * i / (N - 1);
    const w = 2 * Math.PI * Math.pow(10, lx);
    if (cap) {
      const x = w * cap.esl - 1 / (w * cap.c);
      zc.push([lx, Math.log10(Math.max(Math.hypot(cap.esr, x), 1e-6))]);
    }
    if (ind) {
      const sr = ind.dcr, si = w * ind.l, pi = -1 / (w * ind.cp);
      const nr = -si * pi, ni = sr * pi;
      const dr = sr, di = si + pi;
      const den = dr * dr + di * di || 1e-30;
      zl.push([lx, Math.log10(Math.max(Math.hypot((nr * dr + ni * di) / den, (ni * dr - nr * di) / den), 1e-6))]);
    }
  }
  if (cap) series.push({ pts: zc, name: "capacitor" });
  if (ind) series.push({ pts: zl, name: "inductor", alt: series.length > 0 });

  const ys = [];
  series.forEach(function (se) { se.pts.forEach(function (q) { ys.push(q[1]); }); });
  const yLo = Math.floor(Math.min.apply(null, ys)), yHi = Math.ceil(Math.max.apply(null, ys));
  const yTicks = [];
  for (let d = yLo; d <= yHi; d++) yTicks.push({ at: d, label: fmt(Math.pow(10, d), "\u03a9") });

  miniPlot("re-graph", {
    series: series,
    yMin: yLo, yMax: yHi,
    xTicks: decadeTicks(lo, hi, "Hz"),
    xMinor: decadeMinors(lo, hi),
    yTicks: yTicks,
    yUnit: "|Z|",
    marks: [{ at: Math.log10(centre), label: "self-resonance" }],
    label: "Impedance magnitude against frequency, falling to a minimum at self-resonance and rising again beyond it",
    read: function (i) {
      const f = Math.pow(10, series[0].pts[i][0]);
      const vals = series.map(function (se) {
        return se.name + " " + fmt(Math.pow(10, se.pts[i][1]), "\u03a9");
      });
      return [vals.join(", "), "at " + fmt(f, "Hz")];
    }
  });
}

/* ---- fusing current against fault duration ----

   Onderdonk is adiabatic, so the current scales as 1/sqrt(t) and the plot is
   a straight line on log-log. That is the point: halving the duration buys
   only 41 % more current, which a single number never conveys. */

function drawFusePlot(aCmil, ta, kOn, tNow) {
  const N = 61, lo = -2, hi = 2;                  // 10 ms to 100 s, whole decades
  const base = kOn * aCmil * Math.sqrt(Math.log10(1 + (1083 - ta) / (234 + ta)) / 33);
  const pts = [];
  for (let i = 0; i < N; i++) {
    const lx = lo + (hi - lo) * i / (N - 1);
    pts.push([lx, Math.log10(base / Math.sqrt(Math.pow(10, lx)))]);
  }
  const ys = pts.map(function (q) { return q[1]; });
  const yLo = Math.floor(Math.min.apply(null, ys)), yHi = Math.ceil(Math.max.apply(null, ys));
  const yTicks = [];
  for (let d = yLo; d <= yHi; d++) yTicks.push({ at: d, label: fmt(Math.pow(10, d), "A") });
  const marks = [{ at: Math.log10(5), label: "adiabatic model ends" }];
  if (tNow >= Math.pow(10, lo) && tNow <= Math.pow(10, hi)) {
    marks.unshift({ at: Math.log10(tNow), label: "your fault" });
  }
  miniPlot("fu-graph", {
    series: [{ pts: pts, name: "fusing" }],
    yMin: yLo, yMax: yHi,
    xTicks: decadeTicks(lo, hi, "s"),
    xMinor: decadeMinors(lo, hi),
    yTicks: yTicks,
    yUnit: "I",
    marks: marks,
    label: "Fusing current falling as the square root of fault duration, on log axes",
    read: function (i) {
      return [fmt(Math.pow(10, pts[i][1]), "A"), "for a " + fmt(Math.pow(10, pts[i][0]), "s") + " fault"];
    }
  });
}

/* ---- divider error across temperature ----

   Tolerance sets the width of the band at T nominal; TCR opens it out either
   side. Seeing the wedge is what makes the case for matched parts over tight
   parts. No crosshair here: the band is two series wide and the extremes,
   which are the numbers anyone acts on, are already in the results list. */

function drawErrorBand(k, tol1, tol2, tcr1, tcr2, age, tmin, tmax, tnom) {
  const N = 41;
  const hi = [], lo = [], rssHi = [], rssLo = [];
  for (let i = 0; i < N; i++) {
    const T = tmin + (tmax - tmin) * i / (N - 1);
    const dT = Math.abs(T - tnom);
    const d1 = tol1 + Math.abs(tcr1) * 1e-6 * dT + age;
    const d2 = tol2 + Math.abs(tcr2) * 1e-6 * dT + age;
    const wc = (1 - k) * (d1 + d2) * 100;
    const s1 = Math.sqrt(tol1 * tol1 + Math.pow(Math.abs(tcr1) * 1e-6 * dT, 2) + age * age);
    const s2 = Math.sqrt(tol2 * tol2 + Math.pow(Math.abs(tcr2) * 1e-6 * dT, 2) + age * age);
    const rs = (1 - k) * Math.sqrt(s1 * s1 + s2 * s2) * 100;
    hi.push([T, wc]); lo.push([T, -wc]);
    rssHi.push([T, rs]); rssLo.push([T, -rs]);
  }
  const peak = Math.max(hi[0][1], hi[N - 1][1]);
  const step = peak / 2;
  miniPlot("ac-graph", {
    series: [{ pts: hi, name: "worst case" }, { pts: rssHi, name: "RSS", alt: true }],
    band: [hi, lo],
    yMin: -peak * 1.1, yMax: peak * 1.1,
    xTicks: [{ at: tmin, label: tmin.toFixed(0) + " \u00b0C" },
             { at: tnom, label: tnom.toFixed(0) + " \u00b0C" },
             { at: tmax, label: tmax.toFixed(0) + " \u00b0C" }],
    yTicks: [{ at: -step, label: "\u2212" + step.toPrecision(2) }, { at: 0, label: "0" },
             { at: step, label: "+" + step.toPrecision(2) }],
    yUnit: "%",
    label: "Ratio error band across temperature, narrowest at T nominal where only tolerance applies and widening either side as TCR adds to it",
    /* the mirrored halves are drawn as the band, so only the upper edges are
       series; say so rather than leaving the reader to infer symmetry */
    note: "The band is symmetric: the ratio can land the same distance either side of nominal.",
    read: function () { return []; }
  });
}

/* ---------- reactance ---------- */

function calcReact() {
  miniClear("re-graph");
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

  drawReactPlot(
    isFinite(C) && isFinite(Lp) && Lp > 0
      ? { c: C, esl: Lp, esr: isFinite(Rp) && Rp > 0 ? Rp : 1e-3, srf: 1 / (TAU * Math.sqrt(Lp * C)) } : null,
    isFinite(L0) && L0 > 0 && isFinite(epc) && epc > 0
      ? { l: L0, cp: epc, dcr: isFinite(dcr) && dcr > 0 ? dcr : 1e-3, srf: 1 / (TAU * Math.sqrt(L0 * epc)) } : null);

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

/* ---------- component tolerance ----------

   One budget for resistors, capacitors, inductors, oscillators and voltage
   references. Every contribution is a signed pair of fractions, because the
   interesting cases are asymmetric: a Y5V capacitor may fall 82 % and rise
   only 22 %, and DC bias only ever subtracts. */

/* EIA-198 class 2 codes are systematic, so decode them rather than listing a
   handful: first character the low temperature, second the high, third the
   permitted capacitance change over that range. */
const EIA_LOW = { X: -55, Y: -30, Z: 10 };
const EIA_HIGH = { "2": 45, "4": 65, "5": 85, "6": 105, "7": 125, "8": 150, "9": 200 };
const EIA_CHANGE = {
  A: [1, -1], B: [1.5, -1.5], C: [2.2, -2.2], D: [3.3, -3.3], E: [4.7, -4.7],
  F: [7.5, -7.5], P: [10, -10], R: [15, -15], S: [22, -22],
  T: [22, -33], U: [22, -56], V: [22, -82]
};
/* Typical ageing for the dielectric class, in per cent per decade of hours.
   Class 2 ceramics lose capacitance as the crystal structure relaxes; the
   figure is a class typical, not a spec, so it is offered as a default the
   datasheet should replace. */
const EIA_AGEING = { P: 1, R: 1.5, S: 2, T: 3, U: 5, V: 6 };

function decodeEIA(code) {
  const c = String(code || "").trim().toUpperCase();
  if (c === "C0G" || c === "NP0") {
    return { cls: 1, lo: -55, hi: 125, plus: 0, minus: 0, tc: 30, age: 0, name: "C0G / NP0" };
  }
  if (c.length !== 3) return null;
  const lo = EIA_LOW[c[0]], hi = EIA_HIGH[c[1]], ch = EIA_CHANGE[c[2]];
  if (lo === undefined || hi === undefined || !ch) return null;
  return { cls: 2, lo: lo, hi: hi, plus: ch[0], minus: ch[1], tc: 0, age: EIA_AGEING[c[2]] || 2, name: c };
}

/* The five component types, and what each of the shared fields means for it. */
const EC_TYPE = {
  R: { name: "Resistor",          unit: "\u03a9", vlabel: "Nominal value (\u03a9)",  tc: "Temperature coefficient (ppm/\u00b0C)", tcDflt: 100, ageUnit: "ppm/year", ageDflt: 0 },
  C: { name: "Capacitor",         unit: "F",      vlabel: "Nominal value (F)",       tc: "Temperature coefficient (ppm/\u00b0C)", tcDflt: 30,  ageUnit: "%/decade hour", ageDflt: 0 },
  L: { name: "Inductor",          unit: "H",      vlabel: "Nominal value (H)",       tc: "Temperature coefficient (ppm/\u00b0C)", tcDflt: 100, ageUnit: "ppm/year", ageDflt: 0 },
  X: { name: "Crystal",           unit: "Hz",     vlabel: "Nominal frequency (Hz)",  tc: "Frequency stability over range (\u00b1ppm)", tcDflt: 30, ageUnit: "ppm/year", ageDflt: 3 },
  V: { name: "Voltage reference", unit: "V",      vlabel: "Nominal output (V)",      tc: "Temperature coefficient (ppm/\u00b0C)", tcDflt: 25,  ageUnit: "ppm/\u221a1000 h", ageDflt: 50 }
};

/* Show only the fields this component type has, and rename the ones whose
   meaning shifts. Called on every recalculation so the card can never show a
   field that its own maths ignores. */
function ecFields(type) {
  const t = EC_TYPE[type];
  const cap = type === "C", xtal = type === "X", vref = type === "V";
  const show = function (id, on) { const e = document.getElementById(id); if (e) e.hidden = !on; };
  show("ec-f-diel", cap);
  show("ec-f-bias", cap);
  show("ec-f-hyst", vref);
  const diel = cap ? document.getElementById("ec-diel").value : "";
  show("ec-f-code", cap && diel === "other");
  /* a class 2 ceramic's temperature spec is the dielectric code, not a slope */
  const usesTc = !(cap && diel !== "C0G");
  show("ec-f-tc", usesTc);
  document.getElementById("ec-vallabel").innerHTML = t.vlabel;
  document.getElementById("ec-tclabel").innerHTML = t.tc;
  document.getElementById("ec-tollabel").innerHTML = xtal ? "Initial tolerance (\u00b1ppm at 25 \u00b0C)" : "Initial tolerance (%)";
  document.getElementById("ec-agelabel").innerHTML = "Ageing (" + t.ageUnit + ")";
  document.getElementById("ec-lifelabel").innerHTML = cap ? "Service life (hours)" : "Service life (years)";
  document.getElementById("ec-tol").placeholder = xtal ? "20" : "1";
  document.getElementById("ec-tc").placeholder = String(t.tcDflt);
  document.getElementById("ec-age").placeholder = String(t.ageDflt);
  document.getElementById("ec-life").placeholder = cap ? "50000" : "10";
  return t;
}

function calcTolerance() {
  const type = document.getElementById("ec-type").value;
  const t = ecFields(type);
  const cap = type === "C", xtal = type === "X", vref = type === "V";
  const num = function (id, dflt) { const v = val(id); return isFinite(v) ? v : dflt; };

  const nominal = val("ec-val");
  const tmin = num("ec-tmin", -40), tmax = num("ec-tmax", 85), tnom = num("ec-tnom", 25);
  if (tmax < tmin) { render("ec-out", [["", "T max must be at or above T min.", "err"]]); return; }
  const dT = Math.max(Math.abs(tmax - tnom), Math.abs(tmin - tnom));

  const diel = cap ? decodeEIA(document.getElementById("ec-diel").value === "other"
                                 ? document.getElementById("ec-code").value
                                 : document.getElementById("ec-diel").value) : null;
  if (cap && document.getElementById("ec-diel").value === "other" && !diel) {
    render("ec-out", [["", "That is not an EIA class 2 code. The first character is the low temperature (X, Y, Z), "
                          + "the second the high (2, 4\u20139) and the third the permitted change (P, R, S, T, U, V) \u2014 X7R, Y5V, X6T.", "err"]]);
    return;
  }

  /* every contribution as [label, +fraction, -fraction] */
  const parts = [];
  const tol = num("ec-tol", xtal ? 20 : 1);
  if (xtal) parts.push(["Initial tolerance at 25 \u00b0C", tol * 1e-6, tol * 1e-6]);
  else parts.push(["Initial tolerance", tol / 100, tol / 100]);

  if (cap && diel && diel.cls === 2) {
    parts.push(["Temperature, " + diel.name + " over " + diel.lo + " to +" + diel.hi + " \u00b0C",
                diel.plus / 100, -diel.minus / 100]);
  } else if (xtal) {
    const st = num("ec-tc", t.tcDflt);
    parts.push(["Frequency stability over temperature", st * 1e-6, st * 1e-6]);
  } else {
    const tc = num("ec-tc", cap ? 30 : t.tcDflt);
    parts.push(["Temperature, " + Math.abs(tc) + " ppm/\u00b0C over \u0394T " + dT.toFixed(0) + " \u00b0C",
                Math.abs(tc) * 1e-6 * dT, Math.abs(tc) * 1e-6 * dT]);
  }

  const life = num("ec-life", cap ? 50000 : 10);
  const age = num("ec-age", cap && diel ? diel.age : t.ageDflt);
  if (age > 0 && life > 0) {
    if (cap) {
      /* class 2 ceramics lose capacitance by a fixed percentage per decade of
         hours, referred to the 1000 h point the datasheet measures at */
      const decades = Math.max(0, Math.log10(life / 1000));
      parts.push(["Ageing, " + age + " %/decade over " + fmt(life, "h") + " (" + decades.toFixed(2) + " decades past 1000 h)",
                  0, age * decades / 100]);
    } else if (vref) {
      /* reference drift is a random walk, so it accumulates as the square root
         of time rather than linearly */
      const kh = Math.sqrt(life * 8760 / 1000);
      parts.push(["Long-term drift, " + age + " ppm/\u221a1000 h over " + life + " years",
                  age * kh * 1e-6, age * kh * 1e-6]);
    } else {
      parts.push(["Ageing, " + age + " ppm/year over " + life + " years", age * life * 1e-6, age * life * 1e-6]);
    }
  }

  if (cap) {
    const bias = num("ec-bias", 0);
    if (bias > 0) parts.push(["DC bias at the working voltage", 0, bias / 100]);
  }
  if (vref) {
    const hyst = num("ec-hyst", 0);
    if (hyst > 0) parts.push(["Thermal hysteresis", hyst * 1e-6, hyst * 1e-6]);
  }

  let wcP = 0, wcM = 0, ssP = 0, ssM = 0;
  const rows = [];
  parts.forEach(function (q) {
    wcP += q[1]; wcM += q[2];
    ssP += q[1] * q[1]; ssM += q[2] * q[2];
    rows.push([q[0], (q[1] === q[2] ? "\u00b1" + pct(q[1]) : "+" + pct(q[1]) + " / \u2212" + pct(q[2]))]);
  });
  const rssP = Math.sqrt(ssP), rssM = Math.sqrt(ssM);

  rows.push(["Worst case", band(wcP, wcM)]);
  rows.push(["RSS", band(rssP, rssM)]);

  if (isFinite(nominal) && nominal > 0) {
    rows.unshift(["Nominal", fmt(nominal, t.unit)]);
    if (xtal) {
      /* Four significant figures cannot resolve tens of ppm on a megahertz
         part - it would print "16 MHz to 16 MHz" - so a crystal gets whole
         hertz instead of a formatted range. */
      const win = function (m, pl) {
        return Math.round(nominal * (1 - m)).toLocaleString("en-GB") + " to " +
               Math.round(nominal * (1 + pl)).toLocaleString("en-GB") + " Hz";
      };
      rows.push(["Worst-case window", win(wcM, wcP)]);
      rows.push(["RSS window", win(rssM, rssP)]);
    } else {
      /* Contributions are summed, so a stack of large ones can subtract more
         than the whole part. Clamping and saying so beats printing a negative
         capacitance as though it meant something. */
      const gone = wcM >= 1;
      rows.push(["Worst-case range", (gone ? "0" : fmt(nominal * (1 - wcM), t.unit)) +
                 " to " + fmt(nominal * (1 + wcP), t.unit)]);
      rows.push(["RSS range", fmt(Math.max(0, nominal * (1 - rssM)), t.unit) + " to " +
                 fmt(nominal * (1 + rssP), t.unit)]);
      if (gone) {
        rows.push(["", "The negative contributions total more than the whole value, so worst case leaves nothing. " +
                   "Stacking every limit this far is past the point of being useful — work from the RSS figure, or from " +
                   "the manufacturer’s own curves for the conditions you actually have.", "warn"]);
      }
    }
  }

  if (cap && diel && diel.cls === 2) {
    const outside = tmin < diel.lo || tmax > diel.hi;
    rows.push(["", "The " + diel.name + " figure is a bound over the dielectric&rsquo;s whole " + diel.lo +
               " to +" + diel.hi + " \u00b0C range. The curve is not linear, so a narrower operating range sees less than this "
               + "but the spec cannot be scaled down &mdash; use the manufacturer&rsquo;s curve if you need the narrower number.",
               "warn"]);
    if (outside) {
      rows.push(["", "Your " + tmin + " to +" + tmax + " \u00b0C range goes outside what " + diel.name +
                 " is rated for, so the part is unspecified at the extremes.", "err"]);
    }
  }
  if (cap && num("ec-bias", 0) === 0 && diel && diel.cls === 2) {
    rows.push(["", "No DC bias loss entered. On a class 2 ceramic this is usually the largest term of all &mdash; a small "
               + "case size at its rated voltage can lose more than half its capacitance &mdash; so a budget without it is optimistic.", "warn"]);
  }
  render("ec-out", rows);
}

function pct(x) { return (x * 100).toPrecision(3) + " %"; }
function band(plus, minus) {
  return (Math.abs(plus - minus) < 1e-12 ? "\u00b1" + pct(plus) : "+" + pct(plus) + " / \u2212" + pct(minus)) +
         " (" + (plus * 1e6).toFixed(0) + " / " + (minus * 1e6).toFixed(0) + " ppm)";
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
  miniClear("ac-graph");
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

  drawErrorBand(k, tol1, tol2, tcr1, tcr2, age, tmin, tmax, tnom);

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
  drawTrace(document.getElementById("tw-layer").value);
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

  /* The routing question is usually "can this go on an inner layer instead",
     so give the width the other layer would need for the same current rather
     than making the reader flip the selector and lose what they typed. */
  const isExt = k === 0.048;
  const iForOther = isFinite(iVal) && iVal > 0 ? iVal : achievable;
  if (iForOther > 0) {
    const wOther = (ipcArea(iForOther, dT, isExt ? 0.024 : 0.048) / (tMM / MIL)) * MIL;
    rows.push(["Same current on an " + (isExt ? "internal" : "external") + " layer",
               (wOther / MIL).toFixed(1) + " mil (" + wOther.toPrecision(3) + " mm), " +
               (wOther / wMM).toFixed(2) + " times this width"]);
  }

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
  drawVia(valDim("via-stub") > 0);
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
    /* the current is what the net carries, so with n vias it splits between
       them - say so, because "At 3 A" alone reads as 3 A per via */
    rows.push(["At " + fmt(iVia, "A") + (nVia > 1 ? " shared across the " + nVia : ""),
               fmt(iVia * rEff, "V") + " drop, " + fmt(iVia * iVia * rEff, "W") + " dissipated"]);
  }
  if (isFinite(stub) && stub > 0) {
    rows.push(["Stub quarter-wave null", fmt(299792458 / (4 * (stub / 1000) * Math.sqrt(er)), "Hz") +
               " — keep the signal's usable bandwidth well below this"]);
  }
  const pad = valDim("via-pad"), anti = valDim("via-anti");
  let cPF = NaN;                       // needed again for the edge-degradation row
  if (isFinite(pad) && isFinite(anti)) {
    if (anti > pad && pad > 0) {
      cPF = 1.41 * er * (h / 25.4) * (pad / 25.4) / ((anti - pad) / 25.4);
      rows.push(["Capacitance", cPF.toPrecision(3) + " pF"]);
      const cF = cPF * 1e-12, lH = lNH * 1e-9;
      rows.push(["Lumped √(L/C)", Math.sqrt(lH / cF).toFixed(1) + " Ω — compare with your trace impedance; below it the via looks capacitive, above it inductive"]);
      rows.push(["Lumped-model limit", fmt(1 / (2 * Math.PI * Math.sqrt(lH * cF)), "Hz") +
                 " — treat the via as a discontinuity above roughly a third of this"]);
    } else {
      rows.push(["", "Antipad must be larger than pad for the capacitance estimate.", "warn"]);
    }
  }

  /* What the via does to a passing edge. Inductance is the term that usually
     matters: a series inductance looks like pi*L/tr to an edge of that rise
     time, so a 1 nH via is well under an ohm at 1 ns and several ohms at
     100 ps. Capacitance slows the edge by roughly 2.2*C*Z0/2. */
  const tr = val("via-tr");
  const z0line = val("via-z0");
  if (isFinite(tr) && tr > 0) {
    const xl = Math.PI * lNH * 1e-9 / tr;
    rows.push(["Reactance to a " + fmt(tr, "s") + " edge", fmt(xl, "Ω") +
               (isFinite(z0line) && z0line > 0
                  ? ", " + (xl / z0line * 100).toFixed(0) + " % of a " + fmt(z0line, "Ω") + " line"
                  : " — give a trace impedance to see it as a fraction of the line")]);
    if (isFinite(cPF) && cPF > 0 && isFinite(z0line) && z0line > 0) {
      const tdeg = 2.2 * cPF * 1e-12 * z0line / 2;
      rows.push(["Edge slowed by", fmt(tdeg, "s") + ", " + (tdeg / tr * 100).toFixed(0) +
                 " % of the rise time"]);
    }
  }
  render("via-out", rows);
}

/* The other published fusing model, as used by KiCad: an adiabatic energy
   balance that melts the copper outright. It carries the latent heat of fusion,
   which Onderdonk's empirical fit does not, but averages the resistivity over
   the temperature range where Onderdonk integrates it properly. Neither is
   strictly better, so the card reports both and the spread between them. */
const CU_DENSITY = 8940;        // kg/m3
const CU_CP = 385;              // J/(kg K)
const CU_LATENT = 205350;       // J/kg, heat of fusion
const CU_RHO20 = 1.72e-8;       // ohm m at 20 C
const CU_ALPHA = 0.00393;       // per K

function fuseEnergyCurrent(areaM2, ta, tm, seconds) {
  if (!(areaM2 > 0) || !(seconds > 0) || !(tm > ta)) return NaN;
  const volumic = CU_DENSITY * (CU_CP * (tm - ta) + CU_LATENT);   // J/m3
  const rhoA = (1 + CU_ALPHA * (ta - 20)) * CU_RHO20;
  const rhoM = (1 + CU_ALPHA * (tm - 20)) * CU_RHO20;
  const rho = (rhoA + rhoM) / 2;
  return areaM2 * Math.sqrt(volumic / (rho * seconds));
}

/* Onderdonk: 33*(I/A_cmil)^2 * t = log10(1 + (Tm-Ta)/(234+Ta)), Tm = 1083 C */
function calcFuse() {
  miniClear("fu-graph");
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
  drawFusePlot(aCmil, ta, kOn, t);
  const iEnergy = kOn * fuseEnergyCurrent(w * tMM * 1e-6, ta, 1084, t);
  render("fu-out", [
    ["Cross-section", aMil2.toFixed(1) + " mil&sup2; (" + (aMil2 * MIL * MIL).toPrecision(3) + " mm&sup2;)"],
    ["Fusing current for " + fmt(t, "s"), fmt(iFuse, "A") + " (Onderdonk)"],
    ["The other published model", fmt(iEnergy, "A") + " (energy balance with the latent heat of fusion), " +
     (isFinite(iEnergy) && iFuse > 0
        ? ((iEnergy / iFuse - 1) * 100).toFixed(0) + " % from Onderdonk"
        : "not computable here")],
    ["", "Onderdonk integrates the resistivity across the temperature rise but ignores the energy of melting; " +
     "the energy balance includes melting but uses a mean resistivity. The spread between them is the honest " +
     "width of a fusing estimate - design well below the lower of the two.", ""],
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
  drawZ(struct);
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

  if (isFinite(f) && f > 0) {
    const tand = numOr("z-tand", 0.02, 0);
    const rough = numOr("z-rough", 0.4, 0);
    if (isFinite(tand) && isFinite(rough)) {
      const ls = tlineLoss(f, z0, w, er, eeff, tand, rough);
      rows.push(["Skin depth at " + fmt(f, "Hz"), (ls.delta * 1e6).toPrecision(3) +
                 " \u00b5m, surface resistivity " + fmt(ls.rs, "\u03a9") + "/square"]);
      rows.push(["Conductor loss", ls.ac.toPrecision(3) + " dB/m (" + (ls.ac * 0.0254).toPrecision(3) + " dB/in)" +
                 (ls.kr > 1.01 ? ", roughness costing " + ((ls.kr - 1) * 100).toFixed(0) + " %" : "")]);
      rows.push(["Dielectric loss", ls.ad.toPrecision(3) + " dB/m (" + (ls.ad * 0.0254).toPrecision(3) + " dB/in)"]);
      rows.push(["Total", ls.total.toPrecision(3) + " dB/m \u2014 " +
                 (1 / ls.total).toPrecision(3) + " m for 1 dB, " + (3 / ls.total).toPrecision(3) + " m for 3 dB"]);
      rows.push(["", "Conductor loss here is the wide-strip approximation, which ignores current crowding at the " +
                 "trace edges and so reads low on a narrow line \u2014 treat the total as a floor. Roughness uses the " +
                 "Hammerstad correction; ask the fabricator for the foil class, because standard foil and VLP differ " +
                 "by several times at these frequencies.", ""]);
    }
  }
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

/* ---------- attenuator pads ----------

   The general forms take a source and a load impedance separately and reduce
   to the familiar symmetric expressions when they are equal, which is one of
   the tests. L here is the POWER ratio 10^(A/10), not the voltage ratio -
   mixing the two up is the classic way to get these formulas wrong. */

function padDesign(topo, a, zin, zout) {
  const L = Math.pow(10, a / 10);            // power ratio
  const A = (L + 1) / (L - 1);
  if (topo === "pi") {
    const ser = ((L - 1) / 2) * Math.sqrt(zin * zout / L);
    return { ser: ser,
             sh1: 1 / (A / zin - 1 / ser),
             sh2: 1 / (A / zout - 1 / ser) };
  }
  if (topo === "t") {
    const sh = 2 * Math.sqrt(L * zin * zout) / (L - 1);
    return { sh: sh, se1: zin * A - sh, se2: zout * A - sh };
  }
  if (topo === "bridge") {
    const K = Math.pow(10, a / 20);          // voltage ratio for this one
    return { arm: zin, bridge: zin * (K - 1), sh: zin / (K - 1) };
  }
  if (topo === "split") {
    return { arm: zin / 3, term: zin };
  }
  /* L pad: series on the high side, shunt across the low side */
  const hi = Math.max(zin, zout), lo = Math.min(zin, zout);
  return { hiSide: hi, loSide: lo,
           ser: hi * Math.sqrt(1 - lo / hi),
           sh: lo / Math.sqrt(1 - lo / hi) };
}

/* The minimum attenuation any resistive pad can give between two impedances.
   Equivalent to 20*log10(sqrt(r) + sqrt(r-1)), which is how the L pad's limit
   is usually written - the same number either way. */
function padMinLoss(zin, zout) {
  const r = Math.max(zin, zout) / Math.min(zin, zout);
  if (!(r > 1)) return 0;
  return 10 * Math.log10(2 * r - 1 + 2 * Math.sqrt(r * (r - 1)));
}

/* Branch list for a topology, as [nodeA, nodeB, ohms]. Node 0 is ground, 1 the
   input, 2 the output, 3 an internal node. */
function padBranches(topo, d) {
  if (topo === "pi") return [[1, 0, d.sh1], [1, 2, d.ser], [2, 0, d.sh2]];
  if (topo === "t") return [[1, 3, d.se1], [3, 0, d.sh], [3, 2, d.se2]];
  if (topo === "bridge") return [[1, 3, d.arm], [3, 2, d.arm], [1, 2, d.bridge], [3, 0, d.sh]];
  /* the third arm feeds the third port, which is terminated in z0; arm plus
     termination in series to ground is the same thing seen from the junction */
  if (topo === "split") return [[1, 3, d.arm], [3, 2, d.arm], [3, 0, d.arm + d.term]];
  return [[1, 2, d.ser], [2, 0, d.sh]];
}

/* Transducer loss of a resistive network driven from zin and loaded by zout:
   available power from the source over the power actually delivered. Solving
   the node equations rather than using a per-topology formula means the same
   routine covers the bridged T and the splitter, and stays correct when the
   two impedances differ. */
function padLoss(topo, d, zin, zout) {
  const N = 3;                               // nodes 1..3
  const G = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  const I = [0, 0, 0];
  const add = function (x, y, r) {
    if (!(r > 0) || !isFinite(r)) return;
    const g = 1 / r;
    if (x) G[x - 1][x - 1] += g;
    if (y) G[y - 1][y - 1] += g;
    if (x && y) { G[x - 1][y - 1] -= g; G[y - 1][x - 1] -= g; }
  };
  padBranches(topo, d).forEach(function (br) { add(br[0], br[1], br[2]); });
  add(1, 0, zin);                            // source resistance
  add(2, 0, zout);                           // load
  I[0] = 1 / zin;                            // 1 V source behind zin

  /* Gaussian elimination on a 3x3 - small enough to be exact and obvious */
  const M = [[G[0][0], G[0][1], G[0][2], I[0]],
             [G[1][0], G[1][1], G[1][2], I[1]],
             [G[2][0], G[2][1], G[2][2], I[2]]];
  for (let c = 0; c < N; c++) {
    let piv = c;
    for (let r = c + 1; r < N; r++) if (Math.abs(M[r][c]) > Math.abs(M[piv][c])) piv = r;
    if (Math.abs(M[piv][c]) < 1e-15) continue;
    const t = M[c]; M[c] = M[piv]; M[piv] = t;
    for (let r = 0; r < N; r++) {
      if (r === c) continue;
      const f = M[r][c] / M[c][c];
      for (let k = c; k <= N; k++) M[r][k] -= f * M[c][k];
    }
  }
  const v = [0, 0, 0];
  for (let c = 0; c < N; c++) v[c] = Math.abs(M[c][c]) < 1e-15 ? 0 : M[c][N] / M[c][c];
  const vout = v[1];
  const pLoad = vout * vout / zout;
  const pAvail = 1 / (4 * zin);              // from a 1 V source behind zin
  if (!(pLoad > 0)) return Infinity;
  return 10 * Math.log10(pAvail / pLoad);
}

function calcPad() {
  const topo = document.getElementById("pad-topo").value;
  const split = topo === "split", bridge = topo === "bridge";
  const zin = numOr("pad-zin", 50, 1e-9);
  let zout = numOr("pad-zout", 50, 1e-9);
  /* Two topologies have no free attenuation: a splitter is always 6 dB, and a
     matched L pad delivers exactly the minimum loss its impedance ratio allows.
     Reading the attenuation box for those would be pretending it matters. */
  const a = split ? 20 * Math.log10(2)
          : topo === "l" ? padMinLoss(zin, zout)
          : val("pad-a");
  drawPad(topo);
  if (!isFinite(zin) || !isFinite(zout)) { render("pad-out", []); return; }
  /* these two are symmetric by construction */
  if (split || bridge) zout = zin;
  if (!isFinite(a)) { render("pad-out", []); return; }
  if (topo === "l" && !(a > 0)) {
    render("pad-out", [["", "An L pad matches two <em>different</em> impedances. With both the same there is nothing to match, so use a PI or T pad.", "err"]]);
    return;
  }
  if (!split && topo !== "l" && a <= 0) {
    render("pad-out", [["", "Attenuation must be greater than 0 dB.", "err"]]); return;
  }

  const rows = [];
  const aMin = padMinLoss(zin, zout);
  if (aMin > 0 && a < aMin - 1e-9 && topo !== "l" && !split) {
    render("pad-out", [["Minimum attenuation", aMin.toFixed(2) + " dB between " + fmt(zin, "\u03a9") +
                        " and " + fmt(zout, "\u03a9")],
                       ["", "No resistive pad can match both ends at " + a + " dB. Ask for at least " +
                        aMin.toFixed(2) + " dB, or use a transformer.", "err"]]);
    return;
  }

  const d = padDesign(topo, a, zin, zout);
  const R = function (x) { return fmt(x, "\u03a9"); };
  if (topo === "pi") {
    rows.push(["Series", R(d.ser)]);
    rows.push(["Shunt, source side", R(d.sh1)]);
    rows.push(["Shunt, load side", R(d.sh2)]);
  } else if (topo === "t") {
    rows.push(["Series, source side", R(d.se1)]);
    rows.push(["Shunt", R(d.sh)]);
    rows.push(["Series, load side", R(d.se2)]);
  } else if (topo === "bridge") {
    rows.push(["Series arms", R(d.arm) + " each, equal to Z\u2080"]);
    rows.push(["Bridging", R(d.bridge)]);
    rows.push(["Shunt", R(d.sh)]);
  } else if (topo === "split") {
    rows.push(["Each arm", R(d.arm)]);
    rows.push(["Attenuation", a.toFixed(2) + " dB per output, fixed by the topology"]);
    rows.push(["Isolation between outputs", "6.0 dB \u2014 a resistive splitter barely isolates its ports; " +
               "a Wilkinson gets you 20 dB or more, at the cost of being narrowband"]);
  } else {
    rows.push(["Series, on the " + R(d.hiSide) + " side", R(d.ser)]);
    rows.push(["Shunt, across the " + R(d.loSide) + " side", R(d.sh)]);
    rows.push(["Attenuation", a.toFixed(2) + " dB &mdash; fixed by the impedance ratio, not chosen"]);
    rows.push(["", "A matched L pad has no free parameter: one geometry matches these two impedances and it gives exactly this loss. For more attenuation, follow it with a PI or T pad in the matched system.", ""]);
  }

  if (aMin > 0 && topo !== "l") {
    rows.push(["Minimum for these impedances", aMin.toFixed(2) + " dB" +
               (a < aMin + 0.01 ? " \u2014 you are at it, so the pad is a pure matching network" : "")]);
  }

  /* what stock parts actually deliver, by transducer loss against the real
     source and load rather than by a symmetric shortcut */
  const series = gSeries();
  const vals = seriesValues(series, -1, 7);
  const snapAll = function (o) {
    const out = {};
    for (const k in o) out[k] = snap(vals, o[k]);
    return out;
  };
  const dn = snapAll(d);
  const got = padLoss(topo, dn, zin, zout);
  const parts = [];
  for (const k in dn) parts.push(R(dn[k]));
  rows.push(["Nearest " + series, parts.join(" \u00b7 ")]);
  rows.push(["Those parts give", got.toFixed(2) + " dB, against " + a.toFixed(2) + " asked for"]);
  render("pad-out", rows);
}

/* ---------- transmission-line loss ----------

   Z0 and delay say where a wave goes; loss says whether it arrives, and above
   a gigahertz it is usually the number that decides the design.

   Conductor loss uses the wide-strip approximation ac = Rs/(Z0*w). It ignores
   current crowding at the trace edges, so it is a LOWER bound - a real narrow
   microstrip loses more. Roughness is the Hammerstad-Jensen correction, and it
   is not a small effect: standard foil at a few GHz can double the conductor
   loss, which is exactly the factor that makes a link budget wrong.

   Dielectric loss is the usual closed form, and the same expression covers
   stripline because eeff collapses to er there. */

const MU0 = 4e-7 * Math.PI;
const RHO_CU = 1.72e-8;

function skinDepth(f, rho) { return Math.sqrt((rho || RHO_CU) / (Math.PI * f * MU0)); }

function tlineLoss(f, z0, wMM, er, eeff, tand, roughUM) {
  const delta = skinDepth(f, RHO_CU);
  const rs = RHO_CU / delta;                       // surface resistivity, ohms/square
  const kr = roughUM > 0
      ? 1 + (2 / Math.PI) * Math.atan(1.4 * Math.pow((roughUM * 1e-6) / delta, 2))
      : 1;
  const ac = 8.686 * rs * kr / (z0 * (wMM / 1000));            // dB/m
  const lambda0 = 299792458 / f;
  const ad = tand > 0
      ? 27.3 * (er * (eeff - 1)) / (Math.sqrt(eeff) * (er - 1)) * tand / lambda0
      : 0;                                                      // dB/m
  return { delta: delta, rs: rs, kr: kr, ac: ac, ad: ad, total: ac + ad };
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
  drawDiff(document.getElementById("dp-struct").value);
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

/* ---------- battery ----------

   The chemistry sets the three cell voltages, which then drive everything
   else. They are written into the fields rather than held privately, so they
   are visible, and typing over one makes it yours: pick Custom, or just
   overwrite a number.

   `full` is the resting voltage of a fully charged cell, not the constant-
   voltage charge setpoint - they differ on lead-acid, and it is the resting
   figure the discharge curve starts from. `chg` is the ordinary charge rate
   for the chemistry; a real cell's limit is on its datasheet. Maximum
   discharge is deliberately not tabulated: within one chemistry it ranges
   over two orders of magnitude, so it comes from the cell's own C rating. */
const CHEM = {
  lipo:    { name: "LiPo",           nom: 3.7, full: 4.20, min: 3.00, cv: 4.20, chg: 1,   shape: "slope" },
  lihv:    { name: "LiHV",           nom: 3.8, full: 4.35, min: 3.00, cv: 4.35, chg: 1,   shape: "slope" },
  liion:   { name: "Li-ion",         nom: 3.6, full: 4.20, min: 2.50, cv: 4.20, chg: 0.5, shape: "slope" },
  lifepo4: { name: "LiFePO4 / LiFe", nom: 3.2, full: 3.40, min: 2.50, cv: 3.65, chg: 1,   shape: "flat" },
  nimh:    { name: "NiMH",           nom: 1.2, full: 1.40, min: 1.00, cv: 0,    chg: 0.5, shape: "flat" },
  lead:    { name: "Lead-acid",      nom: 2.0, full: 2.13, min: 1.75, cv: 2.40, chg: 0.2, shape: "slope" }
};

/* Normalised discharge shapes: fraction of the full-to-empty voltage span
   against fraction of capacity drawn. Indicative of the chemistry's character
   - a lithium-iron plateau against a sloping lithium-polymer - not any
   particular cell. */
const DISCHARGE_SHAPE = {
  slope: [[0, 1], [0.1, 0.88], [0.3, 0.74], [0.5, 0.62], [0.7, 0.50], [0.85, 0.38], [0.95, 0.22], [1, 0]],
  flat:  [[0, 1], [0.05, 0.80], [0.15, 0.72], [0.5, 0.66], [0.85, 0.58], [0.95, 0.40], [1, 0]]
};

function shapeAt(knots, x) {
  for (let i = 1; i < knots.length; i++) {
    if (x <= knots[i][0]) {
      const a = knots[i - 1], b = knots[i];
      const f = (x - a[0]) / ((b[0] - a[0]) || 1);
      return a[1] + f * (b[1] - a[1]);
    }
  }
  return 0;
}

/* Fill a field from the chemistry, leaving anything the user typed alone. */
function chemFill(id, v) {
  const el = document.getElementById(id);
  if (!el) return;
  if (el.value.trim() === "" || el.classList.contains("computed")) setComputed(id, v);
}

function drawBatteryCurve(vfull, vnom, vmin, S, shape, usable) {
  const span = vfull - vmin;
  if (!(span > 0)) { miniClear("bat-graph"); return; }
  const knots = DISCHARGE_SHAPE[shape] || DISCHARGE_SHAPE.slope;
  /* Bend the shape so it passes through the nominal voltage at half capacity.
     That ties the curve to the three numbers on the card, so a custom
     chemistry gets a curve that honours its own figures instead of borrowing
     someone else's. */
  const target = Math.min(0.95, Math.max(0.05, (vnom - vmin) / span));
  const mid = shapeAt(knots, 0.5);
  let pw = Math.log(target) / Math.log(mid);
  const clamped = !isFinite(pw) || pw < 0.4 || pw > 3;
  pw = clamped ? 1 : pw;

  const N = 81, pts = [];
  for (let i = 0; i < N; i++) {
    const x = i / (N - 1);
    pts.push([x * 100, (vmin + span * Math.pow(Math.max(shapeAt(knots, x), 0), pw)) * S]);
  }
  miniPlot("bat-graph", {
    series: [{ pts: pts, name: "pack" }],
    yMin: vmin * S - span * S * 0.08,
    yMax: vfull * S + span * S * 0.08,
    xTicks: [0, 20, 40, 60, 80, 100].map(function (v) { return { at: v, label: v + " %" }; }),
    yTicks: [vmin, vnom, vfull].map(function (v) { return { at: v * S, label: (v * S).toPrecision(3) }; }),
    yUnit: "V",
    hlines: [{ at: vmin * S, label: "minimum" }],
    marks: usable < 100 ? [{ at: usable, label: usable + " % used" }] : [],
    label: "Typical discharge curve: pack voltage falling as capacity is drawn, from full to the minimum recommended cell voltage",
    note: "Indicative of the chemistry's shape, bent to pass through your nominal voltage at half capacity" +
          (clamped ? " &mdash; except that these three voltages give no sensible curvature, so a straight blend is drawn instead" : "") +
          ". It is not your cell's measured curve, and load and temperature both move it.",
    read: function (i) {
      return [pts[i][1].toPrecision(4) + " V", "at " + pts[i][0].toFixed(0) + " % drawn"];
    }
  });
}

function calcBattery() {
  miniClear("bat-graph");
  const chem = CHEM[document.getElementById("bat-chem").value];
  if (chem) {
    chemFill("bat-vfull", chem.full);
    chemFill("bat-v", chem.nom);
    chemFill("bat-vmin", chem.min);
  }
  const mah = val("bat-mah");
  const vc = numOr("bat-v", 3.7, 0.1);
  const vfull = numOr("bat-vfull", 4.2, 0.1);
  const vmin = numOr("bat-vmin", 3.0, 0.01);
  const S = Math.max(1, Math.round(numOr("bat-s", 1, 1) || 1));
  const P = Math.max(1, Math.round(numOr("bat-p", 1, 1) || 1));
  const load = val("bat-load");
  const usable = numOr("bat-usable", 80, 1, 100);
  const crate = val("bat-crate");

  /* The two halves of this card are independent: the voltage side needs a
     chemistry and a series count, the current side needs a capacity. Answer
     whichever is available rather than making one wait for the other. */
  const haveV = isFinite(vc) && isFinite(vfull) && isFinite(vmin);
  const haveAh = isFinite(mah) && mah > 0;
  if (!haveV && !haveAh) { render("bat-out", []); return; }

  const packV = vc * S;
  const packAh = mah / 1000 * P;
  const rows = [];

  if (haveV && haveAh) {
    const wh = packV * packAh;
    rows.push(["Pack", S + "S" + P + "P at " + fmt(packV, "V") + " nominal" + (chem ? ", " + chem.name : "")]);
    rows.push(["Capacity", packAh.toPrecision(4) + " Ah"]);
    rows.push(["Energy", wh.toPrecision(4) + " Wh (" + (wh * usable / 100).toPrecision(4) +
               " Wh usable at " + usable + " %)"]);
  } else if (haveV) {
    rows.push(["Pack", S + "S at " + fmt(packV, "V") + " nominal" + (chem ? ", " + chem.name : "")]);
  } else {
    rows.push(["Capacity", packAh.toPrecision(4) + " Ah (" + P + "P)"]);
  }

  if (haveV) {
    if (vmin >= vfull) {
      rows.push(["", "The minimum cell voltage is not below the full voltage, so there is nothing to discharge.", "err"]);
      render("bat-out", rows);
      return;
    }
    rows.push(["Charge to", (vfull * S).toPrecision(4) + " V pack (" + vfull + " V per cell)" +
               (chem && chem.cv && chem.cv !== chem.full
                  ? " &mdash; hold at " + (chem.cv * S).toPrecision(4) + " V while charging, " + chem.cv + " V per cell"
                  : "")]);
    rows.push(["Discharge no lower than", (vmin * S).toPrecision(4) + " V pack (" + vmin + " V per cell)"]);
    rows.push(["Working range", (vmin * S).toPrecision(4) + " to " + (vfull * S).toPrecision(4) + " V, " +
               ((vfull - vmin) * S).toPrecision(3) + " V of swing"]);
  }

  if (haveAh) {
    if (chem && chem.chg) {
      rows.push(["Typical charge current", fmt(chem.chg * packAh, "A") + " at " + chem.chg +
                 " C, the ordinary rate for " + chem.name + " &mdash; the cell&rsquo;s datasheet overrides this"]);
    }
    if (isFinite(crate) && crate > 0) {
      rows.push(["Maximum continuous discharge", fmt(crate * packAh, "A") + " at the " + crate + " C rating you gave"]);
    }
  }

  if (haveAh && isFinite(load) && load > 0) {
    const watts = document.getElementById("bat-loadunit").value === "W";
    /* a load in watts needs a pack voltage; without one, say so rather than
       silently using a default */
    if (watts && !haveV) {
      rows.push(["", "A load in watts needs a pack voltage &mdash; give a chemistry, or the cell voltages.", ""]);
    } else {
      const amps = watts ? load / packV : load;
      const hours = packAh * usable / 100 / amps;
      rows.push(["Load", fmt(amps, "A") + (haveV ? " at " + fmt(watts ? load : load * packV, "W") : "")]);
      rows.push(["C-rate", (amps / packAh).toPrecision(3) + " C"]);
      if (isFinite(crate) && crate > 0) {
        const head = crate * packAh / amps;
        rows.push(["Against the rating", head >= 1
                     ? "within it, " + (head >= 2 ? head.toPrecision(2) + "\u00d7 headroom"
                                                  : ((head - 1) * 100).toFixed(0) + " % headroom")
                     : "over it by " + ((1 / head - 1) * 100).toFixed(0) + " % &mdash; the pack cannot supply this continuously",
                   head >= 1 ? "good" : "warn"]);
      }
      rows.push(["Runtime", hours >= 1 ? hours.toPrecision(3) + " h (" + (hours * 60).toPrecision(3) + " min)"
                                       : (hours * 60).toPrecision(3) + " min"]);
    }
  }

  render("bat-out", rows);
  if (haveV) drawBatteryCurve(vfull, vc, vmin, S, chem ? chem.shape : "slope", usable);
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

/* One dialog, refilled on each open, so the page carries a single copy of
   the chrome rather than one per card. <dialog> gives the modal behaviour,
   the backdrop and Escape-to-close for free. */
function showHelp(help) {
  let dlg = document.getElementById("helpdlg");
  if (!dlg) {
    dlg = document.createElement("dialog");
    dlg.id = "helpdlg";
    dlg.className = "help";
    dlg.setAttribute("aria-labelledby", "helpdlg-title");
    dlg.innerHTML = '<div class="help-head"><h3 id="helpdlg-title"></h3>' +
                    '<button type="button" data-close>Close</button></div>' +
                    '<div class="help-body"></div>';
    dlg.querySelector("[data-close]").addEventListener("click", function () { dlg.close(); });
    /* clicking the backdrop closes it; clicks inside the panel must not */
    dlg.addEventListener("click", function (e) { if (e.target === dlg) dlg.close(); });
    document.body.appendChild(dlg);
  }
  dlg.querySelector("h3").innerHTML = help.title;
  const body = dlg.querySelector(".help-body");
  body.innerHTML = help.body;
  body.scrollTop = 0;
  dlg.showModal();
}

/* ---------- card explanations ----------

   One entry per card, keyed by its reset id. Written for someone who
   knows the theory but has not memorised these particular formulas:
   the governing equation, what each symbol is, where the model comes
   from, and the assumption that will catch them out. */
const HELP = {
  "ohm": {
    "title": "Ohm's law and power",
    "body": "<p>Two independent relations tie the four quantities together, so any two of them fix the other two.</p><span class=\"eq\">V = I·R &nbsp;&nbsp; P = V·I = I²·R = V²/R</span><p>The card solves whichever pair you give it. The forms of P are the same equation with V or I substituted out; pick whichever avoids the quantity you are least sure of.</p><p><b>What it assumes.</b> That R is a constant. A real resistor's value moves with temperature (its TCR, typically 50–200 ppm/°C for thin film) and, at high voltage, slightly with applied voltage. Neither matters for a rough sizing; both matter in a divider that sets a reference, which is what the Tolerance tab is for.</p><p><b>The number that bites.</b> P is the one people skip. A 0603 resistor is good for about 100 mW, an 0805 for 125 mW, and the derating curve starts falling from around 70 °C ambient. Work out the dissipation before choosing the package, not after the board comes back warm.</p>"
  },
  "sp": {
    "title": "Series and parallel",
    "body": "<p>Resistors and inductors add in series and combine reciprocally in parallel. Capacitors do the opposite, and it is worth knowing why rather than memorising it.</p><span class=\"eq\">series: Z = ΣZᵢ &nbsp;&nbsp; parallel: 1/Z = Σ1/Zᵢ</span><p>That rule is about <i>impedance</i>, and it never changes. Substituting Z<sub>R</sub> = R and Z<sub>L</sub> = jωL gives the familiar sums. But Z<sub>C</sub> = 1/(jωC), so adding impedances in series adds the <i>reciprocals</i> of the capacitances:</p><span class=\"eq\">R, L: &nbsp; series ΣX &nbsp; parallel 1/Σ(1/X)<br>C: &nbsp;&nbsp;&nbsp;&nbsp; series 1/Σ(1/C) &nbsp; parallel ΣC</span><p>So capacitors in series are like resistors in parallel. Two 10 µF in series make 5 µF; two in parallel make 20 µF.</p><p><b>With a voltage applied.</b> A series chain carries one current, so each element drops in proportion to its own value: V<sub>i</sub> = V·R<sub>i</sub>/ΣR. That is where the per-element voltage and power figures come from, and it is how you find the one resistor in a chain that is quietly over its rating.</p>"
  },
  "div": {
    "title": "Divider solver",
    "body": "<p>Unloaded, the midpoint sits at</p><span class=\"eq\">V<sub>out</sub> = V<sub>in</sub> · R2 / (R1 + R2)</span><p>Draw a current I<sub>L</sub> out of that midpoint and the node equation becomes</p><span class=\"eq\">(V<sub>in</sub> − V<sub>out</sub>) / R1 = V<sub>out</sub> / R2 + I<sub>L</sub></span><p>which the card solves for whichever quantity you left out. Give it any three of V<sub>in</sub>, V<sub>out</sub>, R1 and R2 and it finds the fourth; give it only the two voltages and it searches E-series pairs, optionally against a total resistance you specify.</p><p><b>Source impedance.</b> Looking back into the midpoint you see R1 ∥ R2. That is what the next stage loads, and it is what sets how much a load current disturbs the output. It also forms a pole with any capacitance hanging on the node, which is how a feedback divider ends up slowing a regulator's loop.</p><p><b>The usual rule of thumb</b> is to make the divider's own bleed current at least ten times the load current, which keeps the loading error under about 10 %. You do not need the rule here, because the card accounts for the load exactly — but you still need it when someone hands you a divider and asks whether it is sane.</p><p><b>The trade.</b> High resistances waste less power but pick up more noise and are more affected by input bias current and by leakage across a dirty board. Low resistances are quiet but burn current continuously — on a battery product a 10 kΩ divider across the pack is a real part of the standby budget.</p>"
  },
  "led": {
    "title": "LED series resistor",
    "body": "<p>The resistor takes whatever the supply has left after the LED's forward drop, at the current you want:</p><span class=\"eq\">R = (V<sub>supply</sub> − V<sub>f</sub>) / I<sub>f</sub> &nbsp;&nbsp; P<sub>R</sub> = (V<sub>supply</sub> − V<sub>f</sub>) · I<sub>f</sub></span><p><b>Why this only sets the current approximately.</b> V<sub>f</sub> is not a constant. It varies part to part, it falls about 2 mV/°C as the die warms, and it rises with current. Differentiating the expression above gives the sensitivity:</p><span class=\"eq\">ΔI/I = −ΔV<sub>f</sub> / (V<sub>supply</sub> − V<sub>f</sub>)</span><p>So the headroom across the resistor is what buys you regulation. Driving a 3.2 V white LED from 3.3 V leaves 0.1 V, and a 100 mV shift in V<sub>f</sub> then swings the current by 100 %. From 12 V the same shift costs about 1 %. If the headroom has to be small, use a current-source driver rather than a resistor.</p><p><b>Do not parallel LEDs on one resistor.</b> The lowest-V<sub>f</sub> device takes most of the current, heats, drops further, and takes more still. One resistor per LED, or one driver channel per string.</p>"
  },
  "ec": {
    "title": "Component tolerance budget",
    "body": "<p>Every error source is expressed as a fractional deviation from nominal, and they are combined two ways:</p><span class=\"eq\">worst case = Σ|e<sub>i</sub>| &nbsp;&nbsp; RSS = √(Σe<sub>i</sub>²)</span><p><b>Which to use.</b> Worst case is what a single unit must survive if you cannot screen it: every contribution at its limit, in the same direction. RSS treats the contributions as independent random variables and gives the realistic spread of a production run. RSS assumes independence, and parts from one reel are <i>not</i> independent — a whole batch can sit at the same end of the distribution — so RSS understates lot-to-lot risk.</p><p><b>Temperature.</b> For a part with a linear coefficient,</p><span class=\"eq\">e<sub>T</sub> = TCR [ppm/°C] × ΔT × 10⁻⁶, &nbsp; ΔT = max(|T<sub>max</sub> − T<sub>nom</sub>|, |T<sub>nom</sub> − T<sub>min</sub>|)</span><p>The wider leg is used because the budget must cover the worst excursion from where the part was trimmed.</p><p><b>Class 2 ceramic capacitors are different</b>, and this is the part that catches people out. X7R, X5R, Y5V and the rest are EIA-198 codes, decoded character by character: the first is the low temperature (X = −55 °C, Y = −30, Z = +10), the second the high (5 = +85, 6 = +105, 7 = +125, 8 = +150), and the third the permitted capacitance change over that whole range (R = ±15 %, S = ±22 %, T = +22/−33 %, V = +22/−82 %). It is a bound over the full range, not a slope, so it cannot be scaled down for a narrower operating range — the curve is not linear. Note also that this is <i>on top of</i> the initial tolerance, not instead of it.</p><p><b>DC bias</b> applies to class 2 ceramics only, and it is usually the largest term of all. A 10 µF 0603 X5R at its rated voltage can be under 3 µF. The datasheet capacitance is measured at a small signal with no bias, so a budget that omits this is not conservative, it is wrong. Enter the loss from the manufacturer's bias curve at your working voltage.</p><p><b>Time.</b> Three different laws, because three different mechanisms:</p><ul><li>Class 2 ceramics lose capacitance as the ferroelectric structure relaxes, at a fixed percentage per decade of hours, referred to the 1000 h point the datasheet measures at: ΔC = k · log₁₀(t/1000). Reflow resets it.</li><li>A voltage reference drifts as a random walk, so it accumulates with the <i>square root</i> of time — hence the ppm/√1000 h units. Four times the time is twice the drift.</li><li>A crystal ages roughly linearly, and worst in its first year.</li></ul><p><b>Crystals</b> are quoted in ppm throughout: initial tolerance at 25 °C, stability over the temperature range (a separate line, because an AT-cut's frequency-temperature curve is cubic rather than a slope) and ageing per year. The card adds them and gives the frequency window in whole hertz, because four significant figures cannot show 20 ppm on a 16 MHz part.</p>"
  },
  "ac": {
    "title": "Divider ratio error",
    "body": "<p>A divider does not care what its resistors are, only about their ratio:</p><span class=\"eq\">k = R2 / (R1 + R2)</span><p>Differentiating with respect to each leg gives the sensitivities</p><span class=\"eq\">∂k/k ÷ ∂R2/R2 = (1 − k) &nbsp;&nbsp; ∂k/k ÷ ∂R1/R1 = −(1 − k)</span><p>which is the whole point of the card: they are <b>equal and opposite</b>. A change common to both legs cancels exactly. Only the <i>difference</i> between them shows up at the output.</p><p>That is why matched parts beat tight parts. Two 1 % resistors from the same thin-film array, tracking to 5 ppm/°C, give a far better divider than two individually-trimmed 0.1 % parts with 100 ppm/°C coefficients that drift apart. If you only remember one thing from this card, remember to specify <i>tracking</i> TCR for a divider, not absolute TCR.</p><p><b>Worst case</b> here is computed exactly, by pushing the two legs to opposing extremes and recomputing k, rather than by adding sensitivities — the linearised form drifts from the truth once the tolerances are large. <b>RSS</b> combines the contributions as independent random variables, which is the realistic production spread but assumes the two TCRs are uncorrelated; for parts in one array they are strongly correlated, and the real answer is better than either figure.</p><p>Note the (1 − k) factor: a divider close to unity (k → 1, R1 → 0) is insensitive to both legs, and a heavy divider (k small) passes nearly the full component error through.</p>"
  },
  "flt": {
    "title": "Filter design",
    "body": "<p>A first-order section has one energy store and one corner, where the reactance equals the resistance and the output is 3 dB down and 45° shifted:</p><span class=\"eq\">RC: f<sub>c</sub> = 1/(2πRC), τ = RC<br>RL: f<sub>c</sub> = R/(2πL), τ = L/R</span><p>The time constant is the useful companion to the corner. Step response reaches 63 % in one τ; the 10–90 % rise time is 2.2τ, and settling to 1 % takes 4.6τ. Note that rise time and bandwidth are the same fact stated twice: t<sub>r</sub> ≈ 0.35/f<sub>c</sub>.</p><p><b>LC sections are second order</b> and have a characteristic impedance as well as a resonance:</p><span class=\"eq\">f₀ = 1/(2π√(LC)) &nbsp;&nbsp; Z₀ = √(L/C) &nbsp;&nbsp; Q = R/Z₀ or Z₀/R, depending on where R sits</span><p>Q is what decides whether the filter is useful or dangerous. Undamped, an LC low-pass <i>peaks</i> at f₀ — an input filter with Q of 10 will amplify supply noise tenfold at its resonance, and a step on the input will ring. Q = 0.707 (Butterworth) is maximally flat; below 0.5 the response is overdamped and slower than the LC alone would suggest. Always ask what damps your LC filter.</p><p><b>Order.</b> Cascading n identical sections multiplies the responses, so the ultimate rolloff is 20n dB/decade — but the −3 dB point moves <i>in</i>, because each section is already attenuating at the others' corner:</p><span class=\"eq\">f<sub>−3dB</sub> = f₀ · √(2<sup>1/n</sup> − 1)</span><p>For four identical sections that is 0.435·f₀. The card assumes the sections are <b>buffered</b> from each other. Cascading passive RC sections directly does not give this response, because each section loads the one before it; the real corner ends up lower and the rolloff softer near the knee.</p>"
  },
  "re": {
    "title": "Reactance and self-resonance",
    "body": "<p>Ideally, reactance is all you need:</p><span class=\"eq\">X<sub>C</sub> = 1/(2πfC) &nbsp;&nbsp; X<sub>L</sub> = 2πfL</span><p>Real parts stop obeying those above a certain frequency, and that is what this card is really about.</p><p><b>A real capacitor</b> is C in series with its equivalent series inductance and resistance:</p><span class=\"eq\">Z = ESR + j(2πf·ESL − 1/(2πfC)) &nbsp;&nbsp; f<sub>SRF</sub> = 1/(2π√(ESL·C))</span><p>Below self-resonance the −1/ωC term dominates and it behaves like a capacitor. At resonance the two reactances cancel exactly and the impedance is <b>just the ESR</b> — the minimum of the V-shaped curve. Above resonance the ESL term wins and your decoupling capacitor is an inductor. This is why a 10 µF bulk capacitor does nothing at 100 MHz and why package inductance, not capacitance, decides high-frequency decoupling.</p><p><b>A real inductor</b> is L and its DC resistance in series, with the winding capacitance across the whole thing. It self-resonates at 1/(2π√(L·C<sub>p</sub>)), and above that it is capacitive — a common-mode choke above its SRF is a capacitor, which is the opposite of what you installed it for.</p><p><b>Paralleling n identical capacitors</b> multiplies C by n and divides both ESL and ESR by n. Since SRF depends on the product of ESL and C, and one rises exactly as the other falls, <b>self-resonance does not move</b>. What you gain is a lower impedance floor. To move the resonance you need a physically smaller part, not more of the same one.</p>"
  },
  "xc": {
    "title": "Crystal load capacitance",
    "body": "<p>In a Pierce oscillator the two load capacitors appear in series across the crystal, with the strays in parallel with that:</p><span class=\"eq\">C<sub>L</sub> = C1·C2/(C1 + C2) + C<sub>stray</sub></span><p>Given a target C<sub>L</sub> and one leg, the other follows from rearranging:</p><span class=\"eq\">C2 = (C<sub>L</sub> − C<sub>s</sub>)·C1 / (C1 − (C<sub>L</sub> − C<sub>s</sub>))</span><p>which has no solution if C1 is not larger than (C<sub>L</sub> − C<sub>s</sub>) — a series combination can never exceed its smaller member, so too small a C1 makes the target unreachable however big C2 is.</p><p><b>Why it matters.</b> The crystal is specified to hit its marked frequency <i>at</i> its rated load capacitance. Present it with the wrong C<sub>L</sub> and it is pulled off frequency: too much load pulls it low, too little pulls it high. Tens of ppm of error are easy to get this way, which is more than the crystal's own tolerance and quite enough to break a UART link or fail a radio's frequency accuracy spec.</p><p><b>Stray capacitance</b> is the pin capacitance of the oscillator input and output plus the pad and track capacitance, typically 3–5 pF and worth measuring rather than guessing on a tight design. It is not negligible: with a 12 pF crystal it is a third of the budget.</p>"
  },
  "pad": {
    "title": "PI, T and L pads",
    "body": "<p>Attenuation is a voltage ratio, so first convert decibels:</p><span class=\"eq\">N = 10<sup>A/20</sup></span><p>A PI or T pad is symmetric: it presents Z₀ at both ports while attenuating by A, so the source and load both stay matched. That is the whole reason to use a resistive pad rather than a divider.</p><span class=\"eq\">PI: &nbsp; R<sub>series</sub> = Z₀(N² − 1)/(2N), &nbsp; R<sub>shunt</sub> = Z₀(N + 1)/(N − 1)<br>T: &nbsp;&nbsp; R<sub>series</sub> = Z₀(N − 1)/(N + 1), &nbsp; R<sub>shunt</sub> = 2Z₀·N/(N² − 1)</span><p>Both give the same attenuation and the same match; choose whichever lands closer to values you can buy. At small attenuations the T pad's series resistors get very small and the PI pad's shunt resistors get very large, and vice versa at large attenuations.</p><p><b>An L pad</b> matches two <i>different</i> impedances, and cannot do so at an arbitrary attenuation. There is a minimum loss set purely by the impedance ratio:</p><span class=\"eq\">A<sub>min</sub> = 20·log₁₀(√(Z1/Z2) + √(Z1/Z2 − 1))</span><p>which is about 5.7 dB for 75 Ω to 50 Ω. Ask for less and no resistive network can match both ends; you need a transformer or a matching network.</p><p><b>Remember what a pad costs.</b> It is resistive, so it attenuates signal and noise together and adds thermal noise of its own — a 10 dB pad ahead of a receiver raises the system noise figure by 10 dB. Pads belong after gain, not before it.</p>"
  },
  "tw": {
    "title": "Trace width and current",
    "body": "<p>IPC-2221's curve fit, with the cross-section in square mils:</p><span class=\"eq\">I = k · ΔT<sup>0.44</sup> · A<sup>0.725</sup> &nbsp;&nbsp; k = 0.048 external, 0.024 internal</span><p>The card inverts it when you give a current instead. Cross-section is width × copper thickness, and the thickness comes from the copper weight: 1 oz is 34.8 µm, 2 oz is 69.6 µm, and plating adds to the outer layers.</p><p><b>Why internal is half.</b> An external trace has a face in air and convects; a buried trace can only conduct into the laminate, which is a poor conductor. The constant halves to account for it. IPC-2221 is conservative here — it came from 1950s measurements on bare boards — and IPC-2152 gives noticeably more current for the same rise, particularly for internal layers near a plane. If you need the extra margin, use 2152; this card is the classic, cautious answer.</p><p><b>ΔT is a rise, not a temperature.</b> 10 °C over a 25 °C ambient is 35 °C of copper. Add the board's own self-heating from everything else on it before deciding what rise you can afford.</p><p><b>Resistance</b> comes from ρL/A with ρ<sub>Cu</sub> = 1.72×10⁻⁸ Ω·m at 20 °C, corrected at about 0.393 %/°C. That correction is not a rounding error: copper at 85 °C is 25 % more resistive than at 20 °C, so a trace that is warm because of its own I²R loss gets warmer still.</p><p><b>Skin depth</b> δ = √(ρ/(π·f·µ)) tells you when the whole cross-section stops carrying current. At 1 MHz it is about 65 µm, so a 1 oz trace is fully used; at 100 MHz it is 6.5 µm and most of the copper is idle.</p>"
  },
  "via": {
    "title": "Via properties",
    "body": "<p>A via is a plated tube. Its copper cross-section is the annulus of the plating, not the drill:</p><span class=\"eq\">A ≈ π · (d + t) · t &nbsp;&nbsp; (d = drill diameter, t = plating thickness)</span><p>Ampacity uses the IPC-2221 internal-layer constant on that area, because a barrel is surrounded by laminate.</p><p><b>Inductance and capacitance</b> use the classic first-order expressions, with dimensions in inches:</p><span class=\"eq\">L ≈ 5.08·h·(ln(4h/d) + 1) nH &nbsp;&nbsp; C ≈ 1.41·ε<sub>r</sub>·h·D<sub>pad</sub>/(D<sub>anti</sub> − D<sub>pad</sub>) pF</span><p>Inductance is the number that matters. A via in a decoupling path adds around 1 nH, which at 100 MHz is 0.6 Ω — comparable with the capacitor's own ESL and often more than the capacitor's impedance. Two vias in parallel help, but less than half, because their loops couple magnetically.</p><p><b>√(L/C) is a lumped figure, not a characteristic impedance.</b> A via is short compared with a wavelength at most frequencies, so it behaves as a lump rather than as a transmission line. The ratio is still a useful comparison against your trace impedance: below it the via looks capacitive, above it inductive.</p><p><b>Aspect ratio</b> is board thickness ÷ drill diameter, and it is a fabrication limit, not an electrical one. Above about 10:1 the plating chemistry struggles to throw copper evenly down the barrel and reliability drops. A 0.2 mm drill in a 1.6 mm board is already 8:1.</p><p><b>Stub resonance.</b> If a signal enters on layer 1 and leaves on an inner layer, the rest of the barrel is an unterminated stub. It is a quarter-wave resonator, and at that frequency it shorts the signal:</p><span class=\"eq\">f<sub>stub</sub> = c / (4 · L<sub>stub</sub> · √ε<sub>r</sub>)</span><p>Keep the first null well above your knee frequency, or back-drill.</p>"
  },
  "fu": {
    "title": "Fusing current",
    "body": "<p>Onderdonk's equation, for the current that melts a conductor in a given time:</p><span class=\"eq\">I = A · √( log₁₀(1 + (T<sub>m</sub> − T<sub>a</sub>)/(234 + T<sub>a</sub>)) / (33 · t) )</span><p>A is the cross-section in <i>circular</i> mils (a circular mil is the area of a 1 mil circle, so multiply square mils by 4/π), T<sub>m</sub> is copper's melting point of 1083 °C, T<sub>a</sub> the ambient, and t the duration in seconds.</p><p><b>It is adiabatic.</b> The derivation assumes every joule stays in the copper and none escapes into the laminate. That is a good assumption for a short fault and a bad one for a long one, which is why the model is used up to a few seconds and no further. Beyond about 5 s a real trace sheds heat and survives considerably more current than this predicts.</p><p><b>The shape is the useful part.</b> I ∝ 1/√t, so I²t is constant — the same figure of merit a fuse datasheet uses. Halving the duration buys only 41 % more current. If a protection scheme needs twice the fault current it must clear four times faster.</p><p><b>This is a destruction limit, not a rating.</b> It is where the copper melts, not where it is happy. Design continuous currents with the trace-width card, and use this only to check that a fault is cleared before the track opens — or, if you are deliberately using a trace as a fuse, to size it.</p>"
  },
  "spc": {
    "title": "Conductor spacing",
    "body": "<p>IPC-2221 Table 6-1 gives a minimum clearance for each of seven environments, indexed by the peak voltage between the conductors. Above 500 V it becomes a per-volt slope rather than a table entry.</p><p><b>Use peak voltage, not RMS.</b> 230 V RMS mains peaks at 325 V, and it is the peak that breaks down the air.</p><p><b>The environments matter more than the voltage.</b> Look at the spread: at 300 V, an internal layer needs 0.2 mm, an external uncoated layer at sea level needs 1.25 mm, and the same board above 3050 m needs 6.4 mm. Thin air breaks down more easily, which is why altitude has its own rows — relevant to anything airborne.</p><p><b>Coating buys a lot</b>, because a permanent polymer coating or conformal coat excludes the air and the contamination. But it only counts if it is genuinely continuous over the gap; a coating that stops short of the conductors, or that has a bubble over the gap, gives you the uncoated number.</p><p><b>Clearance is not creepage.</b> This table is about clearance — distance through air. Creepage, the distance across the surface, is governed by the insulation's material group and the pollution degree, and for mains isolation it is usually the larger of the two and the one that decides your layout. IPC-2221 does not cover creepage; IEC 60664 or the relevant product safety standard does.</p>"
  },
  "z": {
    "title": "Single-ended impedance",
    "body": "<p>Characteristic impedance is set by the geometry and the dielectric — the ratio of inductance to capacitance per unit length:</p><span class=\"eq\">Z₀ = √(L/C) &nbsp;&nbsp; t<sub>pd</sub> = √ε<sub>eff</sub> / c</span><p><b>Microstrip</b> uses Hammerstad–Jensen, which is a curve fit to numerical solutions and is accurate to a fraction of a percent over 0.01 ≤ w/h ≤ 100. Outside that range the card refuses rather than extrapolating, because the fit does not degrade gracefully. When you give a frequency it applies Kirschning–Jansen dispersion: ε<sub>eff</sub> rises towards ε<sub>r</sub> as frequency increases and more of the field is pulled into the substrate, so Z₀ falls slightly.</p><p><b>Stripline</b> uses the IPC-2141 expression, 60/√ε<sub>r</sub> · ln(1.9b/(0.8w + t)). Being fully embedded, ε<sub>eff</sub> = ε<sub>r</sub> exactly and there is no dispersion to speak of, which is one reason to route critical timing on inner layers.</p><p><b>Covered microstrip is given as a bracket</b>, not a single number. Solder mask thickness and coverage vary, so the honest answer is bounded by the bare case and the fully-covered case; a real 25–50 µm mask sits nearer the bare figure. No interpolation is offered because any curve drawn between them would be invented.</p><p><b>Take the answer as a starting geometry.</b> Real stackups have resin-rich regions, glass-weave effects, trapezoidal etch and copper roughness that these closed forms do not model. Send the stackup to the fabricator and have them field-solve it; expect their number to differ by a few percent, and expect them to adjust your widths.</p>"
  },
  "dp": {
    "title": "Differential pair",
    "body": "<p>Two coupled lines have an odd mode (driven differentially) and an even mode (driven together). The differential impedance is twice the odd-mode impedance, reduced from 2Z₀ by the coupling between the traces:</p><span class=\"eq\">Z<sub>diff</sub> = 2·Z₀·(1 − k·e<sup>−m·s/h</sup>)</span><p>The exponential is the important shape: coupling falls off quickly with the gap, so beyond roughly s = 3h the traces barely see each other and Z<sub>diff</sub> approaches 2Z₀. Tight pairs are therefore <i>more</i> sensitive to spacing tolerance than loose ones.</p><p>Odd and even mode impedances are tied together by</p><span class=\"eq\">Z₀ = √(Z<sub>odd</sub> · Z<sub>even</sub>)</span><p>which is a useful identity to check any tool's output against, this one included.</p><p><b>What actually matters in practice.</b> Intra-pair skew usually costs you more margin than a few ohms of impedance error. Keep the two traces the same length, match them at the source of the mismatch rather than adding a serpentine somewhere convenient, and keep a continuous reference plane under the whole run — a pair crossing a plane split has no defined impedance at all, and the return current has to detour.</p><p><b>Validity: 0.1 &lt; w/h &lt; 3 and 0.1 &lt; s/h &lt; 3.</b> These are empirical coupling fits, so treat the result as a starting geometry and have the fabricator solve the real stackup.</p>"
  },
  "ee": {
    "title": "Effective permittivity",
    "body": "<p>A microstrip's field is partly in the substrate and partly in the air above it, so the wave sees a weighted average of the two:</p><span class=\"eq\">(ε<sub>r</sub> + 1)/2 ≤ ε<sub>eff</sub> ≤ ε<sub>r</sub></span><p>A wide trace pushes most of the field into the substrate and ε<sub>eff</sub> approaches ε<sub>r</sub>; a narrow one lets more field into the air and ε<sub>eff</sub> falls towards the lower bound. The Hammerstad–Jensen expression interpolates between them as a function of w/h.</p><p><b>Dispersion.</b> As frequency rises the field concentrates in the substrate, so ε<sub>eff</sub> increases towards ε<sub>r</sub> and propagation slows. Kirschning–Jansen models it. This is why a fast edge, which contains a spread of frequencies, arrives smeared: the high-frequency content travels slightly slower than the low.</p><p><b>What you use it for.</b> Propagation delay t<sub>pd</sub> = √ε<sub>eff</sub>/c, which is about 5.7 ps/mm for FR-4 microstrip against 6.8 ps/mm for stripline in the same material. Length-matching calculations need the right one — matching a microstrip run against a stripline run by physical length alone leaves real skew.</p><p><b>ε<sub>r</sub> itself is not a constant.</b> FR-4 is a class of materials, not a specification; 4.2–4.6 at 1 MHz is typical but it falls with frequency and varies with the glass-to-resin ratio, which varies across a panel and even along a trace as it passes over and between glass bundles.</p>"
  },
  "wl": {
    "title": "Wavelength and critical length",
    "body": "<p>The wavelength in a board is shortened by the dielectric:</p><span class=\"eq\">λ = c / (f · √ε<sub>eff</sub>)</span><p>For a digital edge, the frequency that matters is not the clock rate but the <b>knee frequency</b> — the bandwidth implied by the rise time, above which there is little energy:</p><span class=\"eq\">f<sub>knee</sub> ≈ 0.35 / t<sub>r</sub></span><p>A 1 ns edge has significant content to 350 MHz whether it is clocking at 1 MHz or 100 MHz. <b>Slow clocks with fast edges still need transmission-line treatment</b>, which is the single most commonly missed point here.</p><p><b>Critical length</b> is where a trace stops being a wire and starts being a transmission line. The physical test is whether the reflection returns before the edge has finished: if the round-trip delay is shorter than the rise time, the reflection is absorbed into the transition and you never see it. That gives l = t<sub>r</sub>·v/2, and common design rules tighten it to λ/10 or t<sub>r</sub>/6 for margin.</p><p>Beyond that length, an unterminated line rings, and the overshoot can exceed the receiver's absolute maximum rating even though the driver never leaves its rails.</p>"
  },
  "vs": {
    "title": "Via shielding",
    "body": "<p>A row of stitching vias is a waveguide wall built out of holes, and it works only while the holes are close together compared with a wavelength. The usual working rule keeps the pitch below a tenth of the shortest wavelength of interest:</p><span class=\"eq\">pitch ≤ λ/10, &nbsp; λ = c / (f · √ε<sub>r</sub>)</span><p>The physical limit is the half-wave point: when the gap between barrels approaches λ/2 the fence is transparent and the vias do nothing. λ/10 is an order of magnitude below that, which is where the leakage is small enough to ignore. λ/20 is the conservative choice for anything that must pass emissions with margin.</p><p><b>Use the knee frequency, not the clock.</b> As on the wavelength card, a fence sized for a 100 MHz clock does nothing for the 3 GHz content of a 100 ps edge.</p><p><b>Setback matters too.</b> Vias too close to a trace load the line and shift its impedance — the ground is nearer than the stackup assumes. Keep the fence beyond roughly three trace widths unless you have solved the coplanar geometry deliberately.</p><p><b>What this does not tell you.</b> It bounds the leakage rather than computing it. A real shielding effectiveness figure in dB needs a field solver, and depends on what is on the other side of the fence and on whether both ends of every via actually reach a plane.</p>"
  },
  "th": {
    "title": "Junction temperature",
    "body": "<p>Thermal resistance behaves like Ohm's law with power for current and temperature for voltage:</p><span class=\"eq\">T<sub>j</sub> = T<sub>a</sub> + P · Σθ &nbsp;&nbsp; θ<sub>ja</sub> = θ<sub>jc</sub> + θ<sub>cs</sub> + θ<sub>sa</sub></span><p>The resistances in the path add in series, so the largest one dominates and is the only one worth improving. There is no point fitting a better thermal pad if the heatsink-to-air resistance is ten times larger.</p><p>Rearranged, the same equation gives the two answers you usually want: the maximum power for a temperature limit, and the heatsink you would need for a given power:</p><span class=\"eq\">P<sub>max</sub> = (T<sub>j,max</sub> − T<sub>a</sub>) / θ<sub>ja</sub> &nbsp;&nbsp; θ<sub>sa</sub> = (T<sub>j</sub> − T<sub>a</sub>)/P − θ<sub>jc</sub> − θ<sub>cs</sub></span><p><b>Treat θ<sub>ja</sub> from a datasheet with suspicion.</b> It is measured on a specified test board — often JEDEC 2s2p, a four-layer board with solid planes — and your board is not that board. A SOT-23 quoted at 250 °C/W can be far worse on a two-layer board with a small copper pour. θ<sub>jc</sub> is a property of the package and is far more trustworthy; use it with your own estimate of the rest of the path.</p><p><b>Leave margin.</b> Silicon lifetime falls roughly exponentially with junction temperature — the usual rule of thumb is that every 10 °C halves it. Designing to T<sub>j,max</sub> is designing to the point where the manufacturer stops promising anything at all. Target 20–30 °C below it at the worst-case ambient, and remember that ambient inside a sealed enclosure is not room temperature.</p><p><b>This is a steady-state model.</b> Short power pulses are handled by thermal <i>impedance</i>, not resistance; a device can survive brief peaks well above its steady-state rating because the die's own heat capacity absorbs them.</p>"
  },
  "iec": {"title": "Clearance and creepage (IEC 60664-1)", "body": "<p>IPC-2221 gives one number, a minimum clearance through air by environment. IEC 60664-1 is the standard a mains- or high-voltage-connected product is actually assessed against, and it gives two, because there are two ways for insulation to fail.</p><p><b>Clearance</b> is the shortest path through the air. It has to survive the worst <i>transient</i> the installation can deliver, not the working voltage, so it is derived from the rated impulse withstand voltage:</p><span class=\"eq\">overvoltage category + supply voltage &rarr; impulse kV &rarr; clearance</span><p>The overvoltage category says how far you are from the origin of the installation and therefore how much the wiring in between has damped the surge. II is an appliance plugged into a fixed installation; III is part of that fixed installation; IV is at its origin. For 230 V, category II implies a 2.5 kV impulse and 1.5 mm of clearance at pollution degree 2.</p><p><b>Creepage</b> is the path along the surface, and it is about slow tracking rather than a fast breakdown: contamination plus humidity plus voltage carbonises the surface over months or years. It therefore depends on the working rms voltage, on how dirty the environment gets, and on the material.</p><ul><li><b>Pollution degree</b> 1 is sealed, 2 is normal with occasional condensation, 3 is conductive pollution. Most equipment is 2; anything that can get wet inside is 3.</li><li><b>Material group</b> comes from the laminate's comparative tracking index: I is CTI &ge; 600, II is 400 to 599, IIIa is 175 to 399, IIIb is 100 to 174. <b>Most FR-4 is IIIa</b>, which is worse than people assume and costs real millimetres. The fabricator states it; do not guess.</li></ul><p><b>Reinforced insulation</b> is not simply twice basic. Creepage doubles, but clearance takes the next step <i>up the preferred series</i> of impulse voltages &mdash; 2.5 kV becomes 4 kV, giving 3.0 mm rather than 3.0 mm by doubling. The card shows which step it used.</p><p><b>Altitude</b> thins the air, so clearance is multiplied above 2000 m &mdash; 1.14&times; at 3000 m, 1.48&times; at 5000 m. Creepage is unaffected, being a surface phenomenon. This matters for anything that flies or ships to high-altitude sites.</p><p><b>Grooves.</b> A groove in the surface adds to the creepage path, but only if it is wide enough for contamination to be washed out rather than bridging it. Narrower than the stated minimum and it counts for nothing, which is why the card reports that width.</p><p><b>Creepage is floored at the clearance here</b>, because a path along a surface cannot physically be shorter than the straight line through the air beside it. At low voltages the tables often give a smaller creepage, and the clearance is then what you build to.</p><p><b>Outside the scope of this standard:</b> above 30 kHz (IEC 60664-3), conformal coating or potting (60664-4), pollution degree 4, and insulation through any medium other than air. If your design relies on coating to make the numbers work, this card does not model it.</p>"},
  "pdn": {
    "title": "PDN target impedance",
    "body": "<p>If a load steps by ΔI and the rail may only move by ΔV, the power distribution network must present no more than their ratio:</p><span class=\"eq\">Z<sub>target</sub> = ΔV / ΔI = (V<sub>rail</sub> · ripple%) / (I<sub>max</sub> · transient%)</span><p>That single number is the design target for the whole network — regulator, bulk capacitance, decoupling, planes and package — <b>across the whole frequency range of interest</b>, not just at DC. The regulator handles up to its loop bandwidth, typically tens of kilohertz; bulk capacitors take over to a few megahertz; ceramics beyond that; and above their self-resonance only the plane capacitance and the package are left.</p><p><b>Which is why the reactance card matters here.</b> Every capacitor is inductive above its self-resonance, so the impedance curve of a real PDN is a series of V shapes. Mixing values does not simply fill the gaps: between two different capacitors' resonances there is an anti-resonant <i>peak</i> where one is inductive and the other still capacitive, and that peak can be higher than either part alone. Many identical parts, or parts with heavy damping, behave better than a decade-spaced spread.</p><p><b>The transient fraction is a guess</b>, and the answer is only as good as it. If you know the actual step profile of your load — an FPGA coming out of clock gating, a radio keying up — use it rather than a percentage.</p><p><b>What this does not do:</b> it does not tell you the inductance of your via and pad layout, which is usually what stops a PDN meeting its target above 100 MHz. Placement beats part count.</p>"
  },
  "awg": {
    "title": "AWG wire",
    "body": "<p>American Wire Gauge is a geometric series: each step of 6 gauges roughly halves the diameter, and each step of 3 roughly halves the area.</p><span class=\"eq\">d = 0.127 · 92<sup>(36 − n)/39</sup> mm &nbsp;&nbsp; A = πd²/4 &nbsp;&nbsp; R = ρL/A</span><p>Copper's resistivity is 1.72×10⁻⁸ Ω·m at 20 °C and rises about 0.393 % per °C, which the card applies at the conductor temperature you give — a wire running hot in a loom is measurably more resistive than the table value.</p><p><b>Count both directions.</b> Voltage drop is set by the total conductor length in the circuit, so a 0.5 m run means 1 m of copper unless the return is somewhere else entirely. Forgetting the return path is the most common error in a drop calculation, and it is a factor of two.</p><p><b>Ampacity depends on the installation, not the wire.</b> The two figures shown come from the classic chassis-wiring and power-transmission tables, which differ by roughly four times for the same gauge — the first assumes a single wire in free air, the second a conductor in a bundle where its neighbours are also warming it. A wire in a sealed loom in an engine bay is closer to the lower figure, or worse.</p><p><b>Usually the drop decides, not the heating.</b> A wire long enough to matter will violate your voltage budget well before it gets hot.</p>"
  },
  "bat": {
    "title": "Battery pack",
    "body": "<p>Series cells add voltage, parallel cells add capacity, and energy is the product:</p><span class=\"eq\">V<sub>pack</sub> = S · V<sub>cell</sub> &nbsp;&nbsp; Ah<sub>pack</sub> = P · Ah<sub>cell</sub> &nbsp;&nbsp; Wh = V · Ah</span><p><b>C-rate</b> normalises current to capacity: 1 C discharges the pack in one hour, so a 5 Ah pack at 2 C is drawing 10 A. It is the number cell datasheets are written in.</p><p><b>Runtime</b> is usable capacity divided by current, and the word usable is doing the work. You cannot take a lithium cell to zero — the card's default reserves 20 %. Runtime also falls faster than linearly at high current, because internal resistance both wastes energy and drags the terminal voltage down to the cutoff sooner. Peukert's effect is mild for lithium and severe for lead-acid.</p><p><b>The three voltages.</b> Nominal is the average over a discharge and is what capacity and energy are quoted at; full is the <i>resting</i> voltage of a charged cell; minimum is the discharge cutoff. For lead-acid the charging setpoint is well above the resting full voltage, which is why the card lists it separately.</p><p><b>The discharge curve is indicative.</b> It has the character of the chemistry — a lithium-iron plateau against a sloping lithium-polymer — and is bent to pass through your nominal voltage at half capacity, so a custom cell gets a curve consistent with its own three numbers. It is not your cell's measured curve; load and temperature both move it, and at high current the whole curve shifts down by I·R<sub>internal</sub>.</p><p><b>Maximum discharge is not tabulated</b>, deliberately. Within one chemistry it ranges over two orders of magnitude — a 1 C energy cell and a 100 C RC pack are both LiPo — so it has to come from your cell's own rating.</p>"
  },
  "pp": {
    "title": "Frequency error in ppm",
    "body": "<p>Parts per million is a fractional error, so it scales with the frequency:</p><span class=\"eq\">Δf = f · ppm / 10⁶</span><p>20 ppm is 20 Hz at 1 MHz and 320 Hz at 16 MHz. The card converts either way and prints the resulting window in whole hertz, because four significant figures cannot show tens of ppm on a megahertz part.</p><p><b>Budget the sources separately.</b> A crystal's datasheet quotes initial tolerance at 25 °C, stability over the temperature range, and ageing per year as three different lines, and a load capacitance error adds a fourth. They add up: ±10 ppm initial, ±20 ppm over temperature and ±3 ppm/year for five years is ±45 ppm worst case, not ±20. The Tolerance tab does this properly.</p><p><b>What the budget has to fit.</b> An asynchronous UART tolerates roughly ±2 % total between the two ends, so ppm-level accuracy is irrelevant. USB full-speed needs ±0.25 %. Ethernet needs ±100 ppm, CAN a few thousand ppm depending on bit timing, and GPS or cellular radios push into the low ppm and need a TCXO. Find the tightest consumer of your clock before choosing the part.</p>"
  },
  "nb": {
    "title": "Number bases",
    "body": "<p>Straight radix conversion between decimal, hexadecimal, binary and octal, at arbitrary size. Prefixes (<code>0x</code>, <code>0b</code>, <code>0o</code>) are optional, and spaces or underscores may be used as digit separators — <code>0b1010_1100</code> is easier to check than <code>10101100</code>.</p><p><b>Negative values are shown as two's complement</b> at each standard width that can hold them. Two's complement represents −n as 2<sup>w</sup> − n in a w-bit field, which is why −1 is all ones at every width and why the range is asymmetric: an 8-bit signed value runs from −128 to +127, not −127 to +127.</p><p>The practical use is reading a register dump: a value that looks like a wildly large unsigned number is often a small negative one, and 0xFFFFFFF8 being −8 is usually more informative than 4294967288.</p>"
  },
  "rt": {
    "title": "Ratio units",
    "body": "<p>Four ways of writing the same dimensionless fraction:</p><span class=\"eq\">1 % = 10 000 ppm = 10⁷ ppb = 0.01</span><p>Component tolerances are conventionally in per cent, temperature coefficients and frequency errors in ppm, and contamination or long-term drift in ppb. The conversions are trivial and the mistakes are not: a 100 ppm/°C resistor is 0.01 %/°C, so over a 100 °C swing it moves 1 % — comparable with its purchase tolerance, and a routine source of surprise in a design that specified 0.1 % parts.</p>"
  },
  "cv": {
    "title": "Conversions",
    "body": "<p>Length, temperature, gain, complex form and angle, each pair converting in both directions.</p><p><b>Decibels are a ratio, and the factor depends on the quantity:</b></p><span class=\"eq\">voltage: dB = 20·log₁₀(V₂/V₁) &nbsp;&nbsp; power: dB = 10·log₁₀(P₂/P₁)</span><p>Both describe the same power ratio, because power goes as voltage squared and the square becomes a factor of two in the logarithm. The factor of 20 is only correct if the impedance is the same at both points — comparing voltages across different impedances and calling the result a gain in dB is a common and quietly wrong habit.</p><p>Useful anchors worth memorising: 3 dB is ×2 in power (×1.41 in voltage), 6 dB is ×2 in voltage, 10 dB is ×10 in power, and 20 dB is ×10 in voltage.</p><p><b>Rectangular and polar</b> are the same complex number written two ways: a + jb ↔ M∠θ with M = √(a² + b²) and θ = atan2(b, a). Rectangular suits addition, polar suits multiplication and division — which is why impedances in series are easiest in rectangular form and a transfer function's magnitude and phase are easiest in polar.</p><p>A mil is one thousandth of an inch, 25.4 µm — not a millimetre, and not a thou of a millimetre either.</p>"
  }
};

/* ---------- IEC 60664-1 clearance and creepage ----------

   The tables are IEC 60664-1:2020-05 and they are the calculator: several
   hundred rows across impulse withstand, clearance against transient and
   peak voltage, and basic creepage by pollution degree and material group.
   They were transcribed mechanically from KiCad's implementation rather than
   retyped, because a typo in a safety table is not something a unit test
   would catch. See eecalc_iec60664_transcribe.py.

   The pollution-degree blocks are cumulative on purpose: a PD1 lookup whose
   voltage runs past the PD1 rows falls through into PD2 and onwards, which is
   how the standard's tables are laid out. */

function iecGrooveWidth(pd, dist) {
    if (dist <= 0)
        return -1;

    //  Based on IEC60664-1 : 2020-05 §6.8
    if (Math.abs( dist) < 3)
        return dist / 3;

    switch (pd)
    {
    case 1: return 0.25;
    case 2: return 1.0;
    case 3: return 1.5;
    default: return -1;
    }
}

function iecAltitudeFactor(alt) {
    //  Based on IEC60664-1 : 2020-05 Table A.2

    if (alt <= 2000)
        return 1.0;
    if (alt <= 3000)
        return 1.14;
    if (alt <= 4000)
        return 1.29;
    if (alt <= 5000)
        return 1.48;
    if (alt <= 6000)
        return 1.70;
    if (alt <= 7000)
        return 1.95;
    if (alt <= 8000)
        return 2.25;
    if (alt <= 9000)
        return 2.62;
    if (alt <= 10000)
        return 3.02;
    if (alt <= 15000)
        return 6.67;
    if (alt <= 20000)
        return 14.5;
    return -1;
}

function iecClearanceTransient(v, pd, field) {
    //  Based on IEC60664-1 : 2020-05 Table F.2

    switch (field)
    {
    case "inhomogeneous":
        if (pd <= 1)
        {
            if (v <= 0.33)
                return 0.01;
            if (v <= 0.40)
                return 0.02;
            if (v <= 0.50)
                return 0.04;
            if (v <= 0.60)
                return 0.06;
            if (v <= 0.80)
                return 0.10;
            if (v <= 1.0)
                return 0.15;
        }
        if (pd <= 2)
        {
            if (v <= 1.0)
                return 0.2;
            if (v <= 1.2)
                return 0.25;
            if (v <= 1.5)
                return 0.5;
        }
        if (pd <= 3)
        {
            if (v <= 1.5)
                return 0.8;
            if (v <= 2.0)
                return 1.0;
            if (v <= 2.5)
                return 1.5;
        }
        if (( pd >= 4) && ( v <= 2.5))
            return 1.6;
        if (v <= 3.0)
            return 2.0;
        if (v <= 4.0)
            return 3.0;
        if (v <= 5.0)
            return 4.0;
        if (v <= 6.0)
            return 5.5;
        if (v <= 8.0)
            return 8.0;
        if (v <= 10)
            return 11;
        if (v <= 12)
            return 14;
        if (v <= 15)
            return 18;
        if (v <= 20)
            return 25;
        if (v <= 25)
            return 33;
        if (v <= 30)
            return 40;
        if (v <= 40)
            return 60;
        if (v <= 50)
            return 75;
        if (v <= 60)
            return 90;
        if (v <= 80)
            return 130;
        if (v <= 100)
            return 170;

        break;

    case "homogeneous":
        if (pd <= 1)
        {
            if (v <= 0.33)
                return 0.01;
            if (v <= 0.40)
                return 0.02;
            if (v <= 0.50)
                return 0.04;
            if (v <= 0.60)
                return 0.06;
            if (v <= 0.80)
                return 0.10;
            if (v <= 1.0)
                return 0.15;
            if (v <= 1.2)
                return 0.2;
        }
        if (pd <= 2)
        {
            if (v <= 1.2)
                return 0.2;
            if (v <= 1.5)
                return 0.3;
            if (v <= 2.0)
                return 0.45;
            if (v <= 2.5)
                return 0.60;
            if (v <= 3.0)
                return 0.80;
        }
        if (pd <= 3)
        {
            if (v <= 3.0)
                return 0.80;
            if (v <= 4.0)
                return 1.2;
            if (v <= 5.0)
                return 1.5;
        }
        if (( pd >= 4) && ( v <= 5.0))
            return 1.6;
        if (v <= 6.0)
            return 2.0;
        if (v <= 8.0)
            return 3.0;
        if (v <= 10)
            return 3.5;
        if (v <= 12)
            return 4.5;
        if (v <= 15)
            return 5.5;
        if (v <= 20)
            return 8.0;
        if (v <= 25)
            return 10;
        if (v <= 30)
            return 12.5;
        if (v <= 40)
            return 17;
        if (v <= 50)
            return 22;
        if (v <= 60)
            return 27;
        if (v <= 80)
            return 35;
        if (v <= 100)
            return 45;

        break;

    default:
        break;
    }

    return -1;  // Out of range
}

function iecClearancePeak(v, field) {
    //  Based on IEC60664-1 : 2020-05 Table F.8

    switch (field)
    {
    case "inhomogeneous":
        if (v <= 0.04)
            return 0.001;
        if (v <= 0.06)
            return 0.002;
        if (v <= 0.1)
            return 0.003;
        if (v <= 0.12)
            return 0.004;
        if (v <= 0.15)
            return 0.005;
        if (v <= 0.20)
            return 0.006;
        if (v <= 0.25)
            return 0.008;
        if (v <= 0.33)
            return 0.01;
        if (v <= 0.4)
            return 0.02;
        if (v <= 0.5)
            return 0.04;
        if (v <= 0.6)
            return 0.06;
        if (v <= 0.8)
            return 0.13;
        if (v <= 1.0)
            return 0.26;
        if (v <= 1.2)
            return 0.42;
        if (v <= 1.5)
            return 0.76;
        if (v <= 2.0)
            return 1.27;
        if (v <= 2.5)
            return 1.8;
        if (v <= 3.0)
            return 2.4;
        if (v <= 4.0)
            return 3.8;
        if (v <= 5.0)
            return 5.7;
        if (v <= 6.0)
            return 7.9;
        if (v <= 8.0)
            return 11.0;
        if (v <= 10)
            return 15.2;
        if (v <= 12)
            return 19;
        if (v <= 15)
            return 25;
        if (v <= 20)
            return 34;
        if (v <= 25)
            return 44;
        if (v <= 30)
            return 55;
        if (v <= 40)
            return 77;
        if (v <= 50)
            return 100;

        break;

    case "homogeneous":
        if (v <= 0.04)
            return 0.001;
        if (v <= 0.06)
            return 0.002;
        if (v <= 0.1)
            return 0.003;
        if (v <= 0.12)
            return 0.004;
        if (v <= 0.15)
            return 0.005;
        if (v <= 0.20)
            return 0.006;
        if (v <= 0.25)
            return 0.008;
        if (v <= 0.33)
            return 0.01;
        if (v <= 0.33)
            return 0.01;
        if (v <= 0.4)
            return 0.02;
        if (v <= 0.5)
            return 0.04;
        if (v <= 0.6)
            return 0.06;
        if (v <= 0.8)
            return 0.1;
        if (v <= 1.0)
            return 0.15;
        if (v <= 1.2)
            return 0.2;
        if (v <= 1.5)
            return 0.3;
        if (v <= 2.0)
            return 0.45;
        if (v <= 2.5)
            return 0.6;
        if (v <= 3.0)
            return 0.8;
        if (v <= 4.0)
            return 1.2;
        if (v <= 5.0)
            return 1.5;
        if (v <= 6.0)
            return 2;
        if (v <= 8.0)
            return 3;
        if (v <= 10)
            return 3.5;
        if (v <= 12)
            return 4.5;
        if (v <= 15)
            return 5.5;
        if (v <= 20)
            return 8;
        if (v <= 25)
            return 10;
        if (v <= 30)
            return 12.5;
        if (v <= 40)
            return 17;
        if (v <= 50)
            return 22;
        if (v <= 60)
            return 27;
        if (v <= 80)
            return 35;
        if (v <= 100)
            return 45;

        break;

    default:
        break;
    }
    return -1;
}

function iecRatedImpulse(v, ovc) {
    //  Based on IEC60664-1 : 2020-05 Table F.1
    let voltage = v;

    switch (ovc)
    {
    case 1:
        if (voltage <= 50)
            return 330;
        if (voltage <= 100)
            return 500;
        if (voltage <= 150)
            return 800;
        if (voltage <= 300)
            return 1500;
        if (voltage <= 600)
            return 2500;
        if (voltage <= 1000)
            return 4000;
        if (voltage <= 1250)
            return 4000;
        if (voltage <= 1500)
            return 6000;

        break;

    case 2:
        if (voltage <= 50)
            return 500;
        if (voltage <= 100)
            return 800;
        if (voltage <= 150)
            return 1500;
        if (voltage <= 300)
            return 2500;
        if (voltage <= 600)
            return 4000;
        if (voltage <= 1000)
            return 6000;
        if (voltage <= 1250)
            return 6000;
        if (voltage <= 1500)
            return 8000;

        break;

    case 3:
         if (voltage <= 50)
            return 800;
        if (voltage <= 100)
            return 1500;
        if (voltage <= 150)
            return 2500;
        if (voltage <= 300)
            return 4000;
        if (voltage <= 600)
            return 6000;
        if (voltage <= 1000)
            return 8000;
        if (voltage <= 1250)
            return 8000;
        if (voltage <= 1500)
            return 10000;

        break;

    case 4:
        if (voltage <= 50)
            return 1500;
        if (voltage <= 100)
            return 2500;
        if (voltage <= 150)
            return 4000;
        if (voltage <= 300)
            return 6000;
        if (voltage <= 600)
            return 8000;
        if (voltage <= 1000)
            return 12000;
        if (voltage <= 1250)
            return 12000;
        if (voltage <= 1500)
            return 15000;

        break;

    default:
        break;
    }

    return -1;      // Out of range
}

function iecBasicCreepage(v, pd, mg, pcb) {
    //  Based on IEC60664-1 : 2020-05 Table F.5

    let isPcb = pcb;

    if (v > 1000)
        isPcb = false;
    if (pd >= 3)
        isPcb = false;
    if (pd >= 2 && mg == 4)
        isPcb = false;

    if (isPcb)
    {
        if (pd == 1)
        {
            if (v <= 50)
                return 0.025;
            if (v <= 63)
                return 0.040;
            if (v <= 80)
                return 0.063;
            if (v <= 100)
                return 0.100;
            if (v <= 125)
                return 0.160;
            if (v <= 160)
                return 0.250;
            if (v <= 200)
                return 0.400;
            if (v <= 250)
                return 0.560;
            if (v <= 320)
                return 0.75;
            if (v <= 400)
                return 1.0;
            if (v <= 500)
                return 1.3;
            if (v <= 630)
                return 1.8;
            if (v <= 800)
                return 2.4;
            if (v <= 1000)
                return 3.2;
        }
        if (pd == 2)
        {
            if (v <= 50)
                return 0.040;
            if (v <= 63)
                return 0.063;
            if (v <= 80)
                return 0.100;
            if (v <= 100)
                return 0.160;
            if (v <= 125)
                return 0.250;
            if (v <= 160)
                return 0.400;
            if (v <= 200)
                return 0.630;
            if (v <= 250)
                return 1.000;
            if (v <= 320)
                return 1.60;
            if (v <= 400)
                return 2.0;
            if (v <= 500)
                return 2.5;
            if (v <= 630)
                return 3.2;
            if (v <= 800)
                return 4.0;
            if (v <= 1000)
                return 5.0;
        }
    }
    if (pd == 1)
    {
        if (v <= 10)
            return 0.080;
        if (v <= 12.5)
            return 0.090;
        if (v <= 16)
            return 0.100;
        if (v <= 20)
            return 0.110;
        if (v <= 25)
            return 0.125;
        if (v <= 32)
            return 0.14;
        if (v <= 40)
            return 0.16;
        if (v <= 50)
            return 0.18;
        if (v <= 63)
            return 0.20;
        if (v <= 80)
            return 0.22;
        if (v <= 100)
            return 0.25;
        if (v <= 125)
            return 0.28;
        if (v <= 160)
            return 0.32;
        if (v <= 200)
            return 0.42;
        if (v <= 250)
            return 0.56;
        if (v <= 320)
            return 0.75;
        if (v <= 400)
            return 1.0;
        if (v <= 500)
            return 1.3;
        if (v <= 630)
            return 1.8;
        if (v <= 800)
            return 2.4;
        if (v <= 1000)
            return 3.2;
        if (v <= 1250)
            return 4.2;
        if (v <= 1600)
            return 5.6;
        if (v <= 2000)
            return 7.5;
        if (v <= 2500)
            return 10.0;
        if (v <= 3200)
            return 12.5;
        if (v <= 4000)
            return 16.0;
        if (v <= 5000)
            return 20.0;
        if (v <= 6300)
            return 25.0;
        if (v <= 8000)
            return 32.0;
        if (v <= 10000)
            return 40.0;
        if (v <= 12500)
            return 50.0;
        if (v <= 16000)
            return 63.0;
        if (v <= 20000)
            return 80.0;
        if (v <= 25000)
            return 100.0;
        if (v <= 32000)
            return 125.0;
        if (v <= 40000)
            return 160.0;
        if (v <= 50000)
            return 200.0;
        if (v <= 63000)
            return 250;
    }
    if (pd == 2 && mg == 1)
    {
        if (v <= 10)
            return 0.400;
        if (v <= 12.5)
            return 0.420;
        if (v <= 16)
            return 0.450;
        if (v <= 20)
            return 0.480;
        if (v <= 25)
            return 0.500;
        if (v <= 32)
            return 0.53;
        if (v <= 40)
            return 0.56;
        if (v <= 50)
            return 0.60;
        if (v <= 63)
            return 0.63;
        if (v <= 80)
            return 0.67;
        if (v <= 100)
            return 0.71;
        if (v <= 125)
            return 0.75;
        if (v <= 160)
            return 0.80;
        if (v <= 200)
            return 1.00;
        if (v <= 250)
            return 1.25;
        if (v <= 320)
            return 1.60;
        if (v <= 400)
            return 2.0;
        if (v <= 500)
            return 2.5;
        if (v <= 630)
            return 3.2;
        if (v <= 800)
            return 4.0;
        if (v <= 1000)
            return 5.0;
        if (v <= 1250)
            return 6.3;
        if (v <= 1600)
            return 8.0;
        if (v <= 2000)
            return 10.0;
        if (v <= 2500)
            return 12.5;
        if (v <= 3200)
            return 16.0;
        if (v <= 4000)
            return 20.0;
        if (v <= 5000)
            return 25.0;
        if (v <= 6300)
            return 32.0;
        if (v <= 8000)
            return 40.0;
        if (v <= 10000)
            return 50.0;
        if (v <= 12500)
            return 63.0;
        if (v <= 16000)
            return 80.0;
        if (v <= 20000)
            return 100.0;
        if (v <= 25000)
            return 125.0;
        if (v <= 32000)
            return 160.0;
        if (v <= 40000)
            return 200.0;
        if (v <= 50000)
            return 250.0;
        if (v <= 63000)
            return 320.0;
    }
    if (pd == 2 && mg == 2)
    {
        if (v <= 10)
            return 0.400;
        if (v <= 12.5)
            return 0.420;
        if (v <= 16)
            return 0.450;
        if (v <= 20)
            return 0.480;
        if (v <= 25)
            return 0.500;
        if (v <= 32)
            return 0.53;
        if (v <= 40)
            return 0.80;
        if (v <= 50)
            return 0.85;
        if (v <= 63)
            return 0.90;
        if (v <= 80)
            return 0.95;
        if (v <= 100)
            return 1.00;
        if (v <= 125)
            return 1.05;
        if (v <= 160)
            return 1.10;
        if (v <= 200)
            return 1.40;
        if (v <= 250)
            return 1.80;
        if (v <= 320)
            return 2.20;
        if (v <= 400)
            return 2.8;
        if (v <= 500)
            return 3.6;
        if (v <= 630)
            return 4.5;
        if (v <= 800)
            return 5.6;
        if (v <= 1000)
            return 7.1;
        if (v <= 1250)
            return 9.0;
        if (v <= 1600)
            return 11.0;
        if (v <= 2000)
            return 14.0;
        if (v <= 2500)
            return 18.0;
        if (v <= 3200)
            return 22.0;
        if (v <= 4000)
            return 28.0;
        if (v <= 5000)
            return 36.0;
        if (v <= 6300)
            return 45.0;
        if (v <= 8000)
            return 56.0;
        if (v <= 10000)
            return 71.0;
        if (v <= 12500)
            return 90.0;
        if (v <= 16000)
            return 110.0;
        if (v <= 20000)
            return 140.0;
        if (v <= 25000)
            return 180.0;
        if (v <= 32000)
            return 220.0;
        if (v <= 40000)
            return 280.0;
        if (v <= 50000)
            return 360.0;
        if (v <= 63000)
            return 450.0;
    }
    if (pd == 2
        && ( mg == 3 || mg == 4))
    {
        if (v <= 10)
            return 0.400;
        if (v <= 12.5)
            return 0.420;
        if (v <= 16)
            return 0.450;
        if (v <= 20)
            return 0.480;
        if (v <= 25)
            return 0.500;
        if (v <= 32)
            return 0.53;
        if (v <= 40)
            return 1.10;
        if (v <= 50)
            return 1.20;
        if (v <= 63)
            return 1.25;
        if (v <= 80)
            return 1.30;
        if (v <= 100)
            return 1.40;
        if (v <= 125)
            return 1.50;
        if (v <= 160)
            return 1.60;
        if (v <= 50000)
            return v / 100;
        if (v <= 63000)
            return 600.0;
    }
    if (pd == 3 && mg == 1)
    {
        if (v <= 10)
            return 1.000;
        if (v <= 12.5)
            return 1.050;
        if (v <= 16)
            return 1.100;
        if (v <= 20)
            return 1.200;
        if (v <= 25)
            return 1.250;
        if (v <= 32)
            return 1.30;
        if (v <= 40)
            return 1.40;
        if (v <= 50)
            return 1.50;
        if (v <= 63)
            return 1.60;
        if (v <= 80)
            return 1.70;
        if (v <= 100)
            return 1.80;
        if (v <= 125)
            return 1.90;
        if (v <= 160)
            return 2.00;
        if (v <= 200)
            return 2.50;
        if (v <= 250)
            return 3.20;
        if (v <= 320)
            return 4.00;
        if (v <= 400)
            return 5.0;
        if (v <= 500)
            return 6.3;
        if (v <= 630)
            return 8.0;
        if (v <= 800)
            return 10.0;
        if (v <= 1000)
            return 12.5;
        if (v <= 1250)
            return 16.0;
        if (v <= 1600)
            return 20.0;
        if (v <= 2000)
            return 25.0;
        if (v <= 2500)
            return 32.0;
        if (v <= 3200)
            return 40.0;
        if (v <= 4000)
            return 50.0;
        if (v <= 5000)
            return 63.0;
        if (v <= 6300)
            return 80.0;
        if (v <= 8000)
            return 100.0;
        if (v <= 10000)
            return 125.0;
    }
    if (pd == 3 && mg == 2)
    {
        if (v <= 10)
            return 1.000;
        if (v <= 12.5)
            return 1.050;
        if (v <= 16)
            return 1.100;
        if (v <= 20)
            return 1.200;
        if (v <= 25)
            return 1.250;
        if (v <= 32)
            return 1.30;
        if (v <= 40)
            return 1.60;
        if (v <= 50)
            return 1.70;
        if (v <= 63)
            return 1.80;
        if (v <= 80)
            return 1.90;
        if (v <= 100)
            return 2.00;
        if (v <= 125)
            return 2.10;
        if (v <= 160)
            return 2.20;
        if (v <= 200)
            return 2.80;
        if (v <= 250)
            return 3.60;
        if (v <= 320)
            return 4.50;
        if (v <= 400)
            return 5.6;
        if (v <= 500)
            return 7.1;
        if (v <= 630)
            return 9.0;
        if (v <= 800)
            return 11.0;
        if (v <= 1000)
            return 14.0;
        if (v <= 1250)
            return 18.0;
        if (v <= 1600)
            return 22.0;
        if (v <= 2000)
            return 28.0;
        if (v <= 2500)
            return 36.0;
        if (v <= 3200)
            return 45.0;
        if (v <= 4000)
            return 56.0;
        if (v <= 5000)
            return 71.0;
        if (v <= 6300)
            return 90.0;
        if (v <= 8000)
            return 110.0;
        if (v <= 10000)
            return 140.0;
    }
    if (pd == 3
        && ( mg == 3 || mg == 4))
    {
        if (v <= 10)
            return 1.000;
        if (v <= 12.5)
            return 1.050;
        if (v <= 16)
            return 1.100;
        if (v <= 20)
            return 1.200;
        if (v <= 25)
            return 1.250;
        if (v <= 32)
            return 1.30;
        if (v <= 40)
            return 1.80;
        if (v <= 50)
            return 1.90;
        if (v <= 63)
            return 2.00;
        if (v <= 80)
            return 2.10;
        if (v <= 100)
            return 2.20;
        if (v <= 125)
            return 2.40;
        if (v <= 160)
            return 2.50;
        if (v <= 200)
            return 3.20;
        if (v <= 250)
            return 4.00;
        if (v <= 320)
            return 5.00;
        if (v <= 400)
            return 6.3;
        if (v <= 500)
            return 8.0;
        if (v <= 630)
            return 10.0;
        if (v <= 800)
            return 12.5;
        if (v <= 1000)
            return 16.0;
        if (v <= 1250)
            return 20.0;
        if (v <= 1600)
            return 25.0;
        if (v <= 2000)
            return 32.0;
        if (v <= 2500)
            return 40.0;
        if (v <= 3200)
            return 50.0;
        if (v <= 4000)
            return 63.0;
        if (v <= 5000)
            return 80.0;
        if (v <= 6300)
            return 100.0;
        if (v <= 8000)
            return 125.0;
        if (v <= 10000)
            return 160.0;
    }

    return -1; // Pointed out of the table.
}

/* The procedure of charts G.1 and H.1: clearance is the worse of what the
   transient demands and what the working peak demands, scaled for altitude;
   creepage comes from the rms working voltage and doubles for reinforced
   insulation. Creepage is then floored at the clearance, because a path along
   a surface cannot be shorter than the path through the air beside it. */
function iecCompute(o) {
  const impulse = iecRatedImpulse(o.vmains, o.ovc);
  let transientKV = impulse / 1000;
  if (o.ins === "reinforced") {
    /* 5.2.5: reinforced steps up the preferred series rather than scaling */
    const STEP = { 0.33: 0.5, 0.5: 0.8, 0.8: 1.5, 1.5: 2.5, 2.5: 4, 4: 6, 6: 8, 8: 12 };
    transientKV = STEP[transientKV] !== undefined ? STEP[transientKV] : transientKV * 1.6;
  }
  const peakKV = (o.ins === "reinforced" ? o.vpeak * 1.6 : o.vpeak) / 1000;
  const c1 = iecClearanceTransient(transientKV, o.pd, o.field);
  const c2 = iecClearancePeak(peakKV, o.field);
  let clearance = (c1 === -1 || c2 === -1) ? -1 : Math.max(c1, c2);
  if (clearance > 0) clearance *= iecAltitudeFactor(o.alt);
  let creepage = iecBasicCreepage(o.vrms, o.pd, o.mg, o.pcb);
  if (creepage > 0 && o.ins === "reinforced") creepage *= 2;
  if (creepage < clearance || clearance <= 0) creepage = clearance;
  return { impulse: impulse, transientKV: transientKV, clearance: clearance,
           creepage: creepage, groove: iecGrooveWidth(o.pd, clearance) };
}

function calcIEC() {
  const vrms = numOr("iec-vrms", 230, 0);
  const vmains = numOr("iec-vmains", 230, 0);
  const alt = numOr("iec-alt", 2000, 0);
  const vpeakIn = val("iec-vpeak");
  const vpeak = isFinite(vpeakIn) && vpeakIn > 0 ? vpeakIn : vrms * Math.SQRT2;
  if (!isFinite(vrms) || !isFinite(vmains) || !isFinite(alt)) { render("iec-out", []); return; }
  const o = {
    vrms: vrms, vmains: vmains, alt: alt, vpeak: vpeak,
    ins: document.getElementById("iec-ins").value,
    ovc: parseInt(document.getElementById("iec-ovc").value, 10),
    pd: parseInt(document.getElementById("iec-pd").value, 10),
    mg: parseInt(document.getElementById("iec-mg").value, 10),
    field: document.getElementById("iec-field").value,
    pcb: document.getElementById("iec-pcb").value === "1"
  };
  const r = iecCompute(o);
  const mm = function (x) { return x > 0 ? x.toPrecision(3) + " mm" : "outside the table"; };
  const rows = [
    ["Rated impulse withstand", r.impulse > 0 ? (r.impulse / 1000).toPrecision(3) + " kV" : "outside the table"],
    ["Clearance", mm(r.clearance)],
    ["Creepage", mm(r.creepage)]
  ];
  if (r.groove > 0) rows.push(["Minimum groove width", mm(r.groove) + " \u2014 a narrower groove does not count towards creepage"]);
  if (o.ins === "reinforced") {
    rows.push(["Reinforced", "clearance taken at the next step up the preferred series (" +
               r.transientKV.toPrecision(3) + " kV), creepage doubled"]);
  }
  if (r.creepage > 0 && r.clearance > 0 && Math.abs(r.creepage - r.clearance) < 1e-9) {
    rows.push(["", "Creepage has been floored at the clearance: the table gives a shorter surface path than the " +
               "air path, which cannot be built.", ""]);
  }
  if (r.clearance <= 0 || r.creepage <= 0) {
    rows.push(["", "Some part of this falls outside the tables in the standard. Check the voltages, and note " +
               "that pollution degree 4 is not covered here at all.", "err"]);
  }
  if (alt > 2000) {
    rows.push(["Altitude", "clearance multiplied by " + iecAltitudeFactor(alt).toFixed(2) +
               " for " + alt + " m \u2014 thin air breaks down sooner; creepage is unaffected"]);
  }
  render("iec-out", rows);
}

/* ---------- wiring ---------- */

const CALCS = {
  th:  { calc: calcThermal, inputs: ["th-p","th-jc","th-cs","th-sa","th-ja","th-tjmax","th-tjtarget","th-tj","th-ta"] },
  pdn: { calc: calcPDN, inputs: ["pdn-v","pdn-ripple","pdn-i","pdn-tr","pdn-fmax"] },
  pad: { calc: calcPad, inputs: ["pad-topo","pad-a","pad-zin","pad-zout","pad-series"] },
  ee:  { calc: calcEreff, inputs: ["ee-w","ee-h","ee-er","ee-f","ee-oz"] },
  dp:  { calc: calcDiff, inputs: ["dp-struct","dp-w","dp-s","dp-h","dp-er","dp-target","dp-oz"] },
  bat: { calc: calcBattery, inputs: ["bat-chem","bat-mah","bat-vfull","bat-v","bat-vmin","bat-s","bat-p","bat-load","bat-loadunit","bat-usable","bat-crate"] },
  ohm: { calc: calcOhm, inputs: ["ohm-v","ohm-i","ohm-r","ohm-p"] },
  div: { calc: calcDivider, inputs: ["div-vin","div-vout","div-r1","div-r2","div-rtot","div-iload","div-series"] },
  sp:  { calc: calcSP, inputs: ["sp-list","sp-type","sp-v"] },
  led: { calc: calcLED, inputs: ["led-vs","led-vf","led-if","led-r","led-series"] },
  ac:  { calc: calcAccuracy, inputs: ["ac-r1","ac-r2","ac-vin","ac-tol1","ac-tol2","ac-tcr1","ac-tcr2","ac-tmin","ac-tmax","ac-tnom","ac-age"] },
  ec:  { calc: calcTolerance, inputs: ["ec-type","ec-val","ec-diel","ec-code","ec-tol","ec-tc","ec-tmin","ec-tmax","ec-tnom","ec-age","ec-life","ec-bias","ec-hyst"] },
  flt: { calc: calcFilter, inputs: ["flt-type","flt-resp","flt-order","flt-r","flt-c","flt-l","flt-f"] },
  re:  { calc: calcReact, inputs: ["re-f","re-c","re-l","re-esl","re-esr","re-n","re-epc","re-dcr"] },
  tw:  { calc: calcTrace, inputs: ["tw-i","tw-w","tw-layer","tw-len","tw-f","tw-oz","tw-dt","tw-ta"] },
  via: { calc: calcVia, inputs: ["via-d","via-tp","via-h","via-pad","via-anti","via-er","via-i","via-n","via-arlimit","via-stub","via-tr","via-z0","via-dt"] },
  fu:  { calc: calcFuse, inputs: ["fu-w","fu-t","fu-k","fu-oz","fu-ta"] },
  spc: { calc: calcSpacing, inputs: ["spc-v"] },
  iec: { calc: calcIEC, inputs: ["iec-ins","iec-vrms","iec-vpeak","iec-ovc","iec-vmains","iec-pd","iec-mg","iec-pcb","iec-field","iec-alt"] },
  z:   { calc: calcZ, inputs: ["z-struct","z-w","z-h","z-er","z-ermask","z-c","z-s","z-f","z-tand","z-rough","z-oz"] },
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

/* Choosing a chemistry replaces all three cell voltages, including any the
   user typed - that is the point of picking a different chemistry. Editing a
   single voltage afterwards keeps it, because calcBattery only fills fields
   that are blank or still showing a computed value. */
(function () {
  const sel = document.getElementById("bat-chem");
  if (!sel) return;
  sel.addEventListener("change", function () {
    const chem = CHEM[sel.value];
    if (chem) {
      setComputed("bat-vfull", chem.full);
      setComputed("bat-v", chem.nom);
      setComputed("bat-vmin", chem.min);
    }
    calcBattery();
  });
})();

["bat-graph"].forEach(function (hostId) {
  const host = document.getElementById(hostId);
  if (!host) return;
  host.addEventListener("pointermove", function (e) { miniCursor(hostId, e.clientX); });
});

/* The explanatory plots share one hover layer. Listeners sit on the
   container, which persists, so a redraw never has to re-attach them. */
["re-graph", "fu-graph"].forEach(function (hostId) {
  const host = document.getElementById(hostId);
  if (!host) return;
  host.addEventListener("pointermove", function (e) { miniCursor(hostId, e.clientX); });
  host.addEventListener("keydown", function (e) {
    const st = MINI[hostId];
    if (!st || st.index === undefined) return;
    const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
    if (!step) return;
    e.preventDefault();
    miniCursorAt(hostId, Math.max(0, Math.min(st.spec.series[0].pts.length - 1, st.index + step)));
  });
  host.addEventListener("focus", function () { if (MINI[hostId] && MINI[hostId].index === undefined) miniCursorAt(hostId, 0); });
});

/* The filter plot's hover layer. Listeners live on the container, which persists,
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
  const help = HELP[btn.dataset.reset];
  if (help) {
    const info = document.createElement("button");
    info.type = "button";
    info.className = "explain";
    info.textContent = "Explain";
    info.title = "The equations behind this card";
    info.addEventListener("click", function () { showHelp(help); });
    foot.appendChild(info);
  }
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


# The mono face this page uses draws U+221A without its overbar, so in a
# formula plate, an equation block or an SVG label "sqrt(L/C)" renders as
# something an engineer reads as an integral. Those are exactly the places a
# radical appears, so the page writes sqrt() throughout and never the glyph.
# Longest patterns first: the general "radical followed by ( " rule would
# otherwise leave the bare-symbol forms untouched.
RADICALS = [
    ("&radic;&epsilon;<sub>eff</sub>(&epsilon;<sub>r</sub>, cover)",
     "sqrt(&epsilon;<sub>eff</sub>(&epsilon;<sub>r</sub>, cover))"),
    ("&radic;&epsilon;<sub>eff</sub>", "sqrt(&epsilon;<sub>eff</sub>)"),
    ("&radic;&epsilon;<sub>r</sub>", "sqrt(&epsilon;<sub>r</sub>)"),
    ("\u221a\u03b5<sub>eff</sub>", "sqrt(\u03b5<sub>eff</sub>)"),
    ("\u221a\u03b5<sub>r</sub>", "sqrt(\u03b5<sub>r</sub>)"),
    ("√1000 h", "sqrt(1000 h)"),
    ("1/√t", "1/sqrt(t)"),
    ("&radic;(", "sqrt("),
    ("\u221a(", "sqrt("),
]


def write_sqrt(html: str) -> str:
    for old_, new_ in RADICALS:
        html = html.replace(old_, new_)
    assert "&radic;" not in html and "\u221a" not in html, "a radical glyph escaped the rewrite"
    return html


def main() -> None:
    html = write_sqrt(HTML)
    try:
        from theme_inline import inline_into
        html = inline_into(html)
    except ImportError:
        print("build_page: theme_inline not found - writing page without house styling", file=sys.stderr)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
