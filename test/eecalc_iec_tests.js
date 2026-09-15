// IEC 60664-1 clearance and creepage. The reference values here are the ones
// published in the standard's tables and widely quoted in safety design notes,
// so they check the transcription independently of where it came from.

let f = 0, pass = 0;
function eq(l, g, w) {
  if (String(g) === String(w)) { pass++; console.log("  ok   " + l); }
  else { f++; console.log("  FAIL " + l + ": got " + g + ", want " + w); }
}
function near(l, g, w, t) {
  if (Math.abs(g - w) <= Math.abs(w) * t / 100) { pass++; console.log("  ok   " + l + " = " + g); }
  else { f++; console.log("  FAIL " + l + ": got " + g + ", want ~" + w); }
}
function has(l, re) {
  const t = JSON.stringify(rows("iec-out"));
  if (re.test(t)) { pass++; console.log("  ok   " + l); }
  else { f++; console.log("  FAIL " + l + " in " + t.slice(0, 300)); }
}
function opt(id, v) { document.getElementById(id).value = v; }
function run(o) {
  clearAll(["iec-vrms", "iec-vpeak", "iec-vmains", "iec-alt"]);
  opt("iec-ins", o.ins || "basic");
  opt("iec-ovc", String(o.ovc || 2));
  opt("iec-pd", String(o.pd || 2));
  opt("iec-mg", String(o.mg || 2));
  opt("iec-pcb", o.pcb === false ? "0" : "1");
  opt("iec-field", o.field || "inhomogeneous");
  if (o.vrms !== undefined) set("iec-vrms", String(o.vrms));
  if (o.vmains !== undefined) set("iec-vmains", String(o.vmains));
  if (o.alt !== undefined) set("iec-alt", String(o.alt));
  calcIEC();
}

console.log("\n== rated impulse withstand, Table F.1 ==");
/* The four values everyone knows for 230 V mains */
eq("230 V OVC I", iecRatedImpulse(230, 1), 1500);
eq("230 V OVC II", iecRatedImpulse(230, 2), 2500);
eq("230 V OVC III", iecRatedImpulse(230, 3), 4000);
eq("230 V OVC IV", iecRatedImpulse(230, 4), 6000);
eq("120 V OVC II", iecRatedImpulse(120, 2), 1500);
eq("400 V OVC III", iecRatedImpulse(400, 3), 6000);
/* monotonic in both arguments */
let mono = true;
[50, 100, 150, 300, 600, 1000].forEach(function (v) {
  for (let c = 1; c < 4; c++) if (iecRatedImpulse(v, c + 1) < iecRatedImpulse(v, c)) mono = false;
});
eq("a higher category never asks for less", mono, true);

console.log("\n== clearance, Table F.2 ==");
eq("2.5 kV PD2 inhomogeneous is 1.5 mm", iecClearanceTransient(2.5, 2, "inhomogeneous"), 1.5);
eq("4 kV PD2 inhomogeneous is 3 mm", iecClearanceTransient(4, 2, "inhomogeneous"), 3);
eq("1.5 kV PD2 inhomogeneous is 0.5 mm", iecClearanceTransient(1.5, 2, "inhomogeneous"), 0.5);
eq("6 kV PD2 inhomogeneous is 5.5 mm", iecClearanceTransient(6, 2, "inhomogeneous"), 5.5);
/* a homogeneous field always allows less, never more */
let homOk = true;
[1.5, 2.5, 4, 6, 8].forEach(function (v) {
  if (iecClearanceTransient(v, 2, "homogeneous") > iecClearanceTransient(v, 2, "inhomogeneous")) homOk = false;
});
eq("a homogeneous field never needs more clearance", homOk, true);

console.log("\n== creepage, Table F.5 ==");
eq("250 V PD2 MG II on a board is 1.0 mm", iecBasicCreepage(250, 2, 2, true), 1.0);
eq("250 V PD2 MG II elsewhere is 1.8 mm", iecBasicCreepage(250, 2, 2, false), 1.8);
eq("250 V PD1 on a board is 0.56 mm", iecBasicCreepage(250, 1, 2, true), 0.56);
/* a worse material group never allows a shorter path */
let mgOk = true;
[100, 250, 400, 1000].forEach(function (v) {
  for (let g = 1; g < 3; g++) {
    if (iecBasicCreepage(v, 3, g + 1, false) < iecBasicCreepage(v, 3, g, false)) mgOk = false;
  }
});
eq("a worse material group never needs less creepage", mgOk, true);
/* and a worse pollution degree never allows a shorter path */
let pdOk = true;
[100, 250, 630].forEach(function (v) {
  if (iecBasicCreepage(v, 3, 2, false) < iecBasicCreepage(v, 2, 2, false)) pdOk = false;
});
eq("a worse pollution degree never needs less creepage", pdOk, true);

console.log("\n== altitude, Table A.2 ==");
eq("sea level is unity", iecAltitudeFactor(0), 1.0);
eq("2000 m is still unity", iecAltitudeFactor(2000), 1.0);
eq("3000 m is 1.14", iecAltitudeFactor(3000), 1.14);
eq("5000 m is 1.48", iecAltitudeFactor(5000), 1.48);

console.log("\n== the card, end to end ==");
run({ vrms: 230, vmains: 230 });
has("230 V mains gives a 2.5 kV impulse", /"2\.50 kV"/);
has("and 1.5 mm of clearance", /"Clearance","1\.50 mm"/);

run({ vrms: 230, vmains: 230, ins: "reinforced" });
has("reinforced doubles up to 3 mm", /"Clearance","3\.00 mm"/);
has("and says it stepped the series", /next step up the preferred series/);

run({ vrms: 230, vmains: 230, pd: 3 });
has("pollution degree 3 needs 3.6 mm of creepage", /"Creepage","3\.60 mm"/);

run({ vrms: 230, vmains: 230, alt: 4000 });
has("4000 m scales the clearance by 1.29", /multiplied by 1\.29/);
has("and the clearance grows to 1.94 mm", /"Clearance","1\.94 mm"/);

console.log("\n== creepage can never be shorter than clearance ==");
let floorOk = true;
[[60, 60], [230, 230], [400, 400]].forEach(function (c) {
  run({ vrms: c[0], vmains: c[1] });
  const r = rows("iec-out");
  const cl = parseFloat(r.find(function (q) { return q[0] === "Clearance"; })[1]);
  const cr = parseFloat(r.find(function (q) { return q[0] === "Creepage"; })[1]);
  if (cr < cl - 1e-9) floorOk = false;
});
eq("the surface path is never shorter than the air path", floorOk, true);

console.log("\n== a low-voltage pack still has requirements ==");
run({ vrms: 50, vmains: 50, pd: 2, mg: 3, pcb: false });
has("50 V is not exempt", /"Creepage"/);

console.log("\n" + pass + " passed, " + f + " failed");
process.exitCode = f ? 1 : 0;
