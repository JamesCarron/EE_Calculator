// Tests for the UI rework: dBm removed, filters combined, cards moved,
// board settings folded back into the cards that use them.
//
// Tab memory and the mirror write-through live in the page's wiring section,
// which the harness excludes; both are verified in the browser.

let f = 0, pass = 0;
function eq(l, g, w) {
  if (String(g) === String(w)) { pass++; console.log("  ok   " + l); }
  else { f++; console.log("  FAIL " + l + ": got " + g + ", want " + w); }
}
function near(l, g, w, t) {
  if (Math.abs(g - w) <= Math.abs(w) * t / 100) { pass++; console.log("  ok   " + l + " = " + Number(g.toPrecision(6))); }
  else { f++; console.log("  FAIL " + l + ": got " + g + ", want ~" + w); }
}
function has(l, id, re) {
  const t = JSON.stringify(rows(id));
  if (re.test(t)) { pass++; console.log("  ok   " + l); }
  else { f++; console.log("  FAIL " + l + " in " + t); }
}

console.log("\n== disabled cards are gone ==");
eq("no dBm chain", hasField("db-in") || hasField("db-z"), false);
eq("no plane capacitance", hasField("pc-a"), false);
eq("no separate RC card", hasField("rc-r"), false);
eq("no separate LC card", hasField("lc-topo"), false);
eq("no standalone capacitor SRF card", hasField("cs-c"), false);

console.log("\n== combined filter: RC ==");
const F = ["flt-r", "flt-c", "flt-l", "flt-f"];
document.getElementById("flt-type").value = "rc";
document.getElementById("flt-resp").value = "lp";
document.getElementById("flt-order").value = "1";
clearAll(F); set("flt-r", "10k"); set("flt-c", "100n"); calcFilter();
near("cutoff 159.15 Hz", parseVal(get("flt-f")), 159.15, 0.1);
eq("frequency is a calculated field", isCalc("flt-f"), true);
has("time constant 1 ms", "flt-out", /1 ms/);
has("rise time given", "flt-out", /Rise time/);
has("settling given", "flt-out", /Settling to 1 %/);
clearAll(F); set("flt-r", "10k"); set("flt-f", "1k"); calcFilter();
near("solves C from R and f", parseVal(get("flt-c")), 15.915e-9, 0.1);

console.log("\n== combined filter: RL ==");
document.getElementById("flt-type").value = "rl";
clearAll(F); set("flt-r", "100"); set("flt-l", "10u"); calcFilter();
near("corner 1.5915 MHz", parseVal(get("flt-f")), 1.5915e6, 0.1);
has("time constant L/R", "flt-out", /&tau; = L\/R/);

console.log("\n== combined filter: LC is a loaded filter, not a resonator ==");
document.getElementById("flt-type").value = "lc";
document.getElementById("flt-resp").value = "lp";
clearAll(F); set("flt-l", "10u"); set("flt-c", "100n"); calcFilter();
near("resonance 159.15 kHz", parseVal(get("flt-f")), 159154, 0.1);
has("characteristic impedance 10 ohm", "flt-out", /10 Ω/);
has("states the assumed Q", "flt-out", /Q \(assumed, no load given\)/);
set("flt-r", "1"); calcFilter();
has("loaded Q with a 1 ohm load", "flt-out", /Q with 1 Ω load/);
has("overdamped is flagged", "flt-out", /overdamped/);
clearAll(F); set("flt-l", "10u"); set("flt-f", "159154"); calcFilter();
near("sizes the missing C for a target", parseVal(get("flt-c")), 100e-9, 0.5);

console.log("\n== moved cards still work where they now live ==");
eq("reactance carries the capacitor parasitics", hasField("re-esl"), true);
eq("reactance carries the inductor parasitics", hasField("re-epc"), true);
eq("frequency error moved to Utilities", hasField("pp-f"), true);
eq("attenuator pads moved to Filters", hasField("pad-a"), true);
clearAll(["re-f", "re-c", "re-l", "re-esl", "re-esr", "re-n", "re-epc", "re-dcr"]);
set("re-c", "100n"); set("re-esl", "500p"); calcReact();
has("capacitor SRF still 22.5 MHz", "re-out", /22\.5[0-9]* MHz/);
clearAll(["pp-f", "pp-ppm", "pp-df"]);
set("pp-f", "16M"); set("pp-ppm", "20"); calcPPM();
has("ppm window still resolves", "pp-out", /15,999,680/);

console.log("\n== board settings live on their cards, sharing one value ==");
eq("old strip is gone", hasField("g-oz") || hasField("g-series"), false);
["tw-oz", "fu-oz", "z-oz", "ee-oz", "dp-oz"].forEach(function (id) {
  eq(id + " present", hasField(id), true);
});
eq("temp rise on trace and via", hasField("tw-dt") && hasField("via-dt"), true);
eq("ambient on trace, fusing and thermal", hasField("tw-ta") && hasField("fu-ta") && hasField("th-ta"), true);
eq("E-series on divider, LED and pads",
   hasField("div-series") && hasField("led-series") && hasField("pad-series"), true);

console.log("\n" + pass + " passed, " + f + " failed");
process.exitCode = f ? 1 : 0;
