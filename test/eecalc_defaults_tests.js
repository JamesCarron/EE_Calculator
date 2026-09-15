// A field showing a default in its placeholder must compute with that default
// from the start, not sit idle until it is filled in. The check is behavioural:
// leaving the box blank must give exactly the same answer as typing the
// placeholder value into it.

let f = 0, pass = 0;
function eq(l, g, w) {
  if (String(g) === String(w)) { pass++; console.log("  ok   " + l); }
  else { f++; console.log("  FAIL " + l + ":\n        blank -> " + g + "\n        typed -> " + w); }
}

// card, its calculator, the inputs the card needs before it will say anything,
// the results list, and the defaulted fields with the value each claims
const CASES = [
  { name: "error budget", calc: function () { calcAccuracy(); }, out: "ac-out",
    seed: { "ac-r1": "10k", "ac-r2": "10k" },
    fields: { "ac-tol1": "1", "ac-tol2": "1", "ac-tcr1": "100", "ac-tcr2": "100",
              "ac-tmin": "-40", "ac-tmax": "85", "ac-tnom": "25" },
    all: ["ac-r1", "ac-r2", "ac-vin", "ac-tol1", "ac-tol2", "ac-tcr1", "ac-tcr2", "ac-tmin", "ac-tmax", "ac-tnom", "ac-age"] },

  { name: "trace current", calc: function () { calcTrace(); }, out: "tw-out",
    seed: { "tw-i": "3" }, fields: { "tw-dt": "10", "tw-ta": "25" },
    all: ["tw-i", "tw-w", "tw-len", "tw-f", "tw-dt", "tw-ta"] },

  { name: "via", calc: function () { calcVia(); }, out: "via-out",
    seed: { "via-d": "0.3" }, fields: { "via-tp": "25", "via-h": "1.6", "via-er": "4.3", "via-dt": "10" },
    all: ["via-d", "via-tp", "via-h", "via-pad", "via-anti", "via-er", "via-i", "via-n", "via-arlimit", "via-stub", "via-dt"] },

  { name: "fusing current", calc: function () { calcFuse(); }, out: "fu-out",
    seed: { "fu-w": "1", "fu-t": "1" }, fields: { "fu-k": "1", "fu-ta": "25" },
    all: ["fu-w", "fu-t", "fu-k", "fu-ta"] },

  { name: "crystal load", calc: function () { calcXtal(); }, out: "xc-out",
    seed: { "xc-c1": "18p", "xc-c2": "18p" }, fields: { "xc-cs": "3p" },
    all: ["xc-cl", "xc-c1", "xc-c2", "xc-cs"] },

  { name: "impedance", calc: function () { calcZ(); }, out: "z-out",
    seed: { "z-w": "0.3", "z-h": "0.2" }, fields: { "z-er": "4.3" },
    all: ["z-w", "z-h", "z-er", "z-ermask", "z-c", "z-s", "z-f"] },

  { name: "effective permittivity", calc: function () { calcEreff(); }, out: "ee-out",
    seed: { "ee-w": "0.3", "ee-h": "0.2" }, fields: { "ee-er": "4.3" },
    all: ["ee-w", "ee-h", "ee-er", "ee-f"] },

  { name: "differential pair", calc: function () { calcDiff(); }, out: "dp-out",
    seed: { "dp-w": "0.2", "dp-s": "0.2", "dp-h": "0.2" }, fields: { "dp-er": "4.3" },
    all: ["dp-w", "dp-s", "dp-h", "dp-er"] },

  { name: "via shielding", calc: function () { calcViaShield(); }, out: "vs-out",
    seed: { "vs-f": "6G" }, fields: { "vs-er": "4.3" },
    all: ["vs-f", "vs-tr", "vs-er", "vs-pitch", "vs-len", "vs-d"] },

  { name: "battery", calc: function () { calcBattery(); }, out: "bat-out",
    seed: { "bat-mah": "5000" }, fields: { "bat-s": "1", "bat-p": "1", "bat-usable": "80" },
    all: ["bat-mah", "bat-s", "bat-p", "bat-load", "bat-usable", "bat-crate"] },

  { name: "PDN", calc: function () { calcPDN(); }, out: "pdn-out",
    seed: { "pdn-v": "5", "pdn-i": "2" }, fields: { "pdn-ripple": "5", "pdn-tr": "50" },
    all: ["pdn-v", "pdn-ripple", "pdn-i", "pdn-tr", "pdn-fmax"] },

  { name: "AWG wire", calc: function () { calcAWG(); }, out: "awg-out",
    seed: { "awg-n": "12", "awg-i": "10" }, fields: { "awg-temp": "20" },
    all: ["awg-n", "awg-len", "awg-i", "awg-temp", "awg-vsupply"] }
];

CASES.forEach(function (c) {
  console.log("\n== " + c.name + " ==");
  for (const id in c.fields) {
    clearAll(c.all);
    for (const k in c.seed) set(k, c.seed[k]);
    c.calc();
    const blank = JSON.stringify(rows(c.out));

    clearAll(c.all);
    for (const k in c.seed) set(k, c.seed[k]);
    set(id, c.fields[id]);
    c.calc();
    const typed = JSON.stringify(rows(c.out));

    eq(id + " blank computes as if it held " + c.fields[id], blank, typed);
  }
});

console.log("\n" + pass + " passed, " + f + " failed");
process.exitCode = f ? 1 : 0;
