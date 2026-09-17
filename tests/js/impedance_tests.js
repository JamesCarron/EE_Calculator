let f=0,pass=0;
function eq(l,g,w){ if(String(g)===String(w)){pass++;console.log("  ok   "+l);} else {f++;console.log("  FAIL "+l+": got "+g+" want "+w);} }
function near(l,g,w,t){ if(Math.abs(g-w)<=Math.abs(w)*t/100){pass++;console.log("  ok   "+l+" = "+Number(g.toPrecision(6)));} else {f++;console.log("  FAIL "+l+": got "+g+" want ~"+w);} }
function has(l,id,re){ const t=JSON.stringify(rows(id)); if(re.test(t)){pass++;console.log("  ok   "+l);} else {f++;console.log("  FAIL "+l+" in "+t);} }
const Z=["z-w","z-h","z-er","z-ermask","z-c","z-s","z-f"];
// result labels arrive tag-stripped and entity-encoded, so match on that form
function num(label){ const r=rows("z-out").find(x=>x[0]===label); return r?parseFloat(r[1]):NaN; }
function setStruct(v){ document.getElementById("z-struct").value=v; }

console.log("\n== Microstrip on Hammerstad-Jensen ==");
clearAll(Z); setStruct("ms"); set("z-w","0.3"); set("z-h","0.2"); set("z-er","4.3"); calcZ();
near("Zo 54.33", num("Z0"), 54.33, 0.5);
near("eps_eff 3.2297", num("&epsilon;eff"), 3.2297, 0.5);
near("Tpd 152.3 ps/in", parseFloat(rows("z-out").find(x=>/Propagation/.test(x[0]))[1].match(/\(([\d.]+) ps\/in/)[1]), 152.26, 0.5);
// the whole point of one model: sqrt(L/C) must return Zo
const L = parseFloat(rows("z-out").find(x=>/Inductance/.test(x[0]))[1]);
const C = parseFloat(rows("z-out").find(x=>/Capacitance/.test(x[0]))[1]);
near("sqrt(L/C) recovers Zo", Math.sqrt((L*1e-9)/(C*1e-12)), 54.33, 0.5);
has("states its validity window","z-out",/0\.01 ≤ w\/h ≤ 100/);
clearAll(Z); setStruct("ms"); set("z-w","0.0001"); set("z-h","10"); set("z-er","4.3"); calcZ();
has("outside the window is refused","z-out",/breaks down/);

console.log("\n== eps_eff bound holds across widths ==");
for (const w of [0.05,0.1,0.5,1,3]) {
  clearAll(Z); setStruct("ms"); set("z-w",String(w)); set("z-h","0.2"); set("z-er","4.3"); calcZ();
  const ee=num("&epsilon;eff");
  if (ee>=2.65 && ee<4.3) { pass++; } else { f++; console.log("  FAIL bound at w="+w+": "+ee); }
}
console.log("  ok   (er+1)/2 <= eps_eff < er at every width tested");

console.log("\n== Covered microstrip gives a bracket, not an invented number ==");
clearAll(Z); setStruct("mscov"); set("z-w","0.3"); set("z-h","0.2"); set("z-er","4.3"); set("z-ermask","3.8"); calcZ();
const zcov=num("Z0");
has("shows the bare comparison","z-out",/Bare, for comparison/);
has("says the true value lies between","z-out",/lies between/);
has("declines to invent a curve","z-out",/invented rather than sourced/);
if (zcov < 54.33) { pass++; console.log("  ok   covering lowers Zo = "+zcov); } else { f++; console.log("  FAIL covering did not lower Zo: "+zcov); }
// cover er = 1 must reproduce bare exactly
set("z-ermask","1"); calcZ();
near("cover er=1 reproduces bare", num("Z0"), 54.33, 0.5);
// cover er = substrate er must give a homogeneous medium
set("z-ermask","4.3"); calcZ();
near("cover er=er gives eps_eff = er", num("&epsilon;eff"), 4.3, 0.5);

console.log("\n== Offset stripline is normalised at the centre ==");
clearAll(Z); setStruct("sl"); set("z-w","0.2"); set("z-h","1.0"); set("z-er","4.3"); calcZ();
const zsym=num("Z0");
near("symmetric 65.87", zsym, 65.87, 0.5);
// h = c must reproduce the symmetric value for the same total spacing
clearAll(Z); setStruct("asym"); set("z-w","0.2"); set("z-h","0.4825"); set("z-c","0.4825"); set("z-er","4.3"); calcZ();
near("h = c reproduces symmetric", num("Z0"), zsym, 1.0);
// and moving off centre must LOWER it, which the raw IPC formula got backwards
let prev=1e9, mono=true;
for (const h of [0.4825,0.4,0.3,0.2,0.1]) {
  clearAll(Z); setStruct("asym"); set("z-w","0.2"); set("z-h",String(h)); set("z-c",String(0.965-h)); set("z-er","4.3"); calcZ();
  const z=num("Z0");
  if (z>prev+1e-9) mono=false;
  prev=z;
}
eq("moving off centre always lowers Zo", mono, true);

console.log("\n== Grounded coplanar ==");
clearAll(Z); setStruct("cpwg"); set("z-w","0.3"); set("z-s","0.2"); set("z-h","0.2"); set("z-er","4.3"); calcZ();
near("cpwg 55.95", num("Z0"), 55.95, 1.0);
near("eps_eff 3.066", num("&epsilon;eff"), 3.066, 1.0);
has("flags the zero-thickness assumption","z-out",/zero-thickness/);

console.log("\n== Dispersion ==");
clearAll(Z); setStruct("ms"); set("z-w","0.3"); set("z-h","0.2"); set("z-er","4.3"); set("z-f","10G"); calcZ();
has("Kirschning-Jansen applied","z-out",/Kirschning/);
const ee10=num("&epsilon;eff");
if (ee10>3.2297 && ee10<4.3) { pass++; console.log("  ok   dispersion raises eps_eff but stays below er = "+ee10); }
else { f++; console.log("  FAIL dispersion out of bounds: "+ee10); }

console.log("\n"+pass+" passed, "+f+" failed");
process.exitCode=f?1:0;
