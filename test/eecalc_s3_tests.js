let f=0,pass=0;
function eq(l,g,w){ if(String(g)===String(w)){pass++;console.log("  ok   "+l);} else {f++;console.log("  FAIL "+l+": got "+g+" want "+w);} }
function near(l,g,w,t){ if(Math.abs(g-w)<=Math.abs(w)*t/100){pass++;console.log("  ok   "+l+" = "+Number(g.toPrecision(6)));} else {f++;console.log("  FAIL "+l+": got "+g+" want ~"+w);} }
function has(l,id,re){ const t=JSON.stringify(rows(id)); if(re.test(t)){pass++;console.log("  ok   "+l);} else {f++;console.log("  FAIL "+l+" in "+t);} }
function no(l,id,re){ const t=JSON.stringify(rows(id)); if(!re.test(t)){pass++;console.log("  ok   "+l);} else {f++;console.log("  FAIL "+l+" in "+t);} }

console.log("\n== Series/parallel: R, C, L ==");
clearAll(["sp-list","sp-v"]);
document.getElementById("sp-type").value="R"; set("sp-list","10k, 4k7, 1k"); calcSP();
has("R series 15.7k","sp-out",/15\.7 kΩ/); has("R parallel 761.8","sp-out",/761\.[78] Ω/);
document.getElementById("sp-type").value="C"; set("sp-list","10n, 10n"); calcSP();
has("C series 5 nF","sp-out",/Series.*5 nF/); has("C parallel 20 nF","sp-out",/Parallel.*20 nF/);
has("explains the inversion","sp-out",/Capacitors invert/);
document.getElementById("sp-type").value="L"; set("sp-list","10u, 22u"); calcSP();
has("L series 32 uH","sp-out",/32 µH/); has("L parallel 6.875 uH","sp-out",/6\.875 µH/);
document.getElementById("sp-type").value="R"; set("sp-list","10k, 4k7, 1k"); set("sp-v","12"); calcSP();
has("per-element voltages","sp-out",/element 1/);
has("series current 764 uA","sp-out",/764(\.\d)? µA/);

console.log("\n== Via extras ==");
const V=["via-d","via-tp","via-h","via-dt","via-pad","via-anti","via-er","via-i","via-n","via-arlimit","via-stub"];
clearAll(V); set("via-d","0.3"); set("via-pad","0.6"); set("via-anti","1.0"); set("via-i","3"); set("via-n","10");
calcVia();
has("aspect ratio 5.33","via-out",/5\.33 : 1/);
has("lumped sqrt(L/C) 47.6","via-out",/47\.6 Ω/);
has("model limit 5.834 GHz","via-out",/5\.83[0-9] GHz/);
has("10 vias 16.1 K/W","via-out",/16\.[01]/);
has("mutual coupling caveat","via-out",/mutual coupling/);
has("3 A dissipation","via-out",/972(\.\d)? µW|9\.7[23] mW/);
set("via-arlimit","4"); calcVia();
has("aspect ratio limit flagged","via-out",/above the 4:1 limit/);
clearAll(V); set("via-d","0.3"); set("via-stub","1.2"); calcVia();
has("stub null reported","via-out",/Stub quarter-wave null/);

console.log("\n== Fusing multiplier and duration warning ==");
clearAll(["fu-w","fu-t","fu-ta","fu-k"]); set("fu-w","1"); set("fu-t","1"); calcFuse();
has("baseline 10.1 A","fu-out",/10\.1[0-9]* A/);
set("fu-k","0.7"); calcFuse();
has("multiplier applied","fu-out",/7\.0[0-9]* A/);
clearAll(["fu-w","fu-t","fu-k"]); set("fu-w","1"); set("fu-t","10"); calcFuse();
has(">5 s warning","fu-out",/not meant for faults beyond/);

console.log("\n== Crystal frequency window ==");
clearAll(["pp-f","pp-ppm","pp-df"]); set("pp-f","16M"); set("pp-ppm","20"); calcPPM();
has("window reported","pp-out",/Frequency window/);
has("window resolves the ppm","pp-out",/15,999,680 … 16,000,320 Hz/);

console.log("\n== Wavelength period and fraction ==");
clearAll(["wl-f","wl-tr","wl-eeff","wl-period"]);
set("wl-period","10n"); set("wl-eeff","4"); calcWave();
has("frequency from period 100 MHz","wl-out",/100 MHz/);
has("lambda 1.499 m","wl-out",/1\.49[89] m/);
document.getElementById("wl-div").value="10"; calcWave();
has("lambda/10","wl-out",/λ\/10/);

console.log("\n== Wire voltage drop ==");
clearAll(["awg-n","awg-len","awg-i","awg-temp","awg-vsupply"]);
set("awg-n","12"); set("awg-len","0.5"); set("awg-i","40"); set("awg-temp","20"); calcAWG();
has("loop resistance 5.21 mohm","awg-out",/5\.21[0-9]* mΩ/);
has("drop 208 mV","awg-out",/208(\.\d)? mV/);
has("loss 8.34 W","awg-out",/8\.3[0-9]* W/);
set("awg-temp","85"); calcAWG();
has("hot drop 262 mV","awg-out",/26[12](\.\d)? mV/);
has("25.5% higher","awg-out",/25\.5 % higher/);
set("awg-vsupply","22.2"); calcAWG();
has("percentage of supply","awg-out",/1\.1[0-9] %/);
document.getElementById("awg-return").value="1"; calcAWG();
has("one-way halves it","awg-out",/One-way/);

console.log("\n== dBm chain ==");
clearAll(["db-in","db-gain","db-att","db-z"]);
set("db-in","-60"); set("db-gain","23"); set("db-att","10"); calcDbm();
has("output -47 dBm","db-out",/-47\.00 dBm/);
has("net gain +13","db-out",/\+13\.00 dB/);
has("output 998.8 uV rms","db-out",/998.[0-9] µV rms/);

console.log("\n== Rect/polar and deg/rad are wired ==");
eq("cv-re exists", hasField("cv-re"), true);
eq("cv-rad exists", hasField("cv-rad"), true);

console.log("\n"+pass+" passed, "+f+" failed");
process.exitCode=f?1:0;
