/* Flex hatched-plane geometry.

   Written 2026-09-21. The card is pure geometry, so every expectation below is
   a hand-computable number rather than a regression capture - the values were
   checked independently in Python before being written here.

   The two checks that matter most are the angle invariance of the fill factor
   (easy to get wrong by assuming a skewed lattice loses copper) and the pitch
   convention (the CAD grid is root-two larger than the perpendicular pitch at
   45 degrees, and confusing them understates the fill by a third). */

let f = 0, pass = 0;
function eq(l, g, w) { if (String(g) === String(w)) { pass++; console.log("  ok   " + l); } else { f++; console.log("  FAIL " + l + ": got " + g + " want " + w); } }
function has(l, id, re) { const t = JSON.stringify(rows(id)); if (re.test(t)) { pass++; console.log("  ok   " + l); } else { f++; console.log("  FAIL " + l + " in " + t); } }
function no(l, id, re) { const t = JSON.stringify(rows(id)); if (!re.test(t)) { pass++; console.log("  ok   " + l); } else { f++; console.log("  FAIL " + l + " in " + t); } }

const HX = ["hx-w", "hx-p", "hx-f", "hx-ang", "hx-cu"];
function fresh() {
  clearAll(HX);
  document.getElementById("hx-pmode").value = "perp";
}

console.log("\n== Fill factor from width and pitch ==");
/* w = 0.1, p = 0.35: r = 0.2857, fill = 1 - 0.71429^2 = 48.98 % */
fresh(); set("hx-w", "0.1"); set("hx-p", "0.35"); calcHatch();
has("0.1 on 0.35 is 49.0 % copper", "hx-out", /49\.0 %/);
has("and reports the complement etched away", "hx-out", /51\.0 % of the plane etched away/);
has("the width/pitch ratio is 0.286", "hx-out", /0\.286/);
has("gap is pitch minus width", "hx-out", /0\.250 mm gap/);

/* the 50 % landmark: w/p = 1 - 1/sqrt(2) = 0.2929 */
fresh(); set("hx-w", "0.1025"); set("hx-p", "0.35"); calcHatch();
has("w/p = 0.293 is the 50 % point", "hx-out", /50\.0 %/);
has("and the card names it as the landmark", "hx-out", /50 % landmark/);

console.log("\n== Fill is independent of the hatch angle ==");
/* shearing the lattice shears cell and opening alike, so the ratio survives */
fresh(); set("hx-w", "0.1"); set("hx-p", "0.35"); set("hx-ang", "45"); calcHatch();
const fill45 = rows("hx-out")[0][1];
fresh(); set("hx-w", "0.1"); set("hx-p", "0.35"); set("hx-ang", "20"); calcHatch();
const fill20 = rows("hx-out")[0][1];
eq("20 degrees gives the same fill as 45", fill20, fill45);
fresh(); set("hx-w", "0.1"); set("hx-p", "0.35"); set("hx-ang", "70"); calcHatch();
eq("and so does 70", rows("hx-out")[0][1], fill45);

console.log("\n== but the shape is not ==");
/* cell along the signal is p/sin(phi): 0.495 mm at 45, 1.023 mm at 20 */
fresh(); set("hx-w", "0.1"); set("hx-p", "0.35"); set("hx-ang", "45"); calcHatch();
has("at 45 the repeat is square, 0.495 mm each way", "hx-out", /0\.495 mm along the signal &times; 0\.495 mm/);
has("so it fails the elongation guideline", "hx-out", /short\/long = 1\.00/);
has("and the card says which angle would pass", "hx-out", /26\.6&deg; or shallower/);
fresh(); set("hx-w", "0.1"); set("hx-p", "0.35"); set("hx-ang", "20"); calcHatch();
has("at 20 the repeat stretches along the signal", "hx-out", /1\.02 mm along the signal/);
has("meeting the short/long rule at 0.36", "hx-out", /short\/long = 0\.36.*meeting/);

console.log("\n== The CAD grid is not the perpendicular pitch ==");
/* 0.15 track on a 0.5 mm grid: true p = 0.3536, fill 66.9 %.
   Read as a perpendicular pitch instead it comes out 51.0 %. */
fresh(); set("hx-w", "0.15"); set("hx-p", "0.5"); calcHatch();
has("0.5 read as perpendicular pitch gives 51.0 %", "hx-out", /51\.0 %/);
fresh(); set("hx-w", "0.15"); set("hx-p", "0.5");
document.getElementById("hx-pmode").value = "axis"; calcHatch();
has("the same 0.5 as a CAD grid gives 66.9 %", "hx-out", /66\.9 %/);
has("and it reports the grid back for the CAD tool", "hx-out", /0\.500 mm along the signal axis/);

console.log("\n== Solving for the missing dimension ==");
fresh(); set("hx-p", "0.35"); set("hx-f", "50"); calcHatch();
has("a 50 % target on a 0.35 pitch solves the width", "hx-out", /50\.0 %/);
/* val(), not parseFloat: the box carries engineering notation */
eq("and writes 0.1025 mm into the width box",
   Math.abs(val("hx-w") - 0.1025) < 5e-4, true);
fresh(); set("hx-w", "0.1"); set("hx-f", "50"); calcHatch();
has("a 50 % target on a 0.1 track solves the pitch", "hx-out", /50\.0 %/);
eq("giving a 0.3414 mm pitch",
   Math.abs(val("hx-p") - 0.3414) < 2e-3, true);

console.log("\n== Sheet resistance is worse than the fill implies ==");
/* only the family along the current carries it: (p/w)/(2cos^2 phi) */
fresh(); set("hx-w", "0.1"); set("hx-p", "0.35"); calcHatch();
has("0.35/0.1 at 45 degrees is 3.50x solid", "hx-out", /3\.50&times; solid/);
has("isotropic at 45, so across matches along", "hx-out", /3\.50&times; solid along the signal, 3\.50&times; across/);
has("the card says why it is not 1/fill", "hx-out", /only the tracks that run along the current carry it/);
/* 1 oz is 34.79 um, so 0.4955 mOhm/sq solid, times 3.5 */
fresh(); set("hx-w", "0.1"); set("hx-p", "0.35"); set("hx-cu", "1"); calcHatch();
has("1 oz copper gives 1.73 mOhm/sq along the signal", "hx-out", /1\.73[0-9]* m&#?\w*;?Ω\/sq|1\.73[0-9]* mΩ\/sq/);
/* a shallow angle puts more copper along the signal and less across it */
fresh(); set("hx-w", "0.1"); set("hx-p", "0.35"); set("hx-ang", "20"); calcHatch();
has("at 20 degrees the along-signal path improves", "hx-out", /1\.98&times; solid along/);
has("at the cost of the across-signal path", "hx-out", /15\.0&times; across/);

console.log("\n== Guidelines are checked, not recited ==");
fresh(); set("hx-w", "0.1"); set("hx-p", "0.35"); calcHatch();
has("49 % fill is flagged as below the RF figure", "hx-out", /below 50 %/);
has("0.495 mm repeat is inside the 1.27 mm limit", "hx-out", /0\.495 mm, within the 1\.27 mm/);
fresh(); set("hx-w", "0.3"); set("hx-p", "1.5"); calcHatch();
has("a 1.5 mm pitch breaks the repeat-size limit", "hx-out", /above the 1\.27 mm/);
fresh(); set("hx-w", "0.2"); set("hx-p", "0.35"); calcHatch();
has("a fatter track passes the fill guideline", "hx-out", /at or above the 50 %/);

console.log("\n== Refusals and the empty card ==");
fresh(); set("hx-w", "0.4"); set("hx-p", "0.35"); calcHatch();
has("a track wider than the pitch is refused", "hx-out", /tracks merge and the plane is solid/);
fresh(); set("hx-p", "0.35"); set("hx-f", "120"); calcHatch();
has("a fill above 100 % is refused", "hx-out", /between 0 and 100 %/);
fresh(); set("hx-w", "0.1"); calcHatch();
has("a width alone asks for the missing input", "hx-out", /Give a track width and a pitch/);
fresh(); calcHatch();
has("an untouched card says what it needs", "hx-out", /Give a track width and a pitch/);
no("and never reports NaN", "hx-out", /NaN|Infinity/);

console.log("\n== It stays a geometry card ==");
fresh(); set("hx-w", "0.1"); set("hx-p", "0.35"); calcHatch();
has("the model row disclaims impedance", "hx-out", /impedance of a trace over it is not a closed form/);

console.log("\n" + pass + " passed, " + f + " failed");
process.exitCode = f ? 1 : 0;
