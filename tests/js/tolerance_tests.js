// The general component tolerance budget: five component types, EIA
// dielectric decoding, and the three error sources.

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
  const t = JSON.stringify(rows("ec-out"));
  if (re.test(t)) { pass++; console.log("  ok   " + l); }
  else { f++; console.log("  FAIL " + l + " in " + t.slice(0, 500)); }
}
const A = ["ec-val", "ec-tol", "ec-tc", "ec-tmin", "ec-tmax", "ec-tnom", "ec-age", "ec-life", "ec-bias", "ec-hyst", "ec-code"];
function setType(t, diel) {
  document.getElementById("ec-type").value = t;
  if (diel) document.getElementById("ec-diel").value = diel;
  clearAll(A);
}
/* the ± figure of a named row, as a fraction */
function pctOf(label) {
  const r = rows("ec-out").find(function (q) { return new RegExp(label).test(q[0]); });
  if (!r) return NaN;
  const m = /([+-]?[\d.]+) %/.exec(String(r[1]).replace("−", "-"));
  return m ? parseFloat(m[1]) / 100 : NaN;
}
/* the downward half of a contribution; a symmetric "±x %" counts as both */
function minusOf(label) {
  const r = rows("ec-out").find(function (q) { return new RegExp(label).test(q[0]); });
  if (!r) return NaN;
  const m = /−([\d.]+) %/.exec(String(r[1])) || /±([\d.]+) %/.exec(String(r[1]));
  return m ? parseFloat(m[1]) / 100 : NaN;
}

console.log("\n== resistor: the three sources add up ==");
setType("R"); set("ec-val", "10k"); calcTolerance();
near("1 % tolerance", pctOf("Initial tolerance"), 0.01, 0.5);
near("100 ppm over the wider 65 degree leg", pctOf("^Temperature"), 0.0065, 0.5);
near("worst case is the sum", pctOf("Worst case"), 0.0165, 0.5);
near("RSS is the root sum square", pctOf("RSS$"), Math.sqrt(0.01 * 0.01 + 0.0065 * 0.0065), 0.5);
eq("RSS is never worse than worst case", pctOf("RSS$") <= pctOf("Worst case"), true);
has("the range is given in the component's own unit", /kΩ/);

/* one contribution alone: the two methods must agree exactly */
setType("R"); set("ec-val", "1k"); set("ec-tc", "0"); calcTolerance();
near("with a single term, RSS equals worst case", pctOf("RSS$"), pctOf("Worst case"), 0.01);

/* monotonic in temperature span */
setType("R"); set("ec-val", "1k"); set("ec-tmax", "85"); calcTolerance();
const narrow = pctOf("Worst case");
setType("R"); set("ec-val", "1k"); set("ec-tmax", "125"); calcTolerance();
eq("a wider temperature range can only widen the budget", pctOf("Worst case") > narrow, true);

console.log("\n== EIA codes are decoded, not looked up ==");
setType("C", "X7R"); set("ec-val", "100n"); calcTolerance();
has("X7R spans -55 to +125", /X7R over -55 to \+125/);
near("and permits 15 %", pctOf("^Temperature"), 0.15, 0.5);
setType("C", "Y5V"); set("ec-val", "100n"); calcTolerance();
has("Y5V spans -30 to +85", /Y5V over -30 to \+85/);
near("and is asymmetric: +22", pctOf("^Temperature"), 0.22, 0.5);
near("and -82", minusOf("^Temperature"), 0.82, 0.5);
has("a range outside the dielectric's is called out", /unspecified at the extremes/);
setType("C", "other"); set("ec-val", "100n"); set("ec-code", "X6T"); calcTolerance();
has("an uncommon code still decodes", /X6T over -55 to \+105/);
near("T is +22", pctOf("^Temperature"), 0.22, 0.5);
near("T is -33", minusOf("^Temperature"), 0.33, 0.5);
setType("C", "other"); set("ec-val", "100n"); set("ec-code", "Q9Z"); calcTolerance();
has("nonsense is refused with an explanation", /not an EIA class 2 code/);
setType("C", "C0G"); set("ec-val", "100p"); calcTolerance();
has("C0G is class 1, so a slope rather than a band", /ppm\/&deg;C|ppm\/°C/);
eq("and it is not warned about as a class 2 part", /bound over the dielectric/.test(JSON.stringify(rows("ec-out"))), false);

console.log("\n== capacitor ageing is per decade of hours ==");
setType("C", "X7R"); set("ec-val", "100n"); set("ec-age", "2"); set("ec-life", "1000"); calcTolerance();
eq("no loss at the 1000 h reference point", minusOf("^Ageing"), 0);
setType("C", "X7R"); set("ec-val", "100n"); set("ec-age", "2"); set("ec-life", "10000"); calcTolerance();
near("one decade past it costs one helping", minusOf("^Ageing"), 0.02, 1);
setType("C", "X7R"); set("ec-val", "100n"); set("ec-age", "2"); set("ec-life", "100000"); calcTolerance();
near("two decades cost two", minusOf("^Ageing"), 0.04, 1);
eq("ageing only ever subtracts", pctOf("^Ageing"), 0);

console.log("\n== DC bias, the term that usually dominates ==");
setType("C", "X5R"); set("ec-val", "10u"); calcTolerance();
has("its absence is flagged", /No DC bias loss entered/);
setType("C", "X5R"); set("ec-val", "10u"); set("ec-bias", "40"); calcTolerance();
near("40 % loss subtracts 40 %", minusOf("DC bias"), 0.40, 0.5);
eq("and never adds", pctOf("DC bias"), 0);

console.log("\n== a budget that eats the whole part says so ==");
setType("C", "Y5V"); set("ec-val", "10u"); set("ec-bias", "40"); calcTolerance();
has("the low end is clamped at zero", /"Worst-case range","0 to/);
has("with the reason given", /worst case leaves nothing/);

console.log("\n== crystal: everything in ppm, answer in hertz ==");
setType("X"); set("ec-val", "16M"); calcTolerance();
near("20 ppm initial", pctOf("Initial tolerance"), 20e-6, 1);
near("30 ppm over temperature", pctOf("stability"), 30e-6, 1);
near("3 ppm/year for ten years", pctOf("^Ageing"), 30e-6, 1);
near("80 ppm all told", pctOf("Worst case"), 80e-6, 1);
has("the window is whole hertz, which 4 figures cannot show", /15,998,720 to 16,001,280 Hz/);
eq("the window is symmetric about nominal", (function () {
  const r = rows("ec-out").find(function (q) { return /Worst-case window/.test(q[0]); })[1];
  const n = r.match(/[\d,]+/g).map(function (v) { return parseInt(v.replace(/,/g, ""), 10); });
  return (n[0] + n[1]) / 2;
})(), 16000000);

console.log("\n== voltage reference: drift is a random walk ==");
setType("V"); set("ec-val", "2.5"); set("ec-life", "1"); calcTolerance();
const d1 = pctOf("Long-term drift");
setType("V"); set("ec-val", "2.5"); set("ec-life", "4"); calcTolerance();
near("four times the time is twice the drift", pctOf("Long-term drift"), d1 * 2, 1);
setType("V"); set("ec-val", "2.5"); set("ec-hyst", "75"); calcTolerance();
near("thermal hysteresis is carried too", pctOf("hysteresis"), 75e-6, 1);

console.log("\n== the card shows only the fields it uses ==");
setType("R"); calcTolerance();
eq("a resistor has no dielectric", document.getElementById("ec-f-diel").hidden, true);
eq("and no bias field", document.getElementById("ec-f-bias").hidden, true);
setType("C", "X7R"); calcTolerance();
eq("a class 2 capacitor shows the dielectric", document.getElementById("ec-f-diel").hidden, false);
eq("and hides the tempco, which its code replaces", document.getElementById("ec-f-tc").hidden, true);
setType("C", "C0G"); calcTolerance();
eq("a class 1 capacitor gets the tempco back", document.getElementById("ec-f-tc").hidden, false);
setType("C", "other"); calcTolerance();
eq("choosing Other reveals the code box", document.getElementById("ec-f-code").hidden, false);
setType("V"); calcTolerance();
eq("only a reference has thermal hysteresis", document.getElementById("ec-f-hyst").hidden, false);

console.log("\n" + pass + " passed, " + f + " failed");
process.exitCode = f ? 1 : 0;
