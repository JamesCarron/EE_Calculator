"""Generate EE_Calculator.html - a self-contained tabbed EE calculator page.

Written 2026-08-26 for C:\\Auterion\\Tools\\EE_Calculator.

All calculator logic is in-page JavaScript because the page is interactive at
runtime with no server; Python here is only the build harness. The Auterion
house stylesheet and brand fonts are inlined via Tools\\brand\\auterion_inline
so the output works offline, opened straight from the filesystem.

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
  .tabs button[aria-selected="true"] { background: var(--a-bg-accent); color: var(--a-on-accent); border-color: var(--a-bg-accent); }
  .tabs button:focus-visible { outline: 2px solid var(--a-focus); outline-offset: 2px; }
  .serieswrap { margin-left: auto; display: flex; align-items: center; gap: .45rem; font-size: var(--a-text-xs); color: var(--a-ink-secondary); }
  .serieswrap select { font: inherit; font-family: var(--a-font-mono); color: var(--a-ink); background: var(--a-bg); border: var(--a-border) solid var(--a-line-strong); border-radius: var(--a-radius-sm); padding: .3rem .45rem; }
  .serieswrap select:focus-visible { outline: 2px solid var(--a-focus); outline-offset: 1px; }
  .panel { display: none; padding-bottom: 3rem; }
  .panel.active { display: block; }
  .panel h2 { font-family: var(--a-font-display); margin: 0 0 .3rem; }
  .panel p.hint { color: var(--a-ink-secondary); font-size: var(--a-text-sm); margin: 0 0 1.2rem; max-width: var(--a-measure); }
  .card { background: var(--a-bg-panel); border: var(--a-border) solid var(--a-line); border-radius: var(--a-radius); padding: 1.1rem 1.25rem 1.25rem; margin-bottom: 1rem; }
  .card h3 { margin: 0 0 .8rem; font-size: var(--a-text-body); }
  .cardrow { display: flex; flex-wrap: wrap; gap: 1rem 2.5rem; align-items: flex-start; }
  .cardrow .fields { flex: 1 1 20rem; }
  svg.schem { color: var(--a-ink-secondary); flex: 0 0 auto; max-width: 100%; }
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
  button.reset { font: inherit; font-size: var(--a-text-xs); color: var(--a-link); background: none; border: none; cursor: pointer; padding: 0; margin-top: 1rem; }
  button.reset:hover { color: var(--a-link-hover); text-decoration: underline; }
  footer.site { border-top: var(--a-border) solid var(--a-line); color: var(--a-ink-muted); font-size: var(--a-text-xs); padding: 1rem 0 2rem; }
</style>
</head>
<body>
<header class="site wrap">
  <p class="eyebrow">Auterion &middot; Tools</p>
  <h1>EE Calculator</h1>
</header>

<div class="wrap">
<nav class="tabs" role="tablist" id="tabbar">
  <button role="tab" data-tab="ohm" aria-selected="true">Ohm&rsquo;s Law</button>
  <button role="tab" data-tab="div" aria-selected="false">Resistor Divider</button>
  <button role="tab" data-tab="sp" aria-selected="false">Series / Parallel</button>
  <button role="tab" data-tab="rc" aria-selected="false">RC Filter</button>
  <button role="tab" data-tab="react" aria-selected="false">Reactance</button>
  <button role="tab" data-tab="led" aria-selected="false">LED Resistor</button>
  <span class="serieswrap"><label for="g-series">E-series</label>
    <select id="g-series">
      <option value="E12">E12 (10 %)</option>
      <option value="E24">E24 (5 %)</option>
      <option value="E96" selected>E96 (1 %)</option>
    </select>
  </span>
</nav>
</div>

<main class="wrap">

<section class="panel active" id="panel-ohm">
  <h2>Ohm&rsquo;s Law &amp; Power</h2>
  <p class="hint">Fill in any two of the four values; the other two are calculated. Inputs accept SI suffixes (<code>4k7</code>, <code>10m</code>, <code>2.2M</code>).</p>
  <div class="card">
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
</section>

<section class="panel" id="panel-div">
  <h2>Resistor Divider</h2>
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
</section>

<section class="panel" id="panel-sp">
  <h2>Series / Parallel Resistance</h2>
  <p class="hint">Enter resistor values separated by commas, spaces, or new lines. Both combinations are calculated at once. Works for inductors too; for capacitors the two results swap.</p>
  <div class="card">
    <div class="cardrow">
    <div class="fields">
      <div class="field" style="flex:1 1 100%"><label for="sp-list">Values (&Omega;)</label><textarea id="sp-list" rows="3" placeholder="e.g. 10k, 4k7, 1k"></textarea></div>
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

<section class="panel" id="panel-rc">
  <h2>RC Filter Cutoff</h2>
  <p class="hint">f<sub>c</sub> = 1 / (2&pi;RC), the &minus;3 dB point of a first-order RC low-pass or high-pass. Fill in any two values.</p>
  <div class="card">
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="rc-r">R (&Omega;)</label><input id="rc-r" inputmode="decimal" placeholder="e.g. 10k"></div>
      <div class="field"><label for="rc-c">C (F)</label><input id="rc-c" inputmode="decimal" placeholder="e.g. 100n"></div>
      <div class="field"><label for="rc-f">f<sub>c</sub> (Hz)</label><input id="rc-f" inputmode="decimal" placeholder="e.g. 1k"></div>
    </div>
    <svg class="schem" width="230" height="150" viewBox="0 0 230 150" role="img" aria-label="RC low-pass: series R from Vin to Vout, C from Vout to ground">
      <circle class="wire" cx="18" cy="40" r="3.5"/>
      <text x="8" y="26">Vin</text>
      <path class="wire" d="M21.5 40 H58"/>
      <rect class="wire" x="58" y="32" width="40" height="16"/>
      <text x="72" y="27">R</text>
      <path class="wire" d="M98 40 H140"/>
      <circle class="dot" cx="140" cy="40" r="3"/>
      <path class="wire" d="M140 40 H172"/>
      <circle class="wire" cx="175.5" cy="40" r="3.5"/>
      <text x="186" y="44">Vout</text>
      <path class="wire" d="M140 40 V72"/>
      <path class="wire" d="M126 72 H154 M126 82 H154"/>
      <text x="162" y="82">C</text>
      <path class="wire" d="M140 82 V106"/>
      <path class="wire" d="M126 106 H154 M131 113 H149 M136 120 H144"/>
      <text x="8" y="142">Swap R and C for a high-pass; same f<tspan dy="3" font-size="9">c</tspan><tspan dy="-3">.</tspan></text>
    </svg>
    </div>
    <dl class="results" id="rc-out"></dl>
    <button class="reset" data-reset="rc">Reset</button>
  </div>
</section>

<section class="panel" id="panel-react">
  <h2>Reactance</h2>
  <p class="hint">X<sub>C</sub> = 1 / (2&pi;fC) and X<sub>L</sub> = 2&pi;fL at the given frequency. Enter a frequency plus a capacitance and/or an inductance.</p>
  <div class="card">
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="re-f">Frequency f (Hz)</label><input id="re-f" inputmode="decimal" placeholder="e.g. 100k"></div>
      <div class="field"><label for="re-c">Capacitance C (F)</label><input id="re-c" inputmode="decimal" placeholder="e.g. 10n"></div>
      <div class="field"><label for="re-l">Inductance L (H)</label><input id="re-l" inputmode="decimal" placeholder="e.g. 22u"></div>
    </div>
    <svg class="schem" width="250" height="105" viewBox="0 0 250 105" role="img" aria-label="Capacitor and inductor symbols">
      <path class="wire" d="M12 40 H48"/>
      <path class="wire" d="M48 24 V56 M58 24 V56"/>
      <path class="wire" d="M58 40 H94"/>
      <text x="48" y="16">C</text>
      <text x="16" y="80">X<tspan dy="3" font-size="9">C</tspan><tspan dy="-3"> = 1/(2&#960;fC)</tspan></text>
      <path class="wire" d="M140 40 H155"/>
      <path class="wire" d="M155 40 A7.5 7.5 0 0 1 170 40 A7.5 7.5 0 0 1 185 40 A7.5 7.5 0 0 1 200 40 A7.5 7.5 0 0 1 215 40"/>
      <path class="wire" d="M215 40 H230"/>
      <text x="181" y="16">L</text>
      <text x="150" y="80">X<tspan dy="3" font-size="9">L</tspan><tspan dy="-3"> = 2&#960;fL</tspan></text>
    </svg>
    </div>
    <dl class="results" id="re-out"></dl>
    <button class="reset" data-reset="re">Reset</button>
  </div>
</section>

<section class="panel" id="panel-led">
  <h2>LED Series Resistor</h2>
  <p class="hint">R = (V<sub>supply</sub> &minus; V<sub>f</sub>) / I<sub>f</sub>. The suggestion is the next value up in the E-series chosen at the top, so the LED runs at or below the requested current.</p>
  <div class="card">
    <div class="cardrow">
    <div class="fields">
      <div class="field"><label for="led-vs">V<sub>supply</sub> (V)</label><input id="led-vs" inputmode="decimal" placeholder="e.g. 5"></div>
      <div class="field"><label for="led-vf">LED V<sub>f</sub> (V)</label><input id="led-vf" inputmode="decimal" placeholder="e.g. 2.1"></div>
      <div class="field"><label for="led-if">LED I<sub>f</sub> (A)</label><input id="led-if" inputmode="decimal" placeholder="e.g. 10m"></div>
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

</main>

<footer class="site"><div class="wrap">EE Calculator &mdash; all calculation runs locally in this page; nothing leaves your machine.</div></footer>

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

function seriesValues(name, decMin, decMax) {
  const base = SERIES[name], out = [];
  for (let d = decMin; d <= decMax; d++)
    for (const b of base) out.push(Math.round(b * Math.pow(10, d) * 100) / 100);
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
  const V = val("ohm-v"), I = val("ohm-i"), R = val("ohm-r"), P = val("ohm-p");
  const given = [["V",V],["I",I],["R",R],["P",P]].filter(function (x) { return isFinite(x[1]); });
  if (given.length < 2) { render("ohm-out", given.length ? [["", "Enter one more value.", ""]] : []); return; }
  if (given.length > 2) { render("ohm-out", [["", "More than two values entered \u2014 using " + given[0][0] + " and " + given[1][0] + ".", "warn"]].concat(solveOhm(given[0], given[1]))); return; }
  render("ohm-out", solveOhm(given[0], given[1]));
}

function solveOhm(a, b) {
  const g = {}; g[a[0]] = a[1]; g[b[0]] = b[1];
  let V = g.V, I = g.I, R = g.R, P = g.P;
  if (V != null && I != null) { R = V / I; P = V * I; }
  else if (V != null && R != null) { I = V / R; P = V * V / R; }
  else if (V != null && P != null) { I = P / V; R = V * V / P; }
  else if (I != null && R != null) { V = I * R; P = I * I * R; }
  else if (I != null && P != null) { V = P / I; R = P / (I * I); }
  else if (R != null && P != null) { V = Math.sqrt(P * R); I = Math.sqrt(P / R); }
  return [["Voltage", fmt(V, "V")], ["Current", fmt(I, "A")], ["Resistance", fmt(R, "\u03a9")], ["Power", fmt(P, "W")]];
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
  const series = document.getElementById("g-series").value;

  // Total R can stand in for a missing leg when the other is known.
  let legFromTotal = false;
  if (isFinite(rtot) && isFinite(r1) !== isFinite(r2)) {
    legFromTotal = true;
    if (isFinite(r1)) {
      if (rtot <= r1) { render("div-out", [["", "Total R must exceed R1.", "err"]]); return; }
      r2 = rtot - r1; rows.push(["R2 from total", fmt(r2, "Ω")]);
    } else {
      if (rtot <= r2) { render("div-out", [["", "Total R must exceed R2.", "err"]]); return; }
      r1 = rtot - r2; rows.push(["R1 from total", fmt(r1, "Ω")]);
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
        rows.push(["Exact R1 / R2 for this total", fmt(er1, "Ω") + " / " + fmt(er2, "Ω")]);
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
    const std = snap(seriesValues(series, -1, 7), exact);   // 100 mohm .. 97.6 Mohm
    if (solve === "R1") sr1 = std; else sr2 = std;
    rows.push(["Exact " + solve, fmt(exact, "Ω")]);
    rows.push(["Nearest " + series, fmt(std, "Ω")]);
    svout = (svin - sr1 * il) / (1 + sr1 / sr2);
    rows.push(["V<sub>out</sub> with " + series + " value", fmt(svout, "V") + " (" + ((svout - vout) / vout * 100).toFixed(3) + " %)"]);
  } else if (solve === "Vout") {
    svout = (vin - r1 * il) / (1 + r1 / r2);
    if (svout <= 0) { render("div-out", [["", "The load pulls the midpoint to zero — V<sub>out</sub> would be negative.", "err"]]); return; }
    rows.push(["V<sub>out</sub>", fmt(svout, "V")]);
  } else {                                                  // solve Vin
    if (!(vout > 0)) { render("div-out", [["", "V<sub>out</sub> must be positive.", "err"]]); return; }
    svin = vout + r1 * (vout / r2 + il);
    rows.push(["Required V<sub>in</sub>", fmt(svin, "V")]);
  }

  const i1 = (svin - svout) / sr1, i2 = svout / sr2;
  rows.push(["Ratio V<sub>out</sub>/V<sub>in</sub>", (svout / svin).toPrecision(4)]);
  rows.push(["Current in R1", fmt(i1, "A")]);
  rows.push(["Current in R2", fmt(i2, "A")]);
  rows.push(["P in R1 / R2", fmt(i1 * i1 * sr1, "W") + " / " + fmt(i2 * i2 * sr2, "W")]);
  rows.push(["Total R1&#8202;+&#8202;R2", fmt(sr1 + sr2, "Ω")]);
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
  if (!raw) { render("sp-out", []); return; }
  const parts = raw.split(/[\s,;]+/).filter(Boolean);
  const vals = parts.map(parseVal);
  const bad = parts.filter(function (p, i) { return !isFinite(vals[i]) || vals[i] <= 0; });
  if (bad.length) { render("sp-out", [["", "Could not read: " + bad.join(", "), "err"]]); return; }
  const series = vals.reduce(function (a, b) { return a + b; }, 0);
  const parallel = 1 / vals.reduce(function (a, b) { return a + 1 / b; }, 0);
  render("sp-out", [
    ["Values", vals.length + ""],
    ["Series", fmt(series, "\u03a9")],
    ["Parallel", fmt(parallel, "\u03a9")]
  ]);
}

/* ---------- RC filter ---------- */

function calcRC() {
  const R = val("rc-r"), C = val("rc-c"), F = val("rc-f");
  const have = [isFinite(R), isFinite(C), isFinite(F)].filter(Boolean).length;
  if (have < 2) { render("rc-out", []); return; }
  const TAU = 2 * Math.PI;
  let r = R, c = C, f = F;
  if (isFinite(R) && isFinite(C)) f = 1 / (TAU * R * C);
  else if (isFinite(R) && isFinite(F)) c = 1 / (TAU * R * F);
  else c = C, r = 1 / (TAU * C * F);
  render("rc-out", [
    ["R", fmt(r, "\u03a9")], ["C", fmt(c, "F")],
    ["Cutoff f<sub>c</sub>", fmt(f, "Hz")],
    ["Time constant \u03c4 = RC", fmt(r * c, "s")]
  ]);
}

/* ---------- reactance ---------- */

function calcReact() {
  const f = val("re-f"), C = val("re-c"), L = val("re-l");
  if (!isFinite(f) || f <= 0) { render("re-out", []); return; }
  const rows = [];
  if (isFinite(C) && C > 0) rows.push(["X<sub>C</sub> at " + fmt(f, "Hz"), fmt(1 / (2 * Math.PI * f * C), "\u03a9")]);
  if (isFinite(L) && L > 0) rows.push(["X<sub>L</sub> at " + fmt(f, "Hz"), fmt(2 * Math.PI * f * L, "\u03a9")]);
  if (isFinite(C) && C > 0 && isFinite(L) && L > 0)
    rows.push(["LC resonance", fmt(1 / (2 * Math.PI * Math.sqrt(L * C)), "Hz")]);
  render("re-out", rows);
}

/* ---------- LED resistor ---------- */

function calcLED() {
  const vs = val("led-vs"), vf = val("led-vf"), iF = val("led-if");
  if (![vs, vf, iF].every(isFinite)) { render("led-out", []); return; }
  if (vs <= vf) { render("led-out", [["", "Supply must exceed the LED forward voltage.", "err"]]); return; }
  if (iF <= 0) { render("led-out", [["", "Forward current must be positive.", "err"]]); return; }
  const r = (vs - vf) / iF;
  const series = document.getElementById("g-series").value;
  const vals = seriesValues(series, -1, 7);
  let std = vals[vals.length - 1];
  for (const v of vals) if (v >= r) { std = v; break; }
  const iStd = (vs - vf) / std;
  render("led-out", [
    ["Exact resistor", fmt(r, "\u03a9")],
    ["Next " + series + " up", fmt(std, "\u03a9")],
    ["Current with " + series + " value", fmt(iStd, "A")],
    ["Resistor power", fmt(iStd * iStd * std, "W")],
    ["LED power", fmt(vf * iStd, "W")]
  ]);
}

/* ---------- wiring ---------- */

const CALCS = {
  ohm: { calc: calcOhm, inputs: ["ohm-v","ohm-i","ohm-r","ohm-p"] },
  div: { calc: calcDivider, inputs: ["div-vin","div-vout","div-r1","div-r2","div-rtot","div-iload"] },
  sp:  { calc: calcSP, inputs: ["sp-list"] },
  rc:  { calc: calcRC, inputs: ["rc-r","rc-c","rc-f"] },
  re:  { calc: calcReact, inputs: ["re-f","re-c","re-l"] },
  led: { calc: calcLED, inputs: ["led-vs","led-vf","led-if"] }
};

for (const key in CALCS) {
  const c = CALCS[key];
  for (const id of c.inputs) {
    const el = document.getElementById(id);
    el.addEventListener("input", c.calc);
    el.addEventListener("change", c.calc);
  }
}

// the top-level E-series setting feeds every calculator that suggests standard values
document.getElementById("g-series").addEventListener("change", function () {
  calcDivider(); calcLED();
});

document.querySelectorAll("button.reset").forEach(function (btn) {
  btn.addEventListener("click", function () {
    const c = CALCS[btn.dataset.reset];
    for (const id of c.inputs) {
      const el = document.getElementById(id);
      if (el.tagName === "SELECT") el.selectedIndex = el.querySelector("[selected]") ? Array.prototype.indexOf.call(el.options, el.querySelector("[selected]")) : 0;
      else el.value = "";
      el.classList.remove("bad");
    }
    c.calc();
  });
});

const tabbar = document.getElementById("tabbar");
tabbar.addEventListener("click", function (e) {
  const btn = e.target.closest("button[data-tab]");
  if (!btn) return;
  tabbar.querySelectorAll("button").forEach(function (b) { b.setAttribute("aria-selected", b === btn ? "true" : "false"); });
  document.querySelectorAll(".panel").forEach(function (p) { p.classList.toggle("active", p.id === "panel-" + btn.dataset.tab); });
  try { location.hash = btn.dataset.tab; } catch (err) {}
});

// deep-link: #div opens the divider tab
const hash = location.hash.replace("#", "");
if (hash && document.getElementById("panel-" + hash)) {
  const btn = tabbar.querySelector('button[data-tab="' + hash + '"]');
  if (btn) btn.click();
}
</script>
</body>
</html>
"""


def main() -> None:
    html = HTML
    try:
        sys.path.insert(0, r"C:\Auterion\Tools\brand")
        from auterion_inline import inline_into
        html = inline_into(html)
    except ImportError:
        print("build_page: Tools\\brand helper not found - writing page without house styling", file=sys.stderr)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
