"""Execute the page's ENTIRE script, wiring included, and fail on any error.

Written 2026-09-10 for C:\\Auterion\\Tools\\EE_Calculator. It exists because the
node test harness deliberately stops at the wiring section, so nothing was
executing the top-level code that builds the card footers, attaches listeners
and restores the last tab. A `const` declared after the code that reads it is
a temporal-dead-zone ReferenceError that kills the whole script at load; that
bug reached the built page once and only the browser would have shown it, and
the browser was not available.

This is a load check, not a behaviour check: it asks whether the script runs to
completion, not whether the answers are right. The DOM stub is deliberately
permissive - unknown elements return a generic node rather than null - because
the point is to reach the end of the file, not to model a browser.

Verified by moving a `const` below its first use and confirming the failure.

Usage: python load_check.py
"""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

HTML = REPO / "EE_Calculator.html"
OUT = REPO / "tests" / ".work" / "load_check.js"

STUB = r"""
'use strict';
/* A permissive DOM: every node answers every call, so execution reaches the
   end of the script instead of stopping at the first unmodelled method. */
function mkNode(tag, id) {
  const cls = new Set();
  const node = {
    tagName: (tag || "div").toUpperCase(), id: id || "", value: "", innerHTML: "",
    textContent: "", className: "", hidden: false, placeholder: "", title: "", type: "",
    dataset: {}, style: {}, options: [], selectedIndex: 0, children: [], parentNode: null,
    classList: {
      add: function () { for (const c of arguments) cls.add(c); },
      remove: function () { for (const c of arguments) cls.delete(c); },
      contains: function (c) { return cls.has(c); },
      toggle: function (c, on) { if (on === undefined) on = !cls.has(c); if (on) cls.add(c); else cls.delete(c); return on; }
    },
    addEventListener: function () {}, removeEventListener: function () {},
    appendChild: function (c) { this.children.push(c); c.parentNode = this; return c; },
    insertBefore: function (c) { this.children.push(c); c.parentNode = this; return c; },
    insertAdjacentHTML: function () {}, remove: function () {},
    setAttribute: function () {}, getAttribute: function () { return null; },
    removeAttribute: function () {}, hasAttribute: function () { return false; },
    querySelector: function () { return mkNode("div"); },
    querySelectorAll: function () { return []; },
    closest: function () { return mkNode("div"); },
    focus: function () {}, blur: function () {}, click: function () {},
    showModal: function () {}, close: function () {}, scrollIntoView: function () {},
    getBoundingClientRect: function () { return { left: 0, top: 0, width: 600, height: 200 }; }
  };
  return node;
}

const REGISTRY = {};
const IDS = __IDS__;
const SELECT_OPTIONS = __SELECTS__;
IDS.forEach(function (id) {
  const isSelect = Object.prototype.hasOwnProperty.call(SELECT_OPTIONS, id);
  const n = mkNode(isSelect ? "select" : "input", id);
  if (isSelect) {
    n.value = SELECT_OPTIONS[id];
    n.options = [{ value: SELECT_OPTIONS[id], textContent: SELECT_OPTIONS[id] }];
  }
  REGISTRY[id] = n;
});

const document = {
  getElementById: function (id) { return REGISTRY[id] || null; },
  querySelector: function () { return mkNode("div"); },
  querySelectorAll: function (sel) {
    /* the footer builder walks every reset button, so hand it one per card */
    if (/button\.reset/.test(sel)) {
      return __RESETS__.map(function (r) {
        const b = mkNode("button");
        b.dataset = { reset: r };
        b.parentNode = mkNode("div");
        return b;
      });
    }
    return [];
  },
  createElement: function (t) { return mkNode(t); },
  addEventListener: function () {},
  body: mkNode("body"),
  documentElement: mkNode("html")
};
const window = {
  addEventListener: function () {}, matchMedia: function () { return { matches: false, addEventListener: function () {} }; },
  location: { hash: "", href: "" }, getComputedStyle: function () { return {}; },
  requestAnimationFrame: function (f) { f(0); }
};
const navigator = { clipboard: { writeText: function () { return Promise.resolve(); } } };
const localStorage = {
  _d: {}, getItem: function (k) { return this._d[k] === undefined ? null : this._d[k]; },
  setItem: function (k, v) { this._d[k] = String(v); }, removeItem: function (k) { delete this._d[k]; }
};
const location = window.location;
"""


def main():
    html = HTML.read_text(encoding="utf-8")
    js = re.search(r"<script>\n(.*?)</script>", html, re.S).group(1)

    ids = sorted({i for i in re.findall(r'id="([^"]+)"', html)
                  if re.fullmatch(r"[A-Za-z][\w-]*", i)})
    selects = {}
    for sid, body in re.findall(r'<select id="([^"]+)"[^>]*>(.*?)</select>', html, re.S):
        m = re.search(r'<option value="([^"]*)"[^>]*\bselected\b', body) or \
            re.search(r'<option value="([^"]*)"', body)
        selects[sid] = m.group(1) if m else ""
    resets = sorted(set(re.findall(r'data-reset="(\w+)"', html)))

    import json
    stub = (STUB.replace("__IDS__", json.dumps(ids))
                .replace("__SELECTS__", json.dumps(selects))
                .replace("__RESETS__", json.dumps(resets)))
    OUT.write_text(stub + "\n" + js + "\nconsole.log('SCRIPT REACHED THE END');\n", encoding="utf-8")

    res = subprocess.run(["node", str(OUT)], capture_output=True, text=True, encoding="utf-8")
    ok = "SCRIPT REACHED THE END" in (res.stdout or "")
    if ok:
        print("the whole script, wiring included, runs to completion")
        sys.exit(0)
    print("the script did not reach the end:\n")
    print((res.stderr or res.stdout or "").strip()[:2000])
    sys.exit(1)


if __name__ == "__main__":
    main()
