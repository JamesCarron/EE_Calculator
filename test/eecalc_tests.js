// Functional tests for the reworked EE_Calculator page logic.
require("./harness.js");

let fails = 0;
function eq(label, got, want) {
  const ok = String(got) === String(want);
  if (!ok) { fails++; console.log("  FAIL " + label + ": got " + got + ", want " + want); }
  else console.log("  ok   " + label + " = " + got);
}
function near(label, got, want, tolPc) {
  const ok = Math.abs(got - want) <= Math.abs(want) * (tolPc / 100);
  if (!ok) { fails++; console.log("  FAIL " + label + ": got " + got + ", want ~" + want); }
  else console.log("  ok   " + label + " = " + got);
}

const DIV = ["div-vin","div-vout","div-r1","div-r2","div-rtot","div-iload"];
const OHM = ["ohm-v","ohm-i","ohm-r","ohm-p"];

console.log("\n== Ohm's law fills the two empty boxes ==");
clearAll(OHM); set("ohm-v", "12"); set("ohm-r", "4k7"); calcOhm();
eq("I box", get("ohm-i"), "2.5532m"); eq("I is calculated", isCalc("ohm-i"), true);
eq("P box", get("ohm-p"), "30.638m"); eq("V untouched", isCalc("ohm-v"), false);
eq("no duplicate result rows", rows("ohm-out").length, 0);

console.log("\n== stale computed values are cleared, not reused ==");
set("ohm-r", "");                       // user empties R; I and P were computed
calcOhm();
eq("I cleared", get("ohm-i"), ""); eq("P cleared", get("ohm-p"), "");

console.log("\n== divider: solve R2 into its box ==");
clearAll(DIV); set("div-vin","12"); set("div-vout","3.3"); set("div-r1","10k"); set("div-iload","100u");
calcDivider();
eq("R2 box", get("div-r2"), "4.2857k"); eq("R2 calculated", isCalc("div-r2"), true);
eq("total also filled", isCalc("div-rtot"), true);
near("total value", parseVal(get("div-rtot")), 14285.7, 0.1);
const dr = rows("div-out").map(function (r) { return r[0]; });
eq("no 'Exact R2' row left", dr.indexOf("Exact R2"), -1);
console.log("  rows:", JSON.stringify(rows("div-out")));

console.log("\n== divider: solve Vin ==");
clearAll(DIV); set("div-vout","3.3"); set("div-r1","10k"); set("div-r2","4.3k"); set("div-iload","100u");
calcDivider();
near("Vin box", parseVal(get("div-vin")), 11.974, 0.1); eq("Vin calculated", isCalc("div-vin"), true);

console.log("\n== divider: leg from total ==");
clearAll(DIV); set("div-vin","12"); set("div-r1","72.5k"); set("div-rtot","100k");
calcDivider();
eq("R2 from total", get("div-r2"), "27.5k");
near("Vout solved", parseVal(get("div-vout")), 3.3, 0.5);

console.log("\n== divider: two voltages + total -> both legs ==");
clearAll(DIV); set("div-vin","12"); set("div-vout","3.3"); set("div-rtot","100k");
calcDivider();
eq("R1", get("div-r1"), "72.5k"); eq("R2", get("div-r2"), "27.5k");

console.log("\n== divider: pair search still runs on two voltages alone ==");
clearAll(DIV); set("div-vin","12"); set("div-vout","3.3");
calcDivider();
eq("table shown", document.getElementById("div-table").hidden, false);
console.log("  first pair row:", document.getElementById("div-body").innerHTML.split("</tr>")[0]);

console.log("\n== combined filter card fills the third box ==");
document.getElementById("flt-type").value="rc";
clearAll(["flt-r","flt-c","flt-l","flt-f"]); set("flt-r","10k"); set("flt-c","100n"); calcFilter();
near("fc", parseVal(get("flt-f")), 159.15, 0.1); eq("fc calculated", isCalc("flt-f"), true);
clearAll(["flt-r","flt-c","flt-l","flt-f"]); set("flt-r","10k"); set("flt-f","1k"); calcFilter();
near("C solved", parseVal(get("flt-c")), 15.915e-9, 0.1);

console.log("\n== LED solves both directions ==");
clearAll(["led-vs","led-vf","led-if","led-r"]);
set("led-vs","5"); set("led-vf","2.1"); set("led-if","10m"); calcLED();
eq("R box", get("led-r"), "290");
clearAll(["led-vs","led-vf","led-if","led-r"]);
set("led-vs","5"); set("led-vf","2.1"); set("led-r","330"); calcLED();
near("If from R", parseVal(get("led-if")), 8.7879e-3, 0.1);

console.log("\n== crystal ==");
clearAll(["xc-cl","xc-c1","xc-c2","xc-cs"]); set("xc-cl","12p"); calcXtal();
eq("C1", get("xc-c1"), "18p"); eq("C2", get("xc-c2"), "18p");
clearAll(["xc-cl","xc-c1","xc-c2","xc-cs"]); set("xc-c1","18p"); set("xc-c2","18p"); calcXtal();
eq("CL solved", get("xc-cl"), "12p");

console.log("\n== ppm ==");
clearAll(["pp-f","pp-ppm","pp-df"]); set("pp-f","16M"); set("pp-ppm","20"); calcPPM();
eq("df box", get("pp-df"), "320");
clearAll(["pp-f","pp-ppm","pp-df"]); set("pp-f","16M"); set("pp-df","320"); calcPPM();
eq("ppm box", get("pp-ppm"), "20");

console.log("\n== trace width ==");
clearAll(["tw-i","tw-w","tw-len"]); set("tw-i","3"); calcTrace();
near("width mm", parseFloat(get("tw-w")), 1.367, 1);
clearAll(["tw-i","tw-w","tw-len"]); set("tw-w","1"); calcTrace();
near("current", parseVal(get("tw-i")), 2.392, 1);

console.log("\n== accuracy ==");
const AC = ["ac-r1","ac-r2","ac-vin","ac-tol1","ac-tol2","ac-tcr1","ac-tcr2","ac-tmin","ac-tmax","ac-tnom","ac-age"];
clearAll(AC);
set("ac-r1","10k"); set("ac-r2","10k"); set("ac-tol1","1"); set("ac-tol2","1");
set("ac-tcr1","0"); set("ac-tcr2","0"); set("ac-vin","10");
calcAccuracy();
console.log("  " + JSON.stringify(rows("ac-out")));
// k = 0.5, worst case ratio error = (1-k)*(t1+t2) = 0.5*2% = 1% to first order
const wc = rows("ac-out").filter(function (r) { return r[0].indexOf("worst case") >= 0 && r[0].indexOf("Total") === 0; })[0];
console.log("  worst-case row:", JSON.stringify(wc));
// matched TCR must cancel
clearAll(AC);
set("ac-r1","10k"); set("ac-r2","10k"); set("ac-tol1","0"); set("ac-tol2","0");
set("ac-tcr1","100"); set("ac-tcr2","100"); set("ac-tmin","-40"); set("ac-tmax","85");
calcAccuracy();
const tcrRow = rows("ac-out").filter(function (r) { return r[0].indexOf("TCR contribution") === 0; })[0];
console.log("  TCR row:", JSON.stringify(tcrRow));
eq("matched TCR cancels", tcrRow[1].indexOf("0 % if the parts truly track") >= 0, true);

console.log("\n== number bases ==");
showBases(parseInt_("4096", 10), "nb-dec");
eq("hex", get("nb-hex"), "0x1000"); eq("bin", get("nb-bin"), "0b1000000000000"); eq("oct", get("nb-oct"), "0o10000");
eq("parse hex prefix", parseInt_("0xFF", 16), 255n);
eq("parse with underscores", parseInt_("1010_1010", 2), 170n);
eq("reject bad digit", parseInt_("12", 2), null);
eq("big value exact", parseInt_("18446744073709551615", 10), 18446744073709551615n);
showBases(parseInt_("-1", 10), "nb-dec");
console.log("  -1 rows:", JSON.stringify(rows("nb-out")));

console.log("\n== fmtField round-trips through parseVal ==");
[4286, 0.0000047, 1234567, 0.033, 290, 1e-11].forEach(function (v) {
  const s = fmtField(v);
  near("round-trip " + v + " -> " + s, parseVal(s), v, 0.01);
});

console.log(fails ? "\n" + fails + " FAILURES" : "\nall assertions passed");
process.exitCode = fails ? 1 : 0;
