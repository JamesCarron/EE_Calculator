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
const AC = ["div-r1","div-r2","div-vin","div-tol1","div-tol2","div-tcr1","div-tcr2","div-tmin","div-tmax","div-tnom","div-age"];
clearAll(AC);
set("div-r1","10k"); set("div-r2","10k"); set("div-tol1","1"); set("div-tol2","1");
set("div-tcr1","0"); set("div-tcr2","0"); set("div-vin","10");
calcAccuracy();
console.log("  " + JSON.stringify(rows("div-tol-out")));
// k = 0.5, worst case ratio error = (1-k)*(t1+t2) = 0.5*2% = 1% to first order
const wc = rows("div-tol-out").filter(function (r) { return r[0].indexOf("worst case") >= 0 && r[0].indexOf("Total") === 0; })[0];
console.log("  worst-case row:", JSON.stringify(wc));
// matched TCR must cancel
clearAll(AC);
set("div-r1","10k"); set("div-r2","10k"); set("div-tol1","0"); set("div-tol2","0");
set("div-tcr1","100"); set("div-tcr2","100"); set("div-tmin","-40"); set("div-tmax","85");
calcAccuracy();
const tcrRow = rows("div-tol-out").filter(function (r) { return r[0].indexOf("TCR contribution") === 0; })[0];
console.log("  TCR row:", JSON.stringify(tcrRow));
eq("matched TCR cancels", tcrRow[1].indexOf("0 % if the parts truly track") >= 0, true);

/* The tolerance fold lives inside the divider card and has no R1/R2/Vin of its
   own. These three cover what the merge actually bought, and what it risks. */
console.log("\n== tolerance fold inside the divider card ==");
const DIVALL = ["div-vin","div-vout","div-r1","div-r2","div-rtot","div-iload",
                "div-tol1","div-tol2","div-tcr1","div-tcr2","div-tmin","div-tmax","div-tnom","div-age"];

/* interior value: one calcDivider call fills both the solver and the fold */
clearAll(DIVALL);
set("div-vin","10"); set("div-r1","10k"); set("div-r2","10k"); calcDivider();
eq("solving also drives the fold", rows("div-tol-out").length > 0, true);
eq("the fold reads the divider's own legs",
   rows("div-tol-out").filter(function (r) { return r[0] === "Nominal ratio"; })[0][1].indexOf("0.5") === 0, true);
/* rows() strips markup, so the label reads Vout rather than V<sub>out</sub> */
eq("and picks up Vin from the divider",
   rows("div-tol-out").some(function (r) { return r[0] === "Vout nominal"; }), true);

/* the identity that made the merge worth doing: a leg the SOLVER worked out is
   costed without being retyped, because the fold reads the computed box */
clearAll(DIVALL);
set("div-vin","10"); set("div-vout","5"); set("div-r1","10k"); calcDivider();
eq("the solver filled R2", val("div-r2") > 0, true);
eq("a solved leg is costed without retyping it",
   rows("div-tol-out").filter(function (r) { return r[0] === "Nominal ratio"; })[0][1].indexOf("0.5") === 0, true);

/* and the fold must not survive its inputs: an incomplete divider clears it
   rather than leaving the previous answer on screen */
clearAll(DIVALL);
set("div-vin","10"); calcDivider();
eq("an incomplete divider leaves no stale error figures", rows("div-tol-out").length, 0);

/* Read as a regulator feedback network: Vin is the regulator output, Vout the
   feedback pin. 3.3 V from a 0.8 V reference on 31.25k/10k, 1 % 100 ppm parts
   over -40..85 C, gives a ratio error of 2.5214 % worst case; a 1 % reference
   adds directly, so the output is 3.5214 % worst case and 3.1838..3.4162 V. */
const DIVREG = ["div-vin","div-vout","div-r1","div-r2","div-rtot","div-iload",
                "div-tol1","div-tol2","div-tcr1","div-tcr2","div-tmin","div-tmax","div-tnom","div-age","div-vfbtol"];
function regRow(label) {
  return rows("div-tol-out").filter(function (r) { return r[0].indexOf(label) === 0; })[0];
}
clearAll(DIVREG);
set("div-vin","3.3"); set("div-vout","0.8"); set("div-r1","31.25k"); set("div-r2","10k");
calcDivider();
/* the reference lands on the output one for one, so worst case simply adds */
eq("reference tolerance adds to the ratio error",
   /3\.52/.test(regRow("Regulator output error — worst case")[1]), true);
eq("RSS combines them in quadrature, not linearly",
   /1\.62/.test(regRow("Regulator output error — RSS")[1]), true);
eq("the output window is reported in volts",
   /3\.18\d* V … 3\.41\d* V/.test(regRow("Regulator output window")[1]), true);

/* sign check: a worse reference can only widen the output error, and once it
   passes the divider it becomes the term that decides the answer */
const wcOf = function () { return parseFloat(regRow("Regulator output error — worst case")[1].replace(/[^0-9.]/g, "")); };
const onePct = wcOf();
set("div-vfbtol","3"); calcDivider();
eq("a worse reference widens the output error", wcOf() > onePct, true);
eq("and becomes the dominant term", /the reference/.test(regRow("Dominant term")[1]), true);
set("div-vfbtol","0.1"); calcDivider();
eq("a precision reference hands dominance back to the divider",
   /the divider/.test(regRow("Dominant term")[1]), true);

/* A tolerance on the source feeding the divider passes straight through to the
   midpoint. 12 V ±5 % through 10k/4k7 with 1 % 100 ppm parts over -40..85 C:
   ratio 2.2583 % worst case, so 7.2583 % combined, 3.5636..4.1195 V. */
clearAll(DIVREG); clearAll(["div-vintol"]);
set("div-vin","12"); set("div-r1","10k"); set("div-r2","4k7"); calcDivider();
const noSrc = regRow("Vout worst-case window")[1];
eq("with no source tolerance the window is the ratio alone",
   /3\.75\d* V … 3\.92\d* V/.test(noSrc), true);
eq("and no source breakdown row is shown", regRow("Vout error — worst case"), undefined);

set("div-vintol","5"); calcDivider();
eq("the source tolerance adds to the ratio error",
   /7\.26/.test(regRow("Vout error — worst case")[1]), true);
eq("RSS combines them in quadrature", /5\.13/.test(regRow("Vout error — RSS")[1]), true);
/* fmt trims trailing zeros, so 4.1195 prints as 4.12 rather than 4.120 */
eq("and the window widens to match",
   /3\.56\d* V … 4\.12/.test(regRow("Vout worst-case window")[1]), true);

/* It must not leak into the regulator block, where the divider's top IS the
   computed output and adding the same spread again would count it twice.
   3.3 V from 0.8 V on 31.25k/10k is ±2.52 % ratio, so ±3.52 % with a 1 %
   reference - and must stay ±3.52 % however large the source figure is. */
clearAll(DIVREG); clearAll(["div-vintol"]);
set("div-vin","3.3"); set("div-vout","0.8"); set("div-r1","31.25k"); set("div-r2","10k");
set("div-vintol","5"); calcDivider();
const regWcRow = regRow("Regulator output error — worst case")[1];
eq("the regulator rows ignore it", /±3\.52/.test(regWcRow), true);
eq("rather than adding it on top", /±8\.5/.test(regWcRow), false);
/* rows() strips markup, so the note reads Vin rather than V<sub>in</sub> */
eq("and the card says why rather than leaving it to be guessed",
   rows("div-tol-out").some(function (r) { return /ignore the Vin tolerance/.test(r[1]); }), true);

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
