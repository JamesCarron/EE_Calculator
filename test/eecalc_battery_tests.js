// Battery: chemistry presets, charge and discharge limits, and the shape of
// the indicative discharge curve.

let f = 0, pass = 0;
function eq(l, g, w) {
  if (String(g) === String(w)) { pass++; console.log("  ok   " + l); }
  else { f++; console.log("  FAIL " + l + ": got " + g + ", want " + w); }
}
function near(l, g, w, t) {
  if (Math.abs(g - w) <= Math.abs(w) * t / 100) { pass++; console.log("  ok   " + l + " = " + Number(g.toPrecision(6))); }
  else { f++; console.log("  FAIL " + l + ": got " + g + ", want ~" + w); }
}
function has(l, re) {
  const t = JSON.stringify(rows("bat-out"));
  if (re.test(t)) { pass++; console.log("  ok   " + l); }
  else { f++; console.log("  FAIL " + l + " in " + t.slice(0, 400)); }
}
function chem(k) {
  document.getElementById("bat-chem").value = k;
  const c = CHEM[k];
  if (c) { setComputed("bat-vfull", c.full); setComputed("bat-v", c.nom); setComputed("bat-vmin", c.min); }
}
function curve() { return MINI["bat-graph"].spec.series[0].pts; }
function atPct(pts, x) {
  let b = pts[0];
  for (const q of pts) if (Math.abs(q[0] - x) < Math.abs(b[0] - x)) b = q;
  return b[1];
}
const F = ["bat-mah", "bat-vfull", "bat-v", "bat-vmin", "bat-s", "bat-p", "bat-load", "bat-usable", "bat-crate"];

console.log("\n== presets fill the voltages and are used straight away ==");
clearAll(F); chem("lipo"); set("bat-mah", "5000"); calcBattery();
eq("LiPo full 4.2", get("bat-vfull"), "4.2");
eq("LiPo nominal 3.7", get("bat-v"), "3.7");
eq("LiPo minimum 3", get("bat-vmin"), "3");
has("the pack is named for its chemistry", /LiPo/);
clearAll(F); chem("lifepo4"); set("bat-mah", "5000"); set("bat-s", "4"); calcBattery();
has("4S LiFePO4 is a 12.8 V pack", /12\.8 V nominal/);
has("charging setpoint given where it differs from resting full", /hold at 14\.60 V/);

console.log("\n== a value the user types survives, a chemistry change does not ==");
clearAll(F); chem("lipo"); set("bat-mah", "5000"); calcBattery();
set("bat-v", "3.75");                       // typing clears the computed mark
calcBattery();
eq("the typed nominal is kept", get("bat-v"), "3.75");
eq("it is treated as an input, not a fill", document.getElementById("bat-v").classList.contains("computed"), false);

console.log("\n== charge and discharge limits ==");
clearAll(F); chem("lipo"); set("bat-mah", "5000"); set("bat-s", "6"); calcBattery();
has("charge to 25.2 V", /25\.20 V pack/);
has("discharge no lower than 18 V", /18\.00 V pack/);
has("typical charge current is 1 C", /5 A at 1 C/);
clearAll(F); chem("liion"); set("bat-mah", "3000"); set("bat-p", "4"); calcBattery();
has("Li-ion charges at half a C", /6 A at 0\.5 C/);
clearAll(F); chem("lipo"); set("bat-mah", "5000"); set("bat-crate", "25"); calcBattery();
has("the rating sets the continuous limit", /125 A at the 25 C rating/);
set("bat-load", "200"); calcBattery();
has("a load over the rating is called out", /over it by/);
set("bat-load", "20"); calcBattery();
has("a load inside it reports headroom", /within it/);

console.log("\n== the curve honours the three voltages ==");
clearAll(F); chem("lipo"); set("bat-mah", "5000"); set("bat-s", "6"); calcBattery();
const lipo = curve();
near("full at 0 % drawn", atPct(lipo, 0), 25.2, 0.1);
near("nominal at 50 %", atPct(lipo, 50), 22.2, 0.1);
near("minimum at 100 %", atPct(lipo, 100), 18.0, 0.1);
let mono = true;
for (let i = 1; i < lipo.length; i++) if (lipo[i][1] > lipo[i - 1][1] + 1e-9) mono = false;
eq("it never rises", mono, true);

clearAll(F); chem("lifepo4"); set("bat-mah", "5000"); set("bat-s", "6"); calcBattery();
const lfp = curve();
near("LiFePO4 full at 0 %", atPct(lfp, 0), 20.4, 0.1);
near("LiFePO4 nominal at 50 %", atPct(lfp, 50), 19.2, 0.1);
const droop = function (p) { return atPct(p, 20) - atPct(p, 80); };
eq("the iron-phosphate plateau is flatter than the polymer slope", droop(lfp) < droop(lipo) / 2, true);

console.log("\n== a custom cell gets its own curve ==");
clearAll(F); document.getElementById("bat-chem").value = "custom";
set("bat-mah", "2000"); set("bat-vfull", "4.0"); set("bat-v", "3.5"); set("bat-vmin", "2.8"); calcBattery();
const cu = curve();
near("custom full", atPct(cu, 0), 4.0, 0.1);
near("custom nominal at half capacity", atPct(cu, 50), 3.5, 0.1);
near("custom minimum", atPct(cu, 100), 2.8, 0.1);

console.log("\n== nonsense is refused rather than drawn ==");
clearAll(F); document.getElementById("bat-chem").value = "custom";
set("bat-mah", "2000"); set("bat-vfull", "3.0"); set("bat-v", "3.5"); set("bat-vmin", "4.0"); calcBattery();
has("an inverted voltage range is called out", /nothing to discharge/);
eq("and no curve is drawn", !!MINI["bat-graph"], false);

console.log("\n== it answers with whatever it has ==");
clearAll(F); chem("lipo"); set("bat-s", "6"); calcBattery();
has("chemistry and a series count give the voltages", /6S at 22\.2 V nominal/);
has("including the working range", /Working range/);
eq("and the curve, which needs no capacity", !!MINI["bat-graph"], true);
eq("but no energy figure, having no capacity", /Energy/.test(JSON.stringify(rows("bat-out"))), false);

clearAll(F); chem("lipo"); set("bat-mah", "5000"); set("bat-p", "2"); set("bat-crate", "25"); calcBattery();
has("capacity and a parallel count give the amp-hours", /10\.00 Ah/);
has("and the currents that follow from them", /250 A at the 25 C rating/);

clearAll(F); chem("lipo"); set("bat-mah", "5000"); set("bat-load", "10"); calcBattery();
has("a load in amps needs no voltage", /C-rate/);
has("and still gives a runtime", /Runtime/);

console.log("\n" + pass + " passed, " + f + " failed");
process.exitCode = f ? 1 : 0;
