"""Build a node harness around the page JS with a DOM stub good enough to
exercise the computed-field mechanics (value + classList are real)."""
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

html = (REPO / "EE_Calculator.html").read_text(encoding="utf-8")
js = re.search(r"<script>\n(.*?)</script>", html, re.S).group(1)
core = js.split("/* ---------- wiring ---------- */")[0]

# element ids the page defines, so the stub can pre-create them
# ids are also built in JS (id="' + hostId + '-cursor"), so keep only literals
ids = sorted({i for i in re.findall(r'id="([^"]+)"', html)
              if re.fullmatch(r"[A-Za-z][\w-]*", i)})
selects = dict(re.findall(r'<select id="([^"]+)"[^>]*>(.*?)</select>', html, re.S))
mirrors = {}
for tag in re.findall(r"<(?:input|select)[^>]*>", html):
    mid = re.search(r'id="([^"]+)"', tag)
    grp = re.search(r'data-mirror="([^"]+)"', tag)
    if mid and grp:
        mirrors.setdefault(grp.group(1), []).append(mid.group(1))
defaults = {}
for sid, body in selects.items():
    m = re.search(r'<option value="([^"]+)"[^>]*\bselected\b', body)
    if not m:
        m = re.search(r'<option value="([^"]+)"', body)
    defaults[sid] = m.group(1) if m else ""

# Checkboxes: id -> whether the markup ticks it. The page relies on these
# defaults (resistor drift off, regulator on), so the harness must start where
# the browser starts or every suite silently tests a different card.
checkids = {}
for m in re.finditer(r'<input([^>]*\btype="checkbox"[^>]*)>', html):
    attrs = m.group(1)
    mid = re.search(r'id="([^"]+)"', attrs)
    if mid:
        checkids[mid.group(1)] = bool(re.search(r'\bchecked\b', attrs))

stub = """
'use strict';
const els = {};
function mkEl(id) {
  const cls = new Set();
  return {
    id: id, value: "", innerHTML: "", textContent: "", className: "", hidden: true,
    checked: false,
    type: %(checkids)s.hasOwnProperty(id) ? "checkbox" : "text",
    tagName: %(selids)s.indexOf(id) >= 0 ? "SELECT" : "INPUT",
    classList: {
      add: function () { for (const c of arguments) cls.add(c); },
      remove: function () { for (const c of arguments) cls.delete(c); },
      contains: function (c) { return cls.has(c); },
      toggle: function (c, on) { if (on === undefined) on = !cls.has(c); if (on) cls.add(c); else cls.delete(c); return on; }
    },
    _cls: cls,
    querySelector: function () { return null; },
    querySelectorAll: function () { return { forEach: function () {} }; },
    setAttribute: function (k, v) { this[k] = v; },
    getAttribute: function (k) { return this[k]; },
    getBoundingClientRect: function () { return { left: 0, top: 0, width: 560, height: 210 }; },
    addEventListener: function () {},
    options: []
  };
}
const PAGE_IDS = new Set(%(ids)s);      // ids the real page actually defines
function hasField(id) { return PAGE_IDS.has(id); }
%(ids)s.forEach(function (i) { els[i] = mkEl(i); });
const SEL_DEFAULTS = %(defaults)s;
for (const k in SEL_DEFAULTS) els[k].value = SEL_DEFAULTS[k];
const CHECK_DEFAULTS = %(checkids)s;
for (const k in CHECK_DEFAULTS) if (els[k]) els[k].checked = CHECK_DEFAULTS[k];
const MIRRORS = %(mirrors)s;         // group -> ids, in document order
for (const g in MIRRORS) MIRRORS[g].forEach(function (i) { els[i].dataset = { mirror: g }; });
globalThis.document = {
  getElementById: function (i) { return els[i] || (els[i] = mkEl(i)); },
  querySelectorAll: function (sel) {
    const m = /^\[data-mirror="(\w+)"\]$/.exec(sel || "");
    const list = m ? (MIRRORS[m[1]] || []).map(function (i) { return els[i]; }) : [];
    list.forEach = Array.prototype.forEach.bind(list);
    return list;
  },
  createElement: mkEl,
  body: { appendChild: function () {}, removeChild: function () {} },
  addEventListener: function () {}
};
globalThis.location = { hash: "" };
try { globalThis.navigator = {}; } catch (e) {}

// test helpers
function set(id, v) {
  const e = document.getElementById(id);
  /* one spelling in the suites whatever the control is: "on"/"off", true/false
     and 1/0 all tick a checkbox, and anything else is a value */
  if (e.type === "checkbox") { e.checked = (v === true || v === "on" || v === 1 || v === "1"); return; }
  e.value = String(v); e.classList.remove("computed");
}
function get(id) { return document.getElementById(id).value; }
function isCalc(id) { return document.getElementById(id).classList.contains("computed"); }
function clearAll(ids) {
  ids.forEach(function (i) {
    const e = document.getElementById(i);
    /* a checkbox goes back to what the markup says, not to false: the card's
       default state is part of what the suites are checking */
    if (e.type === "checkbox") { e.checked = !!CHECK_DEFAULTS[i]; return; }
    e.value = ""; e.classList.remove("computed");
  });
}
function rows(id) {
  const h = document.getElementById(id).innerHTML;
  const out = [];
  const re = /<dt>(.*?)<\\/dt><dd[^>]*>(.*?)<\\/dd>/g;
  let m;
  while ((m = re.exec(h))) out.push([m[1].replace(/<[^>]+>/g, ""), m[2].replace(/<[^>]+>/g, "")]);
  return out;
}
function show(t, id) { console.log(t, JSON.stringify(rows(id))); }
""" % {
    "ids": repr(ids).replace("'", '"'),
    "selids": repr(sorted(selects)).replace("'", '"'),
    "checkids": json.dumps(checkids),
    "mirrors": "{" + ",".join('"%s":[%s]' % (g, ",".join('"%s"' % i for i in ids)) for g, ids in mirrors.items()) + "}",
    "defaults": "{" + ",".join('"%s":"%s"' % (k, v) for k, v in defaults.items()) + "}",
}

out = REPO / "tests" / ".work" / "harness.js"
out.write_text(stub + "\n" + core, encoding="utf-8")
print("harness written:", out, len(stub) + len(core), "chars")
