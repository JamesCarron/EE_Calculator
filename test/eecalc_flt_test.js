let f=0,pass=0;
function eq(l,g,w){ if(String(g)===String(w)){pass++;console.log("  ok   "+l);} else {f++;console.log("  FAIL "+l+": got "+g+" want "+w);}}
function near(l,g,w,t){ if(Math.abs(g-w)<=Math.abs(w)*t/100){pass++;console.log("  ok   "+l+" = "+Number(g.toPrecision(6)));} else {f++;console.log("  FAIL "+l+": got "+g+" want ~"+w);}}
function has(l,id,re){const t=JSON.stringify(rows(id)); if(re.test(t)){pass++;console.log("  ok   "+l);} else {f++;console.log("  FAIL "+l+" in "+t);}}
const F=["flt-r","flt-c","flt-l","flt-f"];
function setSel(id,v){ document.getElementById(id).value=v; }

console.log("\n== topology follows response ==");
eq("RC low-pass: R series, C shunt", fltTopology("rc","lp").join(""), "RC");
eq("RC high-pass: C series, R shunt", fltTopology("rc","hp").join(""), "CR");
eq("RL low-pass: L series, R shunt", fltTopology("rl","lp").join(""), "LR");
eq("RL high-pass: R series, L shunt", fltTopology("rl","hp").join(""), "RL");
eq("LC low-pass: L series, C shunt", fltTopology("lc","lp").join(""), "LC");
eq("LC high-pass: C series, L shunt", fltTopology("lc","hp").join(""), "CL");

console.log("\n== magnitude at the corner and asymptotes ==");
const st1={type:"rc",resp:"lp",order:1,Q:0.7071,f0:1000};
near("1st-order LP is -3.01 dB at f0", fltDb(1,st1), -3.0103, 0.5);
near("1st-order LP is -20 dB a decade out", fltDb(10,st1), -20.04, 1);
near("1st-order LP is ~0 dB a decade in", fltDb(0.1,st1), -0.0432, 20);
const st4={type:"rc",resp:"lp",order:4,Q:0.7071,f0:1000};
near("4th-order is 4x the dB at f0", fltDb(1,st4), -12.04, 0.5);
near("4th-order rolls off 80 dB/decade", fltDb(10,st4)-fltDb(100,st4), 80, 2);
const hp1={type:"rc",resp:"hp",order:1,Q:0.7071,f0:1000};
near("high-pass mirrors: -3 dB at f0", fltDb(1,hp1), -3.0103, 0.5);
near("high-pass -20 dB a decade below", fltDb(0.1,hp1), -20.04, 1);
const lc={type:"lc",resp:"lp",order:2,Q:0.7071,f0:1000};
near("Butterworth LC is -3 dB at f0", fltDb(1,lc), -3.0103, 1);
near("LC rolls off 40 dB/decade", fltDb(10,lc)-fltDb(100,lc), 40, 2);
const lcq={type:"lc",resp:"lp",order:2,Q:5,f0:1000};
if (fltDb(1,lcq) > 3) { pass++; console.log("  ok   high Q peaks at f0 = "+fltDb(1,lcq).toFixed(1)+" dB"); }
else { f++; console.log("  FAIL high Q did not peak"); }

console.log("\n== the cascade -3 dB is not the section corner ==");
setSel("flt-type","rc"); setSel("flt-resp","lp"); setSel("flt-order","1");
clearAll(F); set("flt-r","10k"); set("flt-c","100n"); calcFilter();
near("1st order f0", parseVal(get("flt-f")), 159.15, 0.1);
has("1st order -3dB equals f0","flt-out",/Overall &minus;3 dB","159/);
setSel("flt-order","4"); calcFilter();
has("4th order -3dB is shifted","flt-out",/0\.43[45]× the section corner/);
has("rolloff 80 dB/decade","flt-out",/80 dB\/decade/);

console.log("\n== solving still works in every mode ==");
setSel("flt-type","rc"); setSel("flt-order","1");
clearAll(F); set("flt-r","10k"); set("flt-f","1k"); calcFilter();
near("RC solves C", parseVal(get("flt-c")), 15.915e-9, 0.1);
setSel("flt-type","rl");
clearAll(F); set("flt-r","100"); set("flt-l","10u"); calcFilter();
near("RL corner", parseVal(get("flt-f")), 1.5915e6, 0.1);
setSel("flt-type","lc");
clearAll(F); set("flt-l","10u"); set("flt-c","100n"); calcFilter();
near("LC resonance", parseVal(get("flt-f")), 159154, 0.1);
has("LC order forced even","flt-out",/40 dB\/decade/);

console.log("\n== attenuation rows make the plot non-essential ==");
setSel("flt-type","rc"); setSel("flt-resp","lp"); setSel("flt-order","1");
clearAll(F); set("flt-r","10k"); set("flt-c","100n"); calcFilter();
has("gives attenuation at 10x","flt-out",/Attenuation at 1\.59[12] kHz.*-20\.0/);

console.log("\n"+pass+" passed, "+f+" failed"); process.exitCode=f?1:0;
