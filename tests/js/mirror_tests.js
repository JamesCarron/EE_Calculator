let f=0,pass=0;
function eq(l,g,w){ if(String(g)===String(w)){pass++;console.log("  ok   "+l);} else {f++;console.log("  FAIL "+l+": got "+g+" want "+w);}}
function near(l,g,w,t){ if(Math.abs(g-w)<=Math.abs(w)*t/100){pass++;console.log("  ok   "+l+" = "+Number(g.toPrecision(6)));} else {f++;console.log("  FAIL "+l+": got "+g+" want ~"+w);}}
console.log("\n== the shared controls exist on their cards ==");
["tw-oz","fu-oz","z-oz","ee-oz","dp-oz"].forEach(id=>eq(id+" present", hasField(id), true));
["tw-dt","via-dt"].forEach(id=>eq(id+" present", hasField(id), true));
["tw-ta","fu-ta","th-ta"].forEach(id=>eq(id+" present", hasField(id), true));
["div-series","led-series","pad-series"].forEach(id=>eq(id+" present", hasField(id), true));
eq("old strip ids gone", hasField("g-oz")||hasField("g-dt")||hasField("g-ta")||hasField("g-series"), false);

console.log("\n== accessors read the shared value ==");
near("copper defaults to 1 oz", gCopperMM(), 0.035, 0.1);
near("temp rise defaults to 10", gTempRise(), 10, 0.1);
near("ambient defaults to 25", gAmbient(), 25, 0.1);
eq("series defaults to E96", gSeries(), "E96");

console.log("\n== changing the value moves every reader ==");
clearAll(["tw-i","tw-w","tw-len","tw-f"]); set("tw-w","1"); calcTrace();
near("1 oz gives 2.392 A", parseVal(get("tw-i")), 2.392, 1);
document.getElementById("tw-oz").value="70";
clearAll(["tw-i"]); set("tw-w","1"); calcTrace();
near("2 oz gives 3.953 A", parseVal(get("tw-i")), 3.953, 1);
// and the impedance card, on another tab, sees the same copper
clearAll(["z-w","z-h","z-er"]); document.getElementById("z-struct").value="ms";
set("z-w","0.3"); set("z-h","0.2"); set("z-er","4.3"); calcZ();
const z70 = parseFloat(rows("z-out").find(x=>x[0]==="Z0")[1]);
document.getElementById("tw-oz").value="35";
clearAll(["z-w","z-h","z-er"]); set("z-w","0.3"); set("z-h","0.2"); set("z-er","4.3"); calcZ();
const z35 = parseFloat(rows("z-out").find(x=>x[0]==="Z0")[1]);
near("impedance follows the same copper (1 oz)", z35, 54.33, 1);
if (z70 < z35) { pass++; console.log("  ok   2 oz lowered Zo to "+z70+" from "+z35); }
else { f++; console.log("  FAIL thicker copper did not lower Zo: "+z70+" vs "+z35); }

console.log("\n== temp rise is shared between trace and via ==");
document.getElementById("tw-dt").value="20";
clearAll(["tw-i"]); set("tw-w","1"); calcTrace();
const i20 = parseVal(get("tw-i"));
document.getElementById("tw-dt").value="10";
clearAll(["tw-i"]); set("tw-w","1"); calcTrace();
near("10 C rise", parseVal(get("tw-i")), 2.392, 1);
if (i20 > 2.392) { pass++; console.log("  ok   20 C rise allows more current: "+Number(i20.toPrecision(4))); }
else { f++; console.log("  FAIL higher rise did not allow more current"); }
console.log("\n"+pass+" passed, "+f+" failed"); process.exitCode=f?1:0;
