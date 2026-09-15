let f=0,pass=0;
function eq(l,g,w){ if(String(g)===String(w)){pass++;console.log("  ok   "+l);} else {f++;console.log("  FAIL "+l+": got "+g+" want "+w);} }
function near(l,g,w,t){ if(Math.abs(g-w)<=Math.abs(w)*t/100){pass++;console.log("  ok   "+l+" = "+Number(g.toPrecision(6)));} else {f++;console.log("  FAIL "+l+": got "+g+" want ~"+w);} }
function has(l,id,re){ const t=JSON.stringify(rows(id)); if(re.test(t)){pass++;console.log("  ok   "+l);} else {f++;console.log("  FAIL "+l+" in "+t);} }
const TW=["tw-i","tw-w","tw-len","tw-dt","tw-ta","tw-f"];

console.log("\n== solving still works and is unchanged ==");
clearAll(TW); set("tw-w","1"); calcTrace();
near("1 mm gives 2.392 A", parseVal(get("tw-i")), 2.392, 1);
clearAll(TW); set("tw-i","3"); calcTrace();
near("3 A needs 1.367 mm", parseFloat(get("tw-w")), 1.367, 1);

console.log("\n== required vs achievable shown together ==");
clearAll(TW); set("tw-w","1"); set("tw-i","3"); calcTrace();
has("shows required","tw-out",/Current required.*3 A/);
has("shows achievable","tw-out",/can carry.*2\.39/);
has("undersized verdict","tw-out",/% short — undersized/);
has("tells you the width needed","tw-out",/Width needed for 3 A/);
clearAll(TW); set("tw-w","2"); set("tw-i","3"); calcTrace();
has("headroom verdict when adequate","tw-out",/% headroom/);

console.log("\n== current density ==");
clearAll(TW); set("tw-w","1"); set("tw-i","3"); calcTrace();
has("85.7 A/mm2","tw-out",/85\.7[0-9]* A\/mm/);

console.log("\n== skin depth ==");
clearAll(TW); set("tw-w","1"); set("tw-f","1M"); calcTrace();
has("66.1 um at 1 MHz","tw-out",/66\.0[0-9]* µm|66\.1 µm/);
has("percent of copper","tw-out",/18[89](\.\d)? %/);
has("whole thickness conducts","tw-out",/whole thickness conducts/);
set("tw-f","100M"); calcTrace();
has("thin skin flagged at 100 MHz","tw-out",/extra thickness buys less/);

console.log("\n== model is stated ==");
has("names IPC-2221 and k","tw-out",/IPC-2221.*k = 0\.048/);

console.log("\n"+pass+" passed, "+f+" failed");
process.exitCode=f?1:0;
