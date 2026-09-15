// Attenuator pads: five topologies, unequal impedances, and the identity that
// an exactly-valued pad delivers exactly its design attenuation.

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
  const t = JSON.stringify(rows("pad-out"));
  if (re.test(t)) { pass++; console.log("  ok   " + l); }
  else { f++; console.log("  FAIL " + l + " in " + t.slice(0, 400)); }
}
const F = ["pad-a", "pad-zin", "pad-zout"];
function setup(topo, a, zin, zout) {
  document.getElementById("pad-topo").value = topo;
  clearAll(F);
  if (a !== undefined) set("pad-a", String(a));
  if (zin !== undefined) set("pad-zin", String(zin));
  if (zout !== undefined) set("pad-zout", String(zout));
  calcPad();
}

console.log("\n== the design identity: exact parts give exactly the design figure ==");
/* This is the check that catches a wrong formula. It must hold for every
   topology, at several attenuations, and with unequal impedances. */
/* The L pad is excluded here on purpose: its attenuation is not a design
   input, so there is no "design figure" for it to return. It is tested
   against its own fixed loss below. */
[["pi", 50, 50], ["t", 50, 50], ["pi", 50, 75], ["t", 75, 50],
 ["pi", 50, 200], ["t", 200, 50], ["bridge", 50, 50]].forEach(function (c) {
  [3, 6, 10, 20, 40].forEach(function (a) {
    const zin = c[1], zout = c[2];
    const floor = padMinLoss(zin, zout);
    if (a < floor) return;                       // not designable, tested separately
    const d = padDesign(c[0], a, zin, zout);
    const got = padLoss(c[0], d, zin, c[0] === "bridge" ? zin : zout);
    near(c[0] + " " + zin + "->" + zout + " at " + a + " dB", got, a, 0.01);
  });
});

console.log("\n== the general form reduces to the symmetric one ==");
/* With equal impedances the PI and T values must equal the textbook
   expressions in K = 10^(A/20). */
[3, 6, 20].forEach(function (a) {
  const K = Math.pow(10, a / 20), z = 50;
  const pi = padDesign("pi", a, z, z), t = padDesign("t", a, z, z);
  near("PI series at " + a + " dB", pi.ser, z * (K * K - 1) / (2 * K), 0.001);
  near("PI shunt at " + a + " dB", pi.sh1, z * (K + 1) / (K - 1), 0.001);
  near("T series at " + a + " dB", t.se1, z * (K - 1) / (K + 1), 0.001);
  near("T shunt at " + a + " dB", t.sh, 2 * K * z / (K * K - 1), 0.001);
  eq("PI is symmetric when the impedances are", Math.abs(pi.sh1 - pi.sh2) < 1e-9, true);
  eq("T is symmetric when the impedances are", Math.abs(t.se1 - t.se2) < 1e-9, true);
});

console.log("\n== unequal impedances make the pad asymmetric ==");
const pu = padDesign("pi", 10, 50, 75);
eq("the two PI shunt legs differ", pu.sh1 !== pu.sh2, true);
eq("the leg on the higher impedance is the larger", pu.sh2 > pu.sh1, true);
const tu = padDesign("t", 10, 50, 75);
eq("the two T series arms differ", tu.se1 !== tu.se2, true);

console.log("\n== minimum attenuation between unequal impedances ==");
near("50 to 75 needs 5.72 dB", padMinLoss(50, 75), 5.7191, 0.1);
near("it does not care which way round", padMinLoss(75, 50), padMinLoss(50, 75), 0.001);
eq("equal impedances have no floor", padMinLoss(50, 50), 0);
/* the two published forms of the limit agree */
[1.5, 2, 4, 10].forEach(function (r) {
  near("the power form matches the voltage form at r=" + r,
       padMinLoss(50 * r, 50), 20 * Math.log10(Math.sqrt(r) + Math.sqrt(r - 1)), 0.001);
});
setup("pi", 3, 50, 200);
has("asking below the floor is refused", /No resistive pad can match both ends/);
has("and the floor is quoted", /Minimum attenuation/);

console.log("\n== bridged T ==");
setup("bridge", 6, 50, 50);
has("its series arms are Z0", /equal to Z/);
const br = padDesign("bridge", 6, 50, 50);
const Kb = Math.pow(10, 6 / 20);
near("bridging arm is Z(K-1)", br.bridge, 50 * (Kb - 1), 0.001);
near("shunt is Z/(K-1)", br.sh, 50 / (Kb - 1), 0.001);
eq("the product of the two is Z squared", Math.abs(br.bridge * br.sh - 2500) < 1e-6, true);

console.log("\n== resistive splitter ==");
setup("split", undefined, 50, 50);
has("each arm is a third of Z0", /16\.67 Ω|16\.7 Ω/);
has("6 dB per output", /6\.02 dB/);
has("its poor isolation is called out", /Isolation between outputs/);
near("splitter arm value", padDesign("split", 6, 50, 50).arm, 50 / 3, 0.001);

console.log("\n== stock values are checked by real transducer loss ==");
setup("pi", 6, 50, 50);
has("a nearest-E-series row is given", /Nearest E/);
has("with what those parts actually deliver", /Those parts give/);
setup("pi", 6, 50, 75);
has("and it still reports for unequal impedances", /Those parts give/);

console.log("\n== the L pad's attenuation is not a free choice ==");
/* A matched L pad has one geometry and therefore one loss - the minimum its
   impedance ratio allows. Asking for more does not change it, which the card
   must say rather than silently ignoring the number, as it used to. */
[[75, 50], [100, 50], [50, 12.5]].forEach(function (c) {
  const d = padDesign("l", 0, c[0], c[1]);
  near("L pad " + c[0] + " to " + c[1] + " delivers its minimum loss",
       padLoss("l", d, c[0], c[1]), padMinLoss(c[0], c[1]), 0.01);
});
setup("l", 30, 75, 50);
has("the attenuation is reported as fixed", /fixed by the impedance ratio/);
has("the 30 dB asked for is not honoured", /5\.72 dB/);
setup("l", 6, 50, 50);
has("equal impedances are refused", /nothing to match/);
setup("l", 10, 75, 50);
has("series on the high side", /Series, on the 75/);
has("shunt across the low side", /Shunt, across the 50/);

console.log("\n" + pass + " passed, " + f + " failed");
process.exitCode = f ? 1 : 0;
