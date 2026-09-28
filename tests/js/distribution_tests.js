/* The probability distribution in the divider tolerance fold.

   Written 2026-09-28. Every expectation was computed independently in Python
   before being written here.

   The check that carries the most weight is the sigma input. The whole chart
   rests on reading a +/-tolerance as a k-sigma bound, and nothing on a
   datasheet states k - so it has to be a live input rather than a constant
   baked into the drawing, and changing it has to move the axis. */

let f = 0, pass = 0;
function eq(l, g, w) { if (String(g) === String(w)) { pass++; console.log("  ok   " + l); } else { f++; console.log("  FAIL " + l + ": got " + g + " want " + w); } }
function shows(l, id, re) { const h = document.getElementById(id).innerHTML; if (re.test(h)) { pass++; console.log("  ok   " + l); } else { f++; console.log("  FAIL " + l); } }
function hides(l, id, re) { const h = document.getElementById(id).innerHTML; if (!re.test(h)) { pass++; console.log("  ok   " + l); } else { f++; console.log("  FAIL " + l); } }
/* diagram_tests keeps its own copy; the harness does not provide one */
function drawn(id) { const e = document.getElementById(id); return !!e && e.innerHTML.indexOf("<svg") >= 0; }

const D = ["div-vin", "div-vout", "div-r1", "div-r2", "div-rtot", "div-iload",
           "div-tol1", "div-tol2", "div-tcr1", "div-tcr2", "div-tmin", "div-tmax",
           "div-tnom", "div-age", "div-vintol", "div-vfbtol", "div-vfbtc",
           "div-sig", "div-rtemp", "div-reg", "div-regtemp"];
function feedback() {
  clearAll(D);
  set("div-vin", "3.3"); set("div-vout", "0.8");
  set("div-r1", "31.25k"); set("div-r2", "10k");
}

console.log("\n== the chart appears only once there is a divider ==");
clearAll(D);
calcDivider();
eq("no divider, no chart", drawn("div-dist"), false);
feedback(); calcDivider();
eq("a divider gets one", drawn("div-dist"), true);

console.log("\n== percentages are cumulative, not per shell ==");
/* 68.27 / 95.45 / 99.73 within one, two and three sigma. Two decimals
   throughout: 95.45 renders as 95.4 at one decimal because the double
   sits just below the half, which reads as an arithmetic slip. */
shows("one sigma holds 68.27 %", "div-dist", /68\.27 %/);
shows("two sigma holds 95.45 %", "div-dist", /95\.45 %/);
shows("three sigma holds 99.73 %", "div-dist", /99\.73 %/);
hides("the per-shell 27.2 % figure is gone", "div-dist", /27\.2 %/);
hides("so is the per-shell 4.28 %", "div-dist", /4\.28 %/);
/* the page files carry literal Unicode, not entities, so the row name is
   an actual plus-minus sign */
shows("and the row says what the figures mean", "div-dist", /within ±/);

console.log("\n== nothing wider than three sigma is drawn or named ==");
hides("no worst-case marker", "div-dist", /worst case/);
hides("no off-scale annotation", "div-dist", /off scale/);
hides("no edge tag", "div-dist", /edge = /);
shows("the axis stops at three sigma", "div-dist", /&gt;\+3&lt;|>\+3</);
hides("and never reaches four", "div-dist", /&gt;\+4&lt;|>\+4</);

console.log("\n== one curve, never an overlay ==");
eq("exactly one curve path",
   (document.getElementById("div-dist").innerHTML.match(/class="curve"/g) || []).length, 1);
hides("no dashed comparison curve", "div-dist", /curve alt/);
hides("and no series labels to tell them apart", "div-dist", /ratio only|with reference/);

console.log("\n== the regulator switch changes what is plotted ==");
/* On, with reference drift at its default 50 ppm/degC over 65 degC: the
   reference is 1 % + 0.325 % before it becomes a sigma, so the combined
   sigma is 0.5679 % - the 3 sigma end is +1.70 % and Vout 3.356. */
feedback(); calcDivider();
shows("with the regulator on the axis is the output error", "div-dist", /output error/);
shows("scaled by the combined sigma", "div-dist", /\+1\.70%/);
shows("and the volts axis is the regulator output", "div-dist", /regulator V out/);
shows("reading 3.356 V at three sigma", "div-dist", /3\.356/);

/* off: ratio sigma 0.3571 %, so +1.07 % and the divider's own 0.8086 V */
set("div-reg", "off"); calcDivider();
shows("with it off the axis is the ratio error", "div-dist", /ratio error/);
shows("scaled by the ratio sigma alone", "div-dist", /\+1\.07%/);
shows("and the volts axis is the divider output", "div-dist", /divider V out/);
shows("reading 0.8086 V at three sigma", "div-dist", /0\.8086/);
hides("the regulator rows go with it", "div-tol-out", /Regulator output error/);

console.log("\n== sigma per tolerance is an input, not a constant ==");
/* nothing on a datasheet states it, so it has to be changeable and has to move
   the axis when it changes: k = 6 halves sigma, so 3 sigma is +0.54 % */
feedback(); set("div-reg", "off"); set("div-sig", "6"); calcDivider();
shows("k = 6 halves the axis", "div-dist", /\+0\.54%/);
feedback(); set("div-reg", "off"); set("div-sig", "1.5"); calcDivider();
shows("k = 1.5 doubles it", "div-dist", /\+2\.14%/);
feedback(); set("div-reg", "off"); calcDivider();
shows("and blank falls back to three", "div-dist", /\+1\.07%/);

console.log("\n== it never claims certainty ==");
hides("99.73 is never rounded to 100", "div-dist", /100 %/);

console.log("\n" + pass + " passed, " + f + " failed");
process.exitCode = f ? 1 : 0;
