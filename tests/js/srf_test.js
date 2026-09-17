let f=0,pass=0;
function has(l,id,re){const t=JSON.stringify(rows(id)); if(re.test(t)){pass++;console.log("  ok   "+l);} else {f++;console.log("  FAIL "+l+" in "+t);}}
function near(l,g,w,t){ if(Math.abs(g-w)<=Math.abs(w)*t/100){pass++;console.log("  ok   "+l+" = "+Number(g.toPrecision(6)));} else {f++;console.log("  FAIL "+l+": got "+g+" want ~"+w);}}
const R=["re-f","re-c","re-l","re-esl","re-esr","re-n","re-epc","re-dcr"];
console.log("\n== ideal reactance unchanged ==");
clearAll(R); set("re-f","100k"); set("re-c","10n"); set("re-l","22u"); calcReact();
has("Xc 159.2 ohm","re-out",/159\.2 Ω/); has("Xl 13.82 ohm","re-out",/13\.8[12] Ω/);
has("LC resonance 339.3 kHz","re-out",/339\.[23] kHz/);
console.log("\n== capacitor self-resonance ==");
clearAll(R); set("re-c","100n"); set("re-esl","500p"); set("re-esr","10m"); calcReact();
has("SRF 22.5 MHz","re-out",/22\.5[0-9]* MHz/);
set("re-f","100M"); calcReact(); has("inductive above SRF","re-out",/inductive, past self-resonance/);
set("re-f","1M"); calcReact(); has("capacitive below SRF","re-out",/still capacitive/);
set("re-n","4"); calcReact(); has("bank of 4 reported","re-out",/Bank of 4/);
console.log("\n== inductor self-resonance ==");
clearAll(R); set("re-l","22u"); set("re-epc","3p"); set("re-dcr","50m"); calcReact();
has("inductor SRF 19.6 MHz","re-out",/19\.[56][0-9]* MHz/);
has("choke warning","re-out",/a choke stops choking/);
set("re-f","1M"); calcReact();
has("inductive below SRF","re-out",/still inductive/);
has("Q reported","re-out",/Inductor Q/);
// |Z| well below SRF must approach wL
const r=rows("re-out").find(x=>/Inductor \|Z\|/.test(x[0]));
near("|Z| ~ wL at 1 MHz", parseVal(r[1].split(" —")[0]), 2*Math.PI*1e6*22e-6, 5);
set("re-f","100M"); calcReact();
has("capacitive above SRF","re-out",/capacitive, past self-resonance/);
console.log("\n"+pass+" passed, "+f+" failed"); process.exitCode=f?1:0;
