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
  .panel { display: none; padding-bottom: 3rem; }
  .panel.active { display: block; }
  .panel h2 { font-family: var(--a-font-display); margin: 0 0 .3rem; }
  .panel p.hint { color: var(--a-ink-secondary); font-size: var(--a-text-sm); margin: 0 0 1.2rem; max-width: var(--a-measure); }
  .card { background: var(--a-bg-panel); border: var(--a-border) solid var(--a-line); border-radius: var(--a-radius); padding: 1.1rem 1.25rem 1.25rem; margin-bottom: 1rem; }
  .card h3 { margin: 0 0 .8rem; font-size: var(--a-text-body); }
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
</nav>
</div>

<main class="wrap">

<section class="panel active" id="panel-ohm">
  <h2>Ohm&rsquo;s Law &amp; Power</h2>
  <p class="hint">Fill in any two of the four values; the other two are calculated. Inputs accept SI suffixes (<code>4k7</code>, <code>10m</code>, <code>2.2M</code>).</p>
  <div class="card">
    <div class="fields">
      <div class="field"><label for="ohm-v">Voltage V (V)</label><input id="ohm-v" inputmode="decimal" placeholder="e.g. 12"></div>
      <div class="field"><label for="ohm-i">Current I (A)</label><input id="ohm-i" inputmode="decimal" placeholder="e.g. 20m"></div>
      <div class="field"><label for="ohm-r">Resistance R (&Omega;)</label><input id="ohm-r" inputmode="decimal" placeholder="e.g. 4k7"></div>
      <div class="field"><label for="ohm-p">Power P (W)</label><input id="ohm-p" inputmode="decimal" placeholder="e.g. 250m"></div>
    </div>
    <dl class="results" id="ohm-out"></dl>
    <button class="reset" data-reset="ohm">Reset</button>
  </div>
</section>

<section class="panel" id="panel-div">
  <h2>Resistor Divider</h2>
  <p class="hint">V<sub>out</sub> = V<sub>in</sub> &middot; R2 / (R1 + R2), with R1 on top and R2 to ground. The finder searches standard E-series values for the pair closest to a target output.</p>
  <div class="card">
    <h3>Divider calculator</h3>
    <div class="fields">
      <div class="field"><label for="div-vin">V<sub>in</sub> (V)</label><input id="div-vin" inputmode="decimal" placeholder="e.g. 12"></div>
      <div class="field"><label for="div-r1">R1 &mdash; top (&Omega;)</label><input id="div-r1" inputmode="decimal" placeholder="e.g. 10k"></div>
      <div class="field"><label for="div-r2">R2 &mdash; bottom (&Omega;)</label><input id="div-r2" inputmode="decimal" placeholder="e.g. 4k7"></div>
    </div>
    <dl class="results" id="div-out"></dl>
    <button class="reset" data-reset="div">Reset</button>
  </div>
  <div class="card">
    <h3>Resistor finder</h3>
    <div class="fields">
      <div class="field"><label for="fnd-vin">V<sub>in</sub> (V)</label><input id="fnd-vin" inputmode="decimal" placeholder="e.g. 12"></div>
      <div class="field"><label for="fnd-vout">Target V<sub>out</sub> (V)</label><input id="fnd-vout" inputmode="decimal" placeholder="e.g. 3.3"></div>
      <div class="field"><label for="fnd-rtot">Total R &asymp; (&Omega;, optional)</label><input id="fnd-rtot" inputmode="decimal" placeholder="e.g. 100k"></div>
      <div class="field"><label for="fnd-series">Series</label>
        <select id="fnd-series">
          <option value="E12">E12 (10 %)</option>
          <option value="E24" selected>E24 (5 %)</option>
          <option value="E96">E96 (1 %)</option>
        </select>
      </div>
    </div>
    <div class="tablewrap"><table class="finder" id="fnd-table" hidden>
      <thead><tr><th>R1 (top)</th><th>R2 (bottom)</th><th>V<sub>out</sub></th><th>Error</th><th>Current</th><th>Total R</th></tr></thead>
      <tbody id="fnd-body"></tbody>
    </table></div>
    <p class="note" id="fnd-note"></p>
    <button class="reset" data-reset="fnd">Reset</button>
  </div>
</section>

<section class="panel" id="panel-sp">
  <h2>Series / Parallel Resistance</h2>
  <p class="hint">Enter resistor values separated by commas, spaces, or new lines. Both combinations are calculated at once. Works for inductors too; for capacitors the two results swap.</p>
  <div class="card">
    <div class="fields">
      <div class="field" style="flex:1 1 100%"><label for="sp-list">Values (&Omega;)</label><textarea id="sp-list" rows="3" placeholder="e.g. 10k, 4k7, 1k"></textarea></div>
    </div>
    <dl class="results" id="sp-out"></dl>
    <button class="reset" data-reset="sp">Reset</button>
  </div>
</section>

<section class="panel" id="panel-rc">
  <h2>RC Filter Cutoff</h2>
  <p class="hint">f<sub>c</sub> = 1 / (2&pi;RC), the &minus;3 dB point of a first-order RC low-pass or high-pass. Fill in any two values.</p>
  <div class="card">
    <div class="fields">
      <div class="field"><label for="rc-r">R (&Omega;)</label><input id="rc-r" inputmode="decimal" placeholder="e.g. 10k"></div>
      <div class="field"><label for="rc-c">C (F)</label><input id="rc-c" inputmode="decimal" placeholder="e.g. 100n"></div>
      <div class="field"><label for="rc-f">f<sub>c</sub> (Hz)</label><input id="rc-f" inputmode="decimal" placeholder="e.g. 1k"></div>
    </div>
    <dl class="results" id="rc-out"></dl>
    <button class="reset" data-reset="rc">Reset</button>
  </div>
</section>

<section class="panel" id="panel-react">
  <h2>Reactance</h2>
  <p class="hint">X<sub>C</sub> = 1 / (2&pi;fC) and X<sub>L</sub> = 2&pi;fL at the given frequency. Enter a frequency plus a capacitance and/or an inductance.</p>
  <div class="card">
    <div class="fields">
      <div class="field"><label for="re-f">Frequency f (Hz)</label><input id="re-f" inputmode="decimal" placeholder="e.g. 100k"></div>
      <div class="field"><label for="re-c">Capacitance C (F)</label><input id="re-c" inputmode="decimal" placeholder="e.g. 10n"></div>
      <div class="field"><label for="re-l">Inductance L (H)</label><input id="re-l" inputmode="decimal" placeholder="e.g. 22u"></div>
    </div>
    <dl class="results" id="re-out"></dl>
    <button class="reset" data-reset="re">Reset</button>
  </div>
</section>

<section class="panel" id="panel-led">
  <h2>LED Series Resistor</h2>
  <p class="hint">R = (V<sub>supply</sub> &minus; V<sub>f</sub>) / I<sub>f</sub>. The suggestion is the next E24 value up, so the LED runs at or below the requested current.</p>
  <div class="card">
    <div class="fields">
      <div class="field"><label for="led-vs">V<sub>supply</sub> (V)</label><input id="led-vs" inputmode="decimal" placeholder="e.g. 5"></div>
      <div class="field"><label for="led-vf">LED V<sub>f</sub> (V)</label><input id="led-vf" inputmode="decimal" placeholder="e.g. 2.1"></div>
      <div class="field"><label for="led-if">LED I<sub>f</sub> (A)</label><input id="led-if" inputmode="decimal" placeholder="e.g. 10m"></div>
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

function calcDiv() {
  const vin = val("div-vin"), r1 = val("div-r1"), r2 = val("div-r2");
  if (![vin, r1, r2].every(isFinite)) { render("div-out", []); return; }
  if (r1 + r2 <= 0) { render("div-out", [["", "R1 + R2 must be positive.", "err"]]); return; }
  const vout = vin * r2 / (r1 + r2), i = vin / (r1 + r2);
  render("div-out", [
    ["V<sub>out</sub>", fmt(vout, "V")],
    ["Ratio V<sub>out</sub>/V<sub>in</sub>", (r2 / (r1 + r2)).toPrecision(4)],
    ["Current", fmt(i, "A")],
    ["P in R1", fmt(i * i * r1, "W")],
    ["P in R2", fmt(i * i * r2, "W")],
    ["Total power", fmt(vin * i, "W")]
  ]);
}

function calcFinder() {
  const vin = val("fnd-vin"), vout = val("fnd-vout"), rtot = val("fnd-rtot");
  const table = document.getElementById("fnd-table"), note = document.getElementById("fnd-note");
  table.hidden = true; note.textContent = ""; note.className = "note";
  if (!isFinite(vin) || !isFinite(vout)) return;
  if (!(vin > 0) || !(vout > 0) || vout >= vin) {
    note.textContent = "Needs 0 < Vout < Vin \u2014 a plain divider can only step down.";
    note.className = "note err";
    return;
  }
  const series = document.getElementById("fnd-series").value;
  const values = seriesValues(series, 1, 6);          // 10 ohm .. 9.76 Mohm
  const targetTot = isFinite(rtot) && rtot > 0 ? rtot : NaN;
  const k = vout / (vin - vout);                       // ideal R2/R1
  const cands = [];
  for (const r1 of values) {
    const r2 = snap(values, r1 * k);
    const vo = vin * r2 / (r1 + r2);
    const errRel = Math.abs(vo - vout) / vout;
    const totPenalty = isFinite(targetTot) ? Math.abs(Math.log10((r1 + r2) / targetTot)) : 0;
    cands.push({ r1: r1, r2: r2, vo: vo, err: errRel, score: errRel * 100 + totPenalty });
  }
  cands.sort(function (a, b) { return a.score - b.score; });
  const seen = new Set(), top = [];
  for (const c of cands) {
    const key = c.r1 + "/" + c.r2;
    if (seen.has(key)) continue;
    seen.add(key); top.push(c);
    if (top.length === 5) break;
  }
  document.getElementById("fnd-body").innerHTML = top.map(function (c) {
    const i = vin / (c.r1 + c.r2);
    return "<tr><td>" + fmt(c.r1, "\u03a9") + "</td><td>" + fmt(c.r2, "\u03a9") + "</td><td>" +
      fmt(c.vo, "V") + "</td><td>" + (c.err * 100).toFixed(3) + " %</td><td>" +
      fmt(i, "A") + "</td><td>" + fmt(c.r1 + c.r2, "\u03a9") + "</td></tr>";
  }).join("");
  table.hidden = false;
  note.textContent = "Best " + series + " pairs, ranked by Vout error" +
    (isFinite(targetTot) ? ", then closeness to the requested total resistance." : ". Enter a total resistance to steer divider current.");
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
  const e24 = seriesValues("E24", -1, 7);
  let std = e24[e24.length - 1];
  for (const v of e24) if (v >= r) { std = v; break; }
  const iStd = (vs - vf) / std;
  render("led-out", [
    ["Exact resistor", fmt(r, "\u03a9")],
    ["Next E24 up", fmt(std, "\u03a9")],
    ["Current with E24 value", fmt(iStd, "A")],
    ["Resistor power", fmt(iStd * iStd * std, "W")],
    ["LED power", fmt(vf * iStd, "W")]
  ]);
}

/* ---------- wiring ---------- */

const CALCS = {
  ohm: { calc: calcOhm, inputs: ["ohm-v","ohm-i","ohm-r","ohm-p"] },
  div: { calc: calcDiv, inputs: ["div-vin","div-r1","div-r2"] },
  fnd: { calc: calcFinder, inputs: ["fnd-vin","fnd-vout","fnd-rtot","fnd-series"] },
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
