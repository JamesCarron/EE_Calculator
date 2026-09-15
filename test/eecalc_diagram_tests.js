// The explanatory plots: drawn when the card has enough to say, and cleared
// when it does not, so a stale curve never sits under changed inputs.
// Geometry and mode-switching are covered by eecalc_diagram_check.py.

let f = 0, pass = 0;
function eq(l, g, w) {
  if (String(g) === String(w)) { pass++; console.log("  ok   " + l); }
  else { f++; console.log("  FAIL " + l + ": got " + g + ", want " + w); }
}
function drawn(id) { const e = document.getElementById(id); return !!e && e.innerHTML.indexOf("<svg") >= 0; }
function shows(id, re) { return re.test(document.getElementById(id).innerHTML); }

console.log("\n== self-resonance plot ==");
const R = ["re-f", "re-c", "re-l", "re-esl", "re-esr", "re-n", "re-epc", "re-dcr"];
clearAll(R); calcReact();
eq("nothing to plot with no parts", drawn("re-graph"), false);
clearAll(R); set("re-c", "100n"); calcReact();
eq("a bare capacitance has no resonance to show", drawn("re-graph"), false);
clearAll(R); set("re-c", "100n"); set("re-esl", "500p"); calcReact();
eq("C with ESL plots", drawn("re-graph"), true);
eq("the capacitor is named on its curve", shows("re-graph", /capacitor/), true);
eq("only one series, so no inductor label", shows("re-graph", /inductor/), false);
eq("self-resonance is marked", shows("re-graph", /self-resonance/), true);
clearAll(R); set("re-l", "22u"); set("re-epc", "3p"); calcReact();
eq("L with winding C plots", drawn("re-graph"), true);
eq("the inductor is named on its curve", shows("re-graph", /inductor/), true);
clearAll(R); set("re-c", "100n"); set("re-esl", "500p"); set("re-l", "22u"); set("re-epc", "3p"); calcReact();
eq("both parts give two curves", shows("re-graph", /capacitor/) && shows("re-graph", /inductor/), true);
eq("the second series is dashed, not a second hue", shows("re-graph", /curve alt/), true);

console.log("\n== fusing current against duration ==");
clearAll(["fu-w", "fu-t", "fu-k"]); calcFuse();
eq("no width, no plot", drawn("fu-graph"), false);
clearAll(["fu-w", "fu-t", "fu-k"]); set("fu-w", "1"); set("fu-t", "1"); calcFuse();
eq("width and duration plot", drawn("fu-graph"), true);
eq("your chosen fault is marked", shows("fu-graph", /your fault/), true);
eq("the adiabatic limit is marked", shows("fu-graph", /adiabatic model ends/), true);

console.log("\n== divider error band ==");
clearAll(["ac-r1", "ac-r2", "ac-tol1", "ac-tol2", "ac-tcr1", "ac-tcr2", "ac-tmin", "ac-tmax", "ac-tnom", "ac-age"]);
calcAccuracy();
eq("no divider, no band", drawn("ac-graph"), false);
set("ac-r1", "10k"); set("ac-r2", "10k"); calcAccuracy();
eq("a divider gets a band", drawn("ac-graph"), true);
eq("both estimates are labelled", shows("ac-graph", /worst case/) && shows("ac-graph", /RSS/), true);
eq("the band is drawn, not implied", shows("ac-graph", /class="band"/), true);

console.log("\n== plates state the model ==");
[calcZ, calcDiff, calcTrace, calcVia, calcSP, calcPad].forEach(function (c) { c(); });
["z-diagram", "dp-diagram", "tw-diagram", "via-diagram", "sp-diagram", "pad-diagram"].forEach(function (id) {
  eq(id + " carries a formula plate", shows(id, /class="plate"/), true);
});

console.log("\n" + pass + " passed, " + f + " failed");
process.exitCode = f ? 1 : 0;
