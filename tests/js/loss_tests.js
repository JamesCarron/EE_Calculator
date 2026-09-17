// Transmission-line loss: conductor loss with roughness, dielectric loss from
// the loss tangent, and the physical trends both must follow.

let f = 0, pass = 0;
function eq(l, g, w) {
  if (String(g) === String(w)) { pass++; console.log("  ok   " + l); }
  else { f++; console.log("  FAIL " + l + ": got " + g + ", want " + w); }
}
function near(l, g, w, t) {
  if (Math.abs(g - w) <= Math.abs(w) * t / 100) { pass++; console.log("  ok   " + l + " = " + Number(g.toPrecision(6))); }
  else { f++; console.log("  FAIL " + l + ": got " + g + ", want ~" + w); }
}

console.log("\n== skin depth ==");
/* copper at 1 GHz is 2.09 um, and it falls as 1/sqrt(f) */
near("copper at 1 GHz", skinDepth(1e9) * 1e6, 2.09, 1);
near("copper at 100 MHz", skinDepth(1e8) * 1e6, 6.6, 1);
near("ten times the frequency is 1/sqrt(10) the depth",
     skinDepth(1e10), skinDepth(1e9) / Math.sqrt(10), 0.01);

console.log("\n== a 50 ohm FR-4 microstrip at 1 GHz ==");
/* the widely quoted figure is about 0.2 dB per inch total */
const ls = tlineLoss(1e9, 50, 0.3, 4.3, 3.3, 0.02, 0.4);
near("conductor loss near 0.11 dB/in", ls.ac * 0.0254, 0.115, 25);
near("dielectric loss near 0.075 dB/in", ls.ad * 0.0254, 0.075, 25);
near("total near 0.19 dB/in", ls.total * 0.0254, 0.19, 20);

console.log("\n== the trends have to be right ==");
/* conductor loss goes as sqrt(f), dielectric loss goes as f */
const a = tlineLoss(1e9, 50, 0.3, 4.3, 3.3, 0.02, 0);
const b = tlineLoss(4e9, 50, 0.3, 4.3, 3.3, 0.02, 0);
near("conductor loss quadruples in frequency as a doubling", b.ac / a.ac, 2, 1);
near("dielectric loss is linear in frequency", b.ad / a.ad, 4, 1);
eq("so dielectric loss overtakes conductor loss eventually",
   tlineLoss(4e10, 50, 0.3, 4.3, 3.3, 0.02, 0).ad >
   tlineLoss(4e10, 50, 0.3, 4.3, 3.3, 0.02, 0).ac, true);

const wide = tlineLoss(1e9, 50, 1.2, 4.3, 3.3, 0.02, 0);
eq("a wider trace loses less in the conductor", wide.ac < a.ac, true);
eq("but the dielectric does not care about width", Math.abs(wide.ad - a.ad) < 1e-9, true);

console.log("\n== roughness ==");
const smooth = tlineLoss(1e9, 50, 0.3, 4.3, 3.3, 0.02, 0);
const rough = tlineLoss(1e9, 50, 0.3, 4.3, 3.3, 0.02, 2.0);
eq("rough copper loses more", rough.ac > smooth.ac, true);
eq("and the correction is bounded by 2", rough.kr <= 2 && rough.kr > 1, true);
eq("smooth copper has no correction", smooth.kr, 1);
/* the correction saturates: it depends on roughness against skin depth, so it
   matters most where the skin is thin */
eq("roughness bites harder at high frequency",
   tlineLoss(1e10, 50, 0.3, 4.3, 3.3, 0.02, 2.0).kr >
   tlineLoss(1e8, 50, 0.3, 4.3, 3.3, 0.02, 2.0).kr, true);

console.log("\n== a lossless dielectric has no dielectric loss ==");
eq("tan delta of zero", tlineLoss(1e9, 50, 0.3, 4.3, 3.3, 0, 0).ad, 0);
/* stripline: eeff collapses to er and the expression reduces to sqrt(er) */
const sl = tlineLoss(1e9, 50, 0.3, 4.3, 4.3, 0.02, 0);
near("stripline dielectric loss is 27.3*sqrt(er)*tand/lambda0",
     sl.ad, 27.3 * Math.sqrt(4.3) * 0.02 / (299792458 / 1e9), 0.01);

console.log("\n== the card reports it ==");
clearAll(["z-w", "z-h", "z-er", "z-f", "z-tand", "z-rough"]);
document.getElementById("z-struct").value = "ms";
set("z-w", "0.3"); set("z-h", "0.2"); set("z-er", "4.3"); set("z-f", "1G");
calcZ();
const t = JSON.stringify(rows("z-out"));
eq("loss appears once a frequency is given", /Conductor loss/.test(t), true);
eq("with the dielectric term too", /Dielectric loss/.test(t), true);
eq("and a length for 1 dB", /for 1 dB/.test(t), true);
eq("and it says the conductor figure is a floor", /treat the total as a floor/.test(t), true);

clearAll(["z-w", "z-h", "z-er", "z-f", "z-tand", "z-rough"]);
set("z-w", "0.3"); set("z-h", "0.2"); set("z-er", "4.3");
calcZ();
eq("no frequency, no loss figures", /Conductor loss/.test(JSON.stringify(rows("z-out"))), false);

console.log("\n" + pass + " passed, " + f + " failed");
process.exitCode = f ? 1 : 0;
