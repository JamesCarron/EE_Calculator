// Log x axes: round-decade ticks and the 2-9 minor gridlines that make the
// axis legible as logarithmic. Applies to every log-x plot, not just one.

let f = 0, pass = 0;
function eq(l, g, w) {
  if (String(g) === String(w)) { pass++; console.log("  ok   " + l); }
  else { f++; console.log("  FAIL " + l + ": got " + g + ", want " + w); }
}
/* The x tick labels are the lowest row of text in the plot. Selecting them by
   text-anchor broke when the end labels were anchored inwards to stop them
   hanging off the SVG, so select by position instead. */
function labels(id) {
  const re = /<text[^>]*\sy="([\d.]+)"[^>]*>([^<]*)<\/text>/g;
  const html = document.getElementById(id).innerHTML;
  const all = [];
  let m;
  while ((m = re.exec(html))) all.push([parseFloat(m[1]), m[2]]);
  if (!all.length) return [];
  const bottom = Math.max.apply(null, all.map(function (q) { return q[0]; }));
  return all.filter(function (q) { return q[0] === bottom; }).map(function (q) { return q[1]; });
}
function minors(id) { return (document.getElementById(id).innerHTML.match(/class="gridmin"/g) || []).length; }

/* A decade label is a round power of ten: 1, 10 or 100 with a prefix. */
const ROUND = /^(1|10|100) [a-zA-Zµμ]*(Hz|s)$/;

console.log("\n== filter response ==");
document.getElementById("flt-type").value = "rc";
document.getElementById("flt-resp").value = "lp";
document.getElementById("flt-order").value = "1";
clearAll(["flt-r", "flt-c", "flt-l", "flt-f"]);
set("flt-r", "10k"); set("flt-c", "100n"); calcFilter();      // f0 = 159.15 Hz
const fl = labels("flt-graph");
eq("every tick is a round decade", fl.every(function (t) { return ROUND.test(t); }), true);
eq("it starts at 1 Hz, not at a multiple of f0", fl[0], "1 Hz");
eq("and ends at 100 kHz", fl[fl.length - 1], "100 kHz");
eq("eight minor lines per decade", minors("flt-graph"), (fl.length - 1) * 8);

/* An f0 in a different decade must still snap to round values. */
clearAll(["flt-r", "flt-c", "flt-l", "flt-f"]);
set("flt-r", "50"); set("flt-c", "100p"); calcFilter();        // f0 = 31.83 MHz
const fl2 = labels("flt-graph");
eq("still round decades an octave up the spectrum",
   fl2.every(function (t) { return ROUND.test(t); }), true);
/* The crosshair reads f = 10^x directly, so x must be absolute log10 of the
   frequency rather than an offset from f0. The stub has no live SVG to
   query, so check the stored geometry the readout is computed from. */
eq("x is absolute log10 f, so the crosshair needs no f0",
   Math.round(Math.pow(10, fltGraph.pts[0][0])), Math.round(Math.pow(10, fltGraph.box.d0)));
eq("the plot spans whole decades", Number.isInteger(fltGraph.box.d0) && Number.isInteger(fltGraph.box.d1), true);
eq("the last sample lands on the last decade",
   Math.round(fltGraph.pts[fltGraph.pts.length - 1][0]), fltGraph.box.d1);

console.log("\n== self-resonance ==");
clearAll(["re-f", "re-c", "re-l", "re-esl", "re-esr", "re-n", "re-epc", "re-dcr"]);
set("re-c", "100n"); set("re-esl", "500p"); calcReact();
const rl = labels("re-graph");
eq("round decades", rl.every(function (t) { return ROUND.test(t); }), true);
eq("eight minor lines per decade", minors("re-graph"), (rl.length - 1) * 8);

console.log("\n== fusing current ==");
clearAll(["fu-w", "fu-t", "fu-k"]);
set("fu-w", "1"); set("fu-t", "1"); calcFuse();
const ul = labels("fu-graph");
eq("round decades of time", ul.every(function (t) { return ROUND.test(t); }), true);
eq("10 ms to 100 s", ul[0] + " to " + ul[ul.length - 1], "10 ms to 100 s");
eq("eight minor lines per decade", minors("fu-graph"), (ul.length - 1) * 8);

console.log("\n== a linear axis gets no minor lines ==");
document.getElementById("bat-chem").value = "lipo";
clearAll(["bat-mah", "bat-vfull", "bat-v", "bat-vmin", "bat-s", "bat-p", "bat-load", "bat-usable", "bat-crate"]);
set("bat-mah", "5000"); calcBattery();
eq("the discharge curve's percentage axis stays plain", minors("bat-graph"), 0);

console.log("\n" + pass + " passed, " + f + " failed");
process.exitCode = f ? 1 : 0;
