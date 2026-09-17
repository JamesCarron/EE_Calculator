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

console.log("\n== dBm and volts ==");
const DBM = ["dbm-p","dbm-w","dbm-z","dbm-vrms","dbm-vpk","dbm-vpp"];
/* interior value: 0 dBm is 1 mW, and into 50 ohms that is 223.6 mV rms */
clearAll(DBM); set("dbm-p","0"); calcDbm();
has("0 dBm is 1 mW","dbm-out",/1 mW/);
has("223.6 mV rms into 50 ohms","dbm-out",/223\.[56] mV rms/);
has("peak is root two above rms","dbm-out",/316\.[12] mV peak/);
has("peak-to-peak is twice the peak","dbm-out",/632\.[45] mV peak-to-peak/);
has("and 106.99 dBuV, the 50 ohm offset quoted as 107","dbm-out",/106\.99 dB&micro;V/);
eq("V rms is written back into its box",
   /223\.[56]/.test(document.getElementById("dbm-vrms").value), true);

/* identity: feed the computed voltage back in and the power comes back out */
clearAll(DBM); set("dbm-vrms","0.2236"); calcDbm();
has("223.6 mV rms round-trips to 0 dBm","dbm-out",/-?0\.00 dBm/);
clearAll(DBM); set("dbm-vpp","0.6325"); calcDbm();
has("so does the peak-to-peak figure","dbm-out",/-?0\.00 dBm/);

/* the impedance is a real parameter, not decoration */
clearAll(DBM); set("dbm-p","0"); set("dbm-z","75"); calcDbm();
has("0 dBm into 75 ohms is a higher voltage","dbm-out",/273\.[89] mV rms/);
has("and the dBuV offset moves with it","dbm-out",/108\.7[0-9]* dB&micro;V/);

/* monotonic in power, by the right factor: +20 dB is ten times the voltage */
/* val(), not parseFloat: the box holds engineering notation ("223.61m"), and
   parseFloat reads that as 223.61 without a murmur */
clearAll(DBM); set("dbm-p","20"); calcDbm();
const v20 = val("dbm-vrms");
clearAll(DBM); set("dbm-p","0"); calcDbm();
const v0 = val("dbm-vrms");
/* the boxes carry display precision, not full precision, so compare loosely */
eq("+20 dB is ten times the voltage", Math.abs(v20 / v0 - 10) < 1e-3, true);

/* zero power has no dBm, and an empty card says nothing rather than NaN */
clearAll(DBM); set("dbm-w","0"); calcDbm();
has("zero power is refused, not reported as -Infinity","dbm-out",/above zero/);
clearAll(DBM); calcDbm();
eq("an untouched card is blank", document.getElementById("dbm-out").innerHTML, "");

console.log("\n== Rect/polar and deg/rad are wired ==");
eq("cv-re exists", hasField("cv-re"), true);
eq("cv-rad exists", hasField("cv-rad"), true);

console.log("\n"+pass+" passed, "+f+" failed");
process.exitCode=f?1:0;
