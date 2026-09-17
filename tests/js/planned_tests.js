// Test vectors for the planned EE Calculator additions.
//
// Written 2026-09-10 alongside Implementation_Plan.md, BEFORE the features
// exist, so implementation can be verified the moment it lands. Every expected
// value here was produced and reference-checked by
// C:\Auterion\Tools\claude\scratch\eecalc_formula_check.py.
//
// Usage: concatenate the generated harness (eecalc_mkharness.py) with this file
// and run under node. Anything not yet built SKIPS rather than fails, so this
// can be run at any stage; a FAIL always means something is built wrongly.

let fails = 0, skips = 0, passes = 0;

function eq(label, got, want) {
  if (String(got) === String(want)) { passes++; console.log("  ok   " + label); }
  else { fails++; console.log("  FAIL " + label + ": got " + got + ", want " + want); }
}

function near(label, got, want, tolPc) {
  if (Math.abs(got - want) <= Math.abs(want) * tolPc / 100) {
    passes++; console.log("  ok   " + label + " = " + Number(got.toPrecision(6)));
  } else {
    fails++; console.log("  FAIL " + label + ": got " + got + ", want ~" + want);
  }
}

// Concatenated into one file, the page's functions are module-scoped rather
// than properties of globalThis, so probe them by evaluating the bare name.
function defined(n) {
  try { return eval("typeof " + n) === "function"; } catch (e) { return false; }
}

function have(fn, field, what) {
  if (!defined(fn)) { skips++; console.log("  -- skipped: " + fn + "() not implemented"); return false; }
  if (field && typeof hasField === "function" && !hasField(field)) {
    skips++; console.log("  -- skipped: " + what + " not added (no #" + field + ")");
    return false;
  }
  return true;
}

function txt(id) { return JSON.stringify(rows(id)); }

// ---------------------------------------------------------------- A1 thermal
console.log("\n== A1  junction temperature ==");
if (have("calcThermal", "th-p", "thermal card")) {
  clearAll(["th-p", "th-ta", "th-jc", "th-cs", "th-sa", "th-ja", "th-tjmax", "th-tj"]);
  set("th-p", "5"); set("th-ta", "25");
  set("th-jc", "1.5"); set("th-cs", "0.5"); set("th-sa", "8"); set("th-tjmax", "150");
  calcThermal();
  const t = txt("th-out");
  console.log("     " + t);
  near("Tj = 75 C", parseVal(get("th-tj")), 75, 0.01);
  eq("Tj is a calculated field", isCalc("th-tj"), true);
  eq("case temperature 67.5 C reported", /67\.5/.test(t), true);
  eq("sink temperature 65 C reported", /\b65\b/.test(t), true);
  eq("headroom 75 K reported", /\b75\b/.test(t), true);
  eq("max power 12.5 W reported", /12\.5/.test(t), true);
}

// ------------------------------------------------------------ A2 wire drop
console.log("\n== A2  wire voltage drop ==");
if (have("calcAWG", "awg-len", "wire length/current")) {
  clearAll(["awg-n", "awg-len", "awg-i", "awg-temp", "awg-vsupply"]);
  set("awg-n", "12"); set("awg-len", "0.5"); set("awg-i", "40"); set("awg-temp", "20");
  calcAWG();
  const t = txt("awg-out");
  console.log("     " + t);
  eq("208 mV loop drop", /208(\.\d)?\s?mV/.test(t), true);
  eq("8.34 W lost in the round trip", /8\.33\d?\s?W/.test(t), true);
  set("awg-temp", "85"); calcAWG();
  eq("262 mV when hot (25.5% worse)", /26[12](\.\d)?\s?mV/.test(txt("awg-out")), true);
}

// -------------------------------------------------- A3 C and L series/parallel
console.log("\n== A3  capacitors and inductors in series/parallel ==");
if (defined("calcSP")) {
  clearAll(["sp-list"]);
  set("sp-list", "10k, 4k7, 1k"); calcSP();
  let t = txt("sp-out");
  eq("R series 15.7k (unchanged)", /15\.7\s?k/.test(t), true);
  eq("R parallel 761.8 (unchanged)", /761/.test(t), true);

  if (typeof hasField === "function" && hasField("sp-type")) {
    document.getElementById("sp-type").value = "C";
    set("sp-list", "10n, 10n"); calcSP();
    t = txt("sp-out");
    eq("C series 5 nF (capacitors invert)", /5\s?nF/.test(t), true);
    eq("C parallel 20 nF", /20\s?nF/.test(t), true);

    document.getElementById("sp-type").value = "L";
    set("sp-list", "10u, 22u"); calcSP();
    t = txt("sp-out");
    eq("L series 32 uH", /32\s?\u00b5H/.test(t), true);
    eq("L parallel 6.875 uH", /6\.87\d?\s?\u00b5H/.test(t), true);
  } else {
    skips++; console.log("  -- skipped: capacitor/inductor types not added (no #sp-type)");
  }
} else { skips++; console.log("  -- skipped: calcSP() not implemented"); }

// ------------------------------------------------------------- A4 via extras
console.log("\n== A4  via impedance, resonance, aspect ratio ==");
if (have("calcVia", "via-i", "via current/count/aspect ratio")) {
  clearAll(["via-d", "via-tp", "via-h", "via-dt", "via-pad", "via-anti", "via-er",
            "via-i", "via-n", "via-arlimit"]);
  set("via-d", "0.3"); set("via-pad", "0.6"); set("via-anti", "1.0");
  set("via-i", "3"); set("via-n", "10");
  calcVia();
  const t = txt("via-out");
  console.log("     " + t);
  eq("impedance 47.6 ohm", /47\.6/.test(t), true);
  eq("resonant frequency 5.83 GHz", /5\.8[23]/.test(t), true);
  eq("aspect ratio 5.33:1", /5\.33/.test(t), true);
  eq("10 vias give 16.1 K/W", /16\.1\s?K\/W/.test(t), true);
  eq("3 A through the bank dissipates 973 uW", /97[23](\.\d+)?\s?&micro;W|97[23](\.\d+)?\s?\u00b5W/.test(t), true);
}

// ------------------------------------------------------------- B3 skin depth
console.log("\n== B3  skin depth (Group B) ==");
if (have("calcSkin", "sk-f", "skin depth card")) {
  clearAll(["sk-f", "sk-t"]);
  set("sk-f", "1M"); set("sk-t", "35u");
  calcSkin();
  const t = txt("sk-out");
  eq("66.1 um at 1 MHz", /66\.[01]/.test(t), true);
  eq("188.8% of 1 oz copper", /188/.test(t), true);
}

// ------------------------------------------------- B2 impedance structures
console.log("\n== B2  extra impedance structures (Group B) ==");
if (defined("calcZ")) {
  const sel = document.getElementById("z-struct");
  const opts = (sel && sel.options) || [];
  const has = v => Array.prototype.some.call(opts, o => o.value === v);
  if (has("asym")) {
    clearAll(["z-w", "z-h", "z-c"]);
    sel.value = "asym";
    set("z-w", "0.2"); set("z-h", "0.25"); set("z-c", "0.75");
    calcZ();
    eq("asymmetric stripline 59.85 ohm", /59\.[89]/.test(txt("z-out")), true);
  } else { skips++; console.log("  -- skipped: asymmetric stripline not added"); }

  if (has("cpwg")) {
    clearAll(["z-w", "z-h", "z-s"]);
    sel.value = "cpwg";
    set("z-w", "0.3"); set("z-s", "0.2"); set("z-h", "0.2");
    calcZ();
    eq("grounded coplanar 55.95 ohm", /5[56]\.\d/.test(txt("z-out")), true);
  } else { skips++; console.log("  -- skipped: coplanar not added"); }

  if (has("covered")) {
    clearAll(["z-w", "z-h", "z-b"]);
    sel.value = "covered";
    set("z-w", "0.3"); set("z-h", "0.2"); set("z-b", "0.2");
    calcZ();
    // the whole point of the ratio construction: b = h must equal bare exactly
    eq("covered at b=h reproduces bare 53.52", /53\.5/.test(txt("z-out")), true);
    set("z-b", "0.225"); calcZ();
    eq("25 um mask drops it to 52.6", /52\.[567]/.test(txt("z-out")), true);
  } else { skips++; console.log("  -- skipped: covered microstrip not added"); }
} else { skips++; console.log("  -- skipped: calcZ() not implemented"); }

// ----------------------------------------------------- B4 etch factor guard
console.log("\n== B4  etch factor must not disturb existing results (Group B) ==");
if (defined("calcTrace")) {
  const hasEtch = typeof hasField === "function" && hasField("tw-etch");
  clearAll(["tw-i", "tw-w", "tw-len"]);
  if (hasEtch) document.getElementById("tw-etch").value = "none";
  set("tw-w", "1"); calcTrace();
  near("rectangular ampacity still 2.392 A", parseVal(get("tw-i")), 2.392, 1);
  if (hasEtch) {
    document.getElementById("tw-etch").value = "1:1";
    clearAll(["tw-i"]);
    set("tw-w", "1"); calcTrace();
    near("1:1 etch drops it to 2.331 A", parseVal(get("tw-i")), 2.331, 1);
  } else { skips++; console.log("  -- skipped: etch factor not added"); }
} else { skips++; console.log("  -- skipped: calcTrace() not implemented"); }

// ------------------------------------------------------------- B6 pads
console.log("\n== B6  attenuator pads (Group B) ==");
if (have("calcPad", "pad-a", "attenuator card")) {
  // one topology at a time now, so read each separately
  clearAll(["pad-a", "pad-zin", "pad-zout"]);
  set("pad-a", "6"); set("pad-zin", "50"); set("pad-zout", "50");
  document.getElementById("pad-topo").value = "pi";
  calcPad();
  const tp = txt("pad-out");
  eq("PI shunt 150.5", /150\.[45]/.test(tp), true);
  eq("PI series 37.35", /37\.3/.test(tp), true);
  document.getElementById("pad-topo").value = "t";
  calcPad();
  const tt = txt("pad-out");
  eq("T series 16.61", /16\.6/.test(tt), true);
  eq("T shunt 66.93", /66\.9/.test(tt), true);
}

console.log("\n" + passes + " passed, " + fails + " failed, " + skips + " skipped");
if (fails === 0) console.log("nothing that is built is built wrongly");
process.exitCode = fails ? 1 : 0;
