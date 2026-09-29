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

console.log("\n== tolerance is its own input, not implied by the E-series ==");
/* The point of separating them: an E96 grid with 5 % parts is a real thing to
   buy, and the old card could not say it. */
function padSet(topo, a, zin, zout, tol, p) {
  clearAll(["pad-a", "pad-zin", "pad-zout", "pad-tol", "pad-p"]);
  document.getElementById("pad-topo").value = topo;
  document.getElementById("pad-series").value = "E96";
  set("pad-a", String(a)); set("pad-zin", String(zin)); set("pad-zout", String(zout));
  if (tol !== undefined) set("pad-tol", String(tol));
  if (p !== undefined) set("pad-p", String(p));
  calcPad();
}
function padRow(name) {
  const r = rows("pad-out").filter(function (x) { return x[0] === name; });
  return r.length ? r[r.length - 1][1] : "";
}
/* fmt writes engineering notation, so "522.5 mW" has to come back as 0.5225 -
   comparing the printed number alone would pass a milliwatt off as a watt */
const SI = { p: 1e-12, n: 1e-9, "\u00b5": 1e-6, u: 1e-6, m: 1e-3, k: 1e3, M: 1e6, G: 1e9 };
function padNum(name, i) {
  const m = padRow(name).split("\u2026");
  if (m.length <= i) return NaN;
  const t = m[i].trim();
  const v = parseFloat(t);
  const pre = (t.match(/[0-9.]\s*([pn\u00b5umkMG])W/) || [])[1];
  return pre ? v * SI[pre] : v;
}

padSet("pi", 10, 50, 50, 1);
/* interior value: the nominal E96 pi pad is 71.5 / 95.3 / 95.3, and evaluating
   all eight corners at +/-1 % gives 9.9765 and 10.1581 dB */
has("the spread is reported at the tolerance asked for", /Attenuation at \u00b11\.00 %/);
near("the low corner", padNum("Attenuation at \u00b11.00 %", 0), 9.98, 0.05);
near("the nominal sits between them", padNum("Attenuation at \u00b11.00 %", 1), 10.07, 0.05);
near("the high corner", padNum("Attenuation at \u00b11.00 %", 2), 10.16, 0.05);

/* monotonicity: a looser part can only widen the window, never narrow it */
const w1 = (function () { padSet("pi", 10, 50, 50, 1); return padNum("Attenuation at \u00b11.00 %", 2) - padNum("Attenuation at \u00b11.00 %", 0); })();
const w5 = (function () { padSet("pi", 10, 50, 50, 5); return padNum("Attenuation at \u00b15.00 %", 2) - padNum("Attenuation at \u00b15.00 %", 0); })();
eq("5 % parts give a wider window than 1 %", w5 > w1 * 3, true);

/* identity: zero tolerance is a point, so there is no window to report */
padSet("pi", 10, 50, 50, 0);
eq("perfect parts get no spread row", padRow("Spread"), "");
has("but the stock-value row survives", /Those parts give/);

/* the grid and the tolerance are independent: same E96 values either way */
padSet("pi", 10, 50, 50, 1);
const at1 = padRow("Nearest E96");
padSet("pi", 10, 50, 50, 10);
eq("changing tolerance does not move the values", padRow("Nearest E96"), at1);
has("only the window it implies", /Attenuation at \u00b110\.0 %/);

console.log("\n== the power budget accounts for every watt ==");
/* identity, and the check that carries the most weight here: the legs plus the
   load must equal what was put in, or the node solution is wrong somewhere. */
padSet("pi", 10, 50, 50, 1, 1);
near("shunt on the source side takes the most", padNum("Shunt, source side", 1), 0.5225, 0.2);
near("the series element next", padNum("Series", 1), 0.3273, 0.2);
near("the load-side shunt least", padNum("Shunt, load side", 1), 0.05166, 0.2);
near("and the load gets the rest", padNum("Delivered to the load", 1), 0.09847, 0.2);
near("which all adds to the 1 W entered",
     padNum("Shunt, source side", 1) + padNum("Series", 1) + padNum("Shunt, load side", 1)
     + padNum("Delivered to the load", 1), 1, 0.2);

/* identity: the delivered power is pinned by the attenuation the stock parts
   actually give. Comparing against the 10 dB asked for instead would be loose
   by the E96 snap - the pi pad lands on 10.07 dB, which is 1.5 % of the power. */
["pi", "t", "bridge"].forEach(function (topo) {
  padSet(topo, 10, 50, 50, 0, 1);
  const got = parseFloat(padRow("Those parts give"));
  near(topo + " delivers exactly what its loss says",
       padNum("Delivered to the load", 1), Math.pow(10, -got / 10), 0.2);
});

/* monotonicity: more attenuation burns more in the pad and delivers less */
padSet("pi", 3, 50, 50, 0, 1);
const d3 = padNum("Delivered to the load", 1);
padSet("pi", 20, 50, 50, 0, 1);
const d20 = padNum("Delivered to the load", 1);
eq("a 20 dB pad delivers far less than a 3 dB one", d20 < d3 / 10, true);

/* the legs really do spread, and the minimum can never exceed the nominal */
padSet("pi", 10, 50, 50, 5, 1);
eq("each leg's minimum is at or below its nominal",
   padNum("Shunt, source side", 0) <= padNum("Shunt, source side", 1)
   && padNum("Series", 0) <= padNum("Series", 1), true);
eq("and its maximum at or above",
   padNum("Shunt, source side", 2) >= padNum("Shunt, source side", 1)
   && padNum("Series", 2) >= padNum("Series", 1), true);
has("the note says the corners are per leg", /size every part for its own maximum/);

console.log("\n== power is optional and scales linearly ==");
padSet("pi", 10, 50, 50, 1);
eq("no power in, no power rows", padRow("Delivered to the load"), "");
padSet("pi", 10, 50, 50, 0, 1);
const p1 = padNum("Series", 1);
padSet("pi", 10, 50, 50, 0, 2);
near("doubling the input doubles every leg", padNum("Series", 1), p1 * 2, 0.1);

console.log("\n== every topology carries a leg for every physical part ==");
/* The bridged T has four resistors and the splitter three, and each is a
   separate part with its own tolerance - which is the whole reason the
   branches were split apart. */
padSet("bridge", 10, 50, 50, 1, 1);
eq("the bridged T lists four legs",
   rows("pad-out").filter(function (r) { return /^(Series arm|Bridging|Shunt)/.test(r[0]); }).length >= 4, true);
padSet("split", 6, 50, 50, 1, 1);
eq("the splitter lists three arms",
   rows("pad-out").filter(function (r) { return /^Arm, /.test(r[0]); }).length >= 3, true);
/* the splitter's two outputs are symmetric, so their arms must dissipate
   the same to within the E96 rounding of the external termination */
near("its two output arms dissipate alike",
     padNum("Arm, output 1", 1), padNum("Arm, output 2", 1), 2);

console.log("\n" + pass + " passed, " + f + " failed");
process.exitCode = f ? 1 : 0;
