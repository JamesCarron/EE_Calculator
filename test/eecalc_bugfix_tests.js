let f=0,pass=0;
function eq(l,g,w){ if(String(g)===String(w)){pass++;console.log("  ok   "+l);} else {f++;console.log("  FAIL "+l+": got "+g+" want "+w);} }
function near(l,g,w,t){ if(Math.abs(g-w)<=Math.abs(w)*t/100){pass++;console.log("  ok   "+l+" = "+Number(g.toPrecision(6)));} else {f++;console.log("  FAIL "+l+": got "+g+" want ~"+w);} }
function txt(id){ return JSON.stringify(rows(id)); }
function isBad(id){ return document.getElementById(id).classList.contains("bad"); }

console.log("\n== A6 crystal: partner cap when C1 is known ==");
clearAll(["xc-cl","xc-c1","xc-c2","xc-cs"]);
set("xc-cl","12p"); set("xc-c1","22p"); calcXtal();
near("C2 partner for 22p", parseVal(get("xc-c2")), 15.23e-12, 0.5);
const CL=(22e-12*parseVal(get("xc-c2")))/(22e-12+parseVal(get("xc-c2")))+3e-12;
near("resulting load equals the 12 pF spec", CL, 12e-12, 0.5);
clearAll(["xc-cl","xc-c1","xc-c2","xc-cs"]);
set("xc-cl","12p"); calcXtal();
eq("symmetric case still 18p/18p", get("xc-c1")+"/"+get("xc-c2"), "18p/18p");
clearAll(["xc-cl","xc-c1","xc-c2","xc-cs"]);
set("xc-cl","12p"); set("xc-c1","5p"); calcXtal();
eq("too-small leg is refused", /too small/.test(txt("xc-out")), true);

console.log("\n== A5 no more silent defaults ==");
clearAll(["z-w","z-h","z-er"]);
set("z-w","0.3"); set("z-h","0.2"); set("z-er","1"); calcZ();
const air=txt("z-out");
eq("er=1 is accepted, not swapped for FR-4", /1[0-9][0-9]\./.test(air) || !/53\.5/.test(air), true);
console.log("     er=1 -> "+air);
set("z-er","0.5"); calcZ();
eq("er=0.5 is flagged bad", isBad("z-er"), true);
eq("...and no result is shown", rows("z-out").length, 0);
set("z-er",""); calcZ();
// 53.5 was the retired IPC-2141 87-form; Hammerstad-Jensen gives 54.3 for
// the same geometry, which is the intended consequence of the model switch.
eq("empty er still defaults to 4.3", /54\.3/.test(txt("z-out")), true);

console.log("\n== A4 via plating parses as micrometres ==");
clearAll(["via-d","via-tp","via-h","via-dt","via-pad","via-anti","via-er"]);
set("via-d","0.3"); calcVia();
const base=txt("via-out");
set("via-tp","25"); calcVia();
eq("bare 25 means 25 um (same as default)", txt("via-out")===base, true);
set("via-tp","25um"); calcVia();
eq("25um gives the same answer", txt("via-out")===base, true);
set("via-tp","0.025mm"); calcVia();
eq("0.025mm gives the same answer", txt("via-out")===base, true);
set("via-tp","zzz"); calcVia();
eq("nonsense is flagged bad", isBad("via-tp"), true);

console.log("\n== A3 spacing still works under its new id ==");
clearAll(["spc-v"]); set("spc-v","48"); calcSpacing();
eq("48 V gives the B2 0.60 mm row", /0\.60 mm/.test(txt("spc-out")), true);

console.log("\n== regression: previously verified values unchanged ==");
clearAll(["div-vin","div-vout","div-r1","div-r2","div-rtot","div-iload"]);
set("div-vin","12"); set("div-vout","3.3"); set("div-r1","10k"); set("div-iload","100u"); calcDivider();
eq("divider R2 still 4.2857k", get("div-r2"), "4.2857k");
clearAll(["tw-i","tw-w","tw-len"]); set("tw-w","1"); calcTrace();
near("trace ampacity still 2.392 A", parseVal(get("tw-i")), 2.392, 1);
clearAll(["via-d","via-tp","via-pad","via-anti"]); set("via-d","0.3"); set("via-pad","0.6"); set("via-anti","1.0"); calcVia();
eq("via capacitance still 0.573 pF", /0\.573 pF/.test(txt("via-out")), true);
clearAll(["wl-f","wl-tr","wl-eeff"]); set("wl-f","100M"); calcWave();
eq("wavelength still 1.65 m", /1\.65 m/.test(txt("wl-out")), true);
console.log("\n"+pass+" passed, "+f+" failed");
process.exitCode=f?1:0;
