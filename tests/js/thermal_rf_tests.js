let f=0,pass=0;
function eq(l,g,w){ if(String(g)===String(w)){pass++;console.log("  ok   "+l);} else {f++;console.log("  FAIL "+l+": got "+g+" want "+w);} }
function near(l,g,w,t){ if(Math.abs(g-w)<=Math.abs(w)*t/100){pass++;console.log("  ok   "+l+" = "+Number(g.toPrecision(6)));} else {f++;console.log("  FAIL "+l+": got "+g+" want ~"+w);} }
function has(l,id,re){ const t=JSON.stringify(rows(id)); if(re.test(t)){pass++;console.log("  ok   "+l);} else {f++;console.log("  FAIL "+l+" in "+t);} }

console.log("\n== Junction temperature ==");
const TH=["th-p","th-ta","th-jc","th-cs","th-sa","th-ja","th-tjmax","th-tjtarget","th-tj"];
clearAll(TH); set("th-p","5"); set("th-ta","25"); set("th-jc","1.5"); set("th-cs","0.5"); set("th-sa","8"); set("th-tjmax","150");
calcThermal();
near("Tj = 75", parseVal(get("th-tj")), 75, 0.01);
has("total theta 10","th-out",/10\.00 °C\/W/);
has("rise 50 K","th-out",/50\.00 K/);
has("case 67.5","th-out",/67\.50/);
has("sink 65","th-out",/65\.00/);
has("headroom 75","th-out",/75\.00 K/);
has("Pmax 12.5 W","th-out",/12\.5 W/);
set("th-tjtarget","125"); calcThermal();
has("theta_sa needed 18","th-out",/18\.00 °C\/W/);
clearAll(TH); set("th-p","50"); set("th-ta","25"); set("th-ja","10"); set("th-tjmax","150"); calcThermal();
has("over-temperature flagged","th-out",/over temperature/);

console.log("\n== Capacitor SRF ==");
clearAll(["cs-c","cs-esl","cs-esr","cs-f","cs-n"]);
set("cs-c","100n"); set("cs-esl","500p"); set("cs-esr","10m"); calcCapSRF();
has("SRF 22.5 MHz","cs-out",/22\.5[0-9]* MHz/);
set("cs-f","100M"); calcCapSRF();
has("inductive above SRF","cs-out",/inductive, past self-resonance/);
set("cs-f","1M"); calcCapSRF();
has("capacitive below SRF","cs-out",/capacitive/);

console.log("\n== Plane capacitance and PDN ==");
// plane capacitance card removed at the owner's request
clearAll(["pdn-v","pdn-ripple","pdn-i","pdn-tr","pdn-fmax"]);
set("pdn-v","1.2"); set("pdn-ripple","2"); set("pdn-i","20"); set("pdn-tr","50"); calcPDN();
has("target 2.4 mohm","pdn-out",/2\.4 mΩ/);

console.log("\n== Attenuator pads ==");
// the card now draws and reports one topology at a time, so pick each in turn
clearAll(["pad-a","pad-zin","pad-zout"]);
document.getElementById("pad-topo").value = "pi";
set("pad-a","6"); set("pad-zin","50"); set("pad-zout","50"); calcPad();
has("PI 150.5 / 37.35","pad-out",/37\.35 Ω/);
has("PI shunt legs","pad-out",/150\.5 Ω/);
document.getElementById("pad-topo").value = "t"; calcPad();
has("T 16.61 / 66.93","pad-out",/16\.61 Ω/);
has("T shunt","pad-out",/66\.93 Ω/);
document.getElementById("pad-topo").value = "l";
set("pad-zin","75"); set("pad-zout","50"); calcPad();
has("L pad min loss 5.72 dB","pad-out",/5\.7[12] dB/);

console.log("\n== Er effective (Hammerstad-Jensen) ==");
clearAll(["ee-w","ee-h","ee-er","ee-f"]);
set("ee-w","0.3"); set("ee-h","0.2"); set("ee-er","4.3"); calcEreff();
has("u corrected 1.691","ee-out",/1\.691/);
has("eps_eff 3.2297","ee-out",/3\.229[0-9]/);
has("bounded 2.65..4.3","ee-out",/2\.650 … 4\.300/);
set("ee-f","10G"); calcEreff();
has("dispersion at 10 GHz","ee-out",/3\.24[0-9]/);
set("ee-w","0.0005"); set("ee-h","10"); calcEreff();
has("outside validity refused","ee-out",/validity range/);

console.log("\n== Differential pair ==");
clearAll(["dp-w","dp-s","dp-h","dp-er"]);
set("dp-w","0.2"); set("dp-s","0.2"); set("dp-h","0.2"); set("dp-er","4.3");
document.getElementById("dp-target").value="100";
calcDiff();
console.log("     "+JSON.stringify(rows("dp-out")));
has("reports Zdiff","dp-out",/Differential/);
has("compares to target","dp-out",/vs. target 100/);

console.log("\n== LC / RL, now the combined filter card ==");
const FF=["flt-r","flt-c","flt-l","flt-f"];
document.getElementById("flt-type").value="lcs";
clearAll(FF); set("flt-l","10u"); set("flt-c","100n"); calcFilter();
has("resonance 159.2 kHz","flt-out",/159\.[12] kHz/);
has("sqrt(L/C) = 10 ohm","flt-out",/10 Ω/);
set("flt-r","1"); calcFilter();
// the card now models a LOADED filter, not an unloaded resonator: with a
// 1 ohm load on a 10 ohm sqrt(L/C) the filter Q is 0.1, heavily overdamped
has("loaded filter Q = 0.1","flt-out",/Q with 1 Ω load/);
has("overdamped is flagged","flt-out",/overdamped/);
document.getElementById("flt-type").value="rl";
clearAll(FF); set("flt-l","10u"); set("flt-r","100"); calcFilter();
has("RL corner 1.592 MHz","flt-out",/1\.59[12] MHz/);

console.log("\n== Battery ==");
clearAll(["bat-mah","bat-v","bat-s","bat-p","bat-load","bat-usable"]);
set("bat-mah","5000"); set("bat-v","3.7"); set("bat-s","6"); set("bat-p","2"); set("bat-load","20"); set("bat-usable","80");
calcBattery();
console.log("     "+JSON.stringify(rows("bat-out")));
has("6S2P at 22.2 V","bat-out",/6S2P at 22\.2 V/);
has("10 Ah","bat-out",/10.00 Ah/);
has("222 Wh","bat-out",/222/);
has("C-rate 2","bat-out",/2 C|2\.00 C/);

console.log("\n"+pass+" passed, "+f+" failed");
process.exitCode=f?1:0;

console.log("\n== differential mode relations ==");
clearAll(["dp-w","dp-s","dp-h","dp-er"]);
set("dp-w","0.2"); set("dp-s","0.2"); set("dp-h","0.2"); set("dp-er","4.3"); calcDiff();
const r = rows("dp-out");
const z0 = parseFloat(r.find(x=>/Single-ended/.test(x[0]))[1]);
const modes = r.find(x=>/Odd \/ even/.test(x[0]))[1].match(/([\d.]+) Ω \/ ([\d.]+) Ω/);
const zodd = parseFloat(modes[1]), zeven = parseFloat(modes[2]);
near("Z0 = sqrt(Zodd*Zeven)", Math.sqrt(zodd*zeven), z0, 0.2);
near("Zdiff = 2*Zodd", 2*zodd, parseFloat(r.find(x=>/Differential/.test(x[0]))[1]), 0.2);
console.log("\n"+pass+" passed, "+f+" failed");
process.exitCode=f?1:0;
