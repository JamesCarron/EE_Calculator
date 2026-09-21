/* S11 to impedance.

   Written 2026-09-21. Every expectation was computed independently in Python
   before being written here, not captured from the card's own output.

   The check that carries the most weight is the one for the phase-less case.
   The obvious implementation returns Z0*(1+p)/(1-p) and looks right, because
   it agrees with every published magnitude-only calculator - and it is wrong,
   because |S11| fixes a circle rather than a point. The test pins the circle. */

let f = 0, pass = 0;
function eq(l, g, w) { if (String(g) === String(w)) { pass++; console.log("  ok   " + l); } else { f++; console.log("  FAIL " + l + ": got " + g + " want " + w); } }
function has(l, id, re) { const t = JSON.stringify(rows(id)); if (re.test(t)) { pass++; console.log("  ok   " + l); } else { f++; console.log("  FAIL " + l + " in " + t); } }
function no(l, id, re) { const t = JSON.stringify(rows(id)); if (!re.test(t)) { pass++; console.log("  ok   " + l); } else { f++; console.log("  FAIL " + l + " in " + t); } }

const S = ["s11-z0", "s11-db", "s11-lin", "s11-ph", "s11-f"];

console.log("\n== Scalar figures, which the magnitude does fix ==");
/* -20 dB: rho 0.1, VSWR 1.2222, 1 % reflected, mismatch loss 0.0436 dB */
clearAll(S); set("s11-db", "-20"); calcS11();
has("-20 dB is a linear 0.1", "s11-out", /0\.1000 = -20\.00 dB/);
has("return loss is the positive of it", "s11-out", /20\.00 dB/);
has("VSWR 1.2222", "s11-out", /1\.2222 : 1/);
has("1 % of the power comes back", "s11-out", /1\.00 %/);
has("mismatch loss 0.044 dB", "s11-out", /0\.04[34] dB/);
eq("the linear box is filled in", Math.abs(val("s11-lin") - 0.1) < 1e-6, true);

/* the pair mirrors both ways */
clearAll(S); set("s11-lin", "0.1"); calcS11();
has("entering the linear value gives the same VSWR", "s11-out", /1\.2222 : 1/);
eq("and the dB box is filled in", Math.abs(val("s11-db") + 20) < 1e-3, true);

console.log("\n== Magnitude alone does not give an impedance ==");
clearAll(S); set("s11-db", "-20"); calcS11();
has("the card says so outright", "s11-out", /Not determined by the magnitude alone/);
has("circle centred on 51.01 ohms", "s11-out", /51\.01 /);
has("of radius 10.1 ohms", "s11-out", /10\.1 /);
has("both real-axis crossings are given", "s11-out", /40\.91 .*61\.11 /);
has("and the reactance bound", "s11-out", /anything up to/);
no("it never claims a single impedance", "s11-out", /"Impedance","[0-9]/);

console.log("\n== With the phase the impedance is determined ==");
/* -20 dB at -35 deg: G = 0.08192 - 0.05736j, Z = 58.499 - 6.7785j */
clearAll(S); set("s11-db", "-20"); set("s11-ph", "-35"); calcS11();
has("gamma in rectangular form", "s11-out", /0\.081[89]\d* - 0\.057[34]\d*j/);
has("Z = 58.5 - j6.779 ohm, written as one quantity", "s11-out", /58\.5 − j6\.77[89] /);
has("polar form 58.89 ohms at -6.61 deg", "s11-out", /58\.89 .*-6\.61/);
no("and the circle language is gone", "s11-out", /Not determined by the magnitude/);

/* a purely reactive-looking case: -10 dB at +90 deg is 40.909 + 28.748j */
clearAll(S); set("s11-db", "-10"); set("s11-ph", "90"); calcS11();
has("-10 dB at 90 deg is 40.91 + j28.75", "s11-out", /40\.91 \+ j28\.7[45] /);
has("VSWR 1.925", "s11-out", /1\.9250 : 1/);
has("10 % of the power reflected", "s11-out", /10\.0 %/);

console.log("\n== The reactance as a part you could fit ==");
/* X = +28.748 at 2.4 GHz is 1.906 nH; the mirror case is 2.307 pF */
clearAll(S); set("s11-db", "-10"); set("s11-ph", "90"); set("s11-f", "2.4G"); calcS11();
has("positive reactance is an inductance", "s11-out", /1\.90[56] nH/);
clearAll(S); set("s11-db", "-10"); set("s11-ph", "-90"); set("s11-f", "2.4G"); calcS11();
has("negative reactance is a capacitance", "s11-out", /2\.30[67] pF/);
clearAll(S); set("s11-db", "-10"); set("s11-ph", "90"); calcS11();
has("without a frequency it offers the conversion", "s11-out", /Give a frequency/);

console.log("\n== The reference impedance is a real parameter ==");
clearAll(S); set("s11-db", "-20"); set("s11-z0", "75"); calcS11();
has("75 ohm system scales the crossings", "s11-out", /61\.36 .*91\.67 /);
has("but the VSWR is unchanged", "s11-out", /1\.2222 : 1/);

console.log("\n== Edges: match, open, and more out than in ==");
clearAll(S); set("s11-lin", "0"); calcS11();
has("zero reflection is a perfect match", "s11-out", /Perfect/);
has("and VSWR is exactly 1", "s11-out", /1\.000 : 1/);
clearAll(S); set("s11-lin", "1"); set("s11-ph", "0"); calcS11();
has("gamma of 1 at 0 deg is an open", "s11-out", /open circuit|edge of the Smith chart/);
clearAll(S); set("s11-db", "3"); calcS11();
has("more power back than sent is flagged", "s11-out", /passive load cannot/);
no("and no impedance is invented for it", "s11-out", /circle centred/);

console.log("\n== Refusals and the empty card ==");
clearAll(S); calcS11();
eq("an untouched card is blank", document.getElementById("s11-out").innerHTML, "");
clearAll(S); set("s11-db", "-20"); calcS11();
no("never reports NaN", "s11-out", /NaN|Infinity/);
has("the model row names the reference plane", "s11-out", /de-embed/);

console.log("\n" + pass + " passed, " + f + " failed");
process.exitCode = f ? 1 : 0;
