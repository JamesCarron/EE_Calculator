let f=0,pass=0;
function has(l,id,re){const t=JSON.stringify(rows(id)); if(re.test(t)){pass++;console.log("  ok   "+l);} else {f++;console.log("  FAIL "+l+" in "+t);}}
function near(l,g,w,t){ if(Math.abs(g-w)<=Math.abs(w)*t/100){pass++;console.log("  ok   "+l+" = "+Number(g.toPrecision(6)));} else {f++;console.log("  FAIL "+l+": got "+g+" want ~"+w);}}
const V=["vs-f","vs-tr","vs-er","vs-pitch","vs-len","vs-d"];
console.log("\n== via shielding ==");
clearAll(V); set("vs-f","6G"); set("vs-er","4.3"); calcViaShield();
// lambda = c/(f*sqrt(er)) = 3e8/(6e9*2.0736) = 24.1 mm; /10 = 2.41 mm
near("suggested pitch = lambda/10", parseFloat(get("vs-pitch")), 2.410, 2);
has("reports the wavelength","vs-out",/Wavelength in the board/);
has("warns about the half-wave point","vs-out",/Half-wave leak point/);
set("vs-pitch","2"); calcViaShield();
has("2 mm passes","vs-out",/inside the λ\/10 rule/);
set("vs-pitch","5"); calcViaShield();
has("5 mm is flagged","vs-out",/too coarse/);
set("vs-pitch","2"); set("vs-len","50"); calcViaShield();
has("counts the vias","vs-out",/26 per row, 52 for a pair/);
set("vs-d","1.9"); calcViaShield();
has("flags a tight barrel gap","vs-out",/tight for fabrication/);
clearAll(V); set("vs-tr","100p"); set("vs-er","4.3"); calcViaShield();
has("derives f from rise time","vs-out",/Knee frequency from rise time.*3\.5 GHz/);
has("names the model","vs-out",/rule of thumb/);
console.log("\n"+pass+" passed, "+f+" failed"); process.exitCode=f?1:0;
