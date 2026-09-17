"""Static integrity check of the generated EE_Calculator page."""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

html = (REPO / "EE_Calculator.html").read_text(encoding="utf-8")
js = re.search(r"<script>\n(.*?)</script>", html, re.S).group(1)

ids = set(re.findall(r'id="([^"]+)"', html))
refs = set(re.findall(r'getElementById\("([^"]+)"\)', js))
listed = set()
for m in re.finditer(r'inputs:\s*\[([^\]]*)\]', js):
    listed |= set(re.findall(r'"([^"]+)"', m.group(1)))
for m in re.finditer(r'NB_FIELDS = \[(.*?)\];', js, re.S):
    listed |= set(re.findall(r'"([^"]+)"', m.group(1)))
for m in re.finditer(r'wirePair\(\[(.*?)\]\);', js, re.S):
    listed |= set(re.findall(r'\["([a-z]{2}-[a-z0-9]+)"', m.group(1)))

missing = sorted((refs | listed) - ids)
print("referenced but absent:", missing or "none")

tabs = set(re.findall(r'data-tab="([^"]+)"', html))
panels = set(re.findall(r'id="panel-([^"]+)"', html))
subs = set(re.findall(r'data-sub="([^"]+)"', html))
subpanels = set(re.findall(r'id="sub-([^"]+)"', html))
print("tabs:", sorted(tabs))
print("tabs<->panels mismatch:", sorted(tabs ^ panels) or "none")
print("subs:", sorted(subs), "| mismatch:", sorted(subs ^ subpanels) or "none")

resets = set(re.findall(r'data-reset="([^"]+)"', html))
calcs = set(re.findall(r'^\s+(\w+):\s*\{ calc:', js, re.M))
print("reset without CALCS entry:", sorted(resets - calcs) or "none")
print("CALCS without a card:", sorted(calcs - resets) or "none")

# every calc function named in CALCS must be defined
named = set(re.findall(r'calc:\s*(calc\w+)', js))
defined = set(re.findall(r'function (calc\w+)\(', js))
print("called but undefined:", sorted(named - defined) or "none")

print("branding leak:", html.lower().count("auterion"))
print("page bytes:", len(html))

# ---- every card that reads a shared value must also SHOW that control ----
import re as _re

# the page's markup and JavaScript are real files since the 2026-09-17 template split
src = (REPO / "src" / "eecalc" / "static" / "page.js").read_text(encoding="utf-8")
_markup = (REPO / "src" / "eecalc" / "templates" / "page.html").read_text(encoding="utf-8")
_js = src[src.index("/* ---------- value parsing"):]
_funcs = {}
for _m in _re.finditer(r"function (calc\w+)\(\) \{", _js):
    _d, _i = 1, _m.end()
    while _d and _i < len(_js):
        _d += (_js[_i] == "{") - (_js[_i] == "}")
        _i += 1
    _funcs[_m.group(1)] = _js[_m.end():_i]
_TOK = {"gCopperMM()": "copper", "gTempRise()": "dt", "gAmbient()": "ta", "gSeries()": "series"}
_calcs = dict(_re.findall(r"^\s+(\w+):\s*\{ calc: (calc\w+)", src, _re.M))
# nb, rt and cv register an inline function rather than a named one
_all_cards = set(_calcs) | set(_re.findall(r"^\s+(\w+):\s*\{ calc: ", src, _re.M))
_card_of = {v: k for k, v in _calcs.items()}
_html = _markup[_markup.index('<main class="wrap">'):_markup.index("</main>")]
_cards = {}
for _m in _re.finditer(r'<div class="card">(.*?)data-reset="(\w+)"', _html, _re.S):
    _cards[_m.group(2)] = set(_re.findall(r'data-mirror="(\w+)"', _m.group(1)))
_bad = []
for _n, _b in _funcs.items():
    _card = _card_of.get(_n)
    if not _card: continue
    for _t, _g in _TOK.items():
        if _t in _b and _g not in _cards.get(_card, set()):
            _bad.append(_card + " reads " + _g + " but does not show it")
_groups = {}
for _c, _gs in _cards.items():
    for _g in _gs: _groups.setdefault(_g, []).append(_c)
print("shared controls:", {k: len(v) for k, v in sorted(_groups.items())})
print("every card that reads a shared value shows it:", "yes" if not _bad else "NO -> " + "; ".join(_bad))

# Every card carries an Explain entry, and every entry belongs to a card.
# A card that ships without one is the failure this catches; the length and
# tag-balance checks catch a stub or a truncated paste.
_help = _re.search(r"const HELP = (\{.*?\n\});", src, _re.S)
if not _help:
    print("card explanations: NONE FOUND")
else:
    import json as _json
    _H = _json.loads(_help.group(1))
    _missing = sorted(_all_cards - set(_H))
    _orphan = sorted(set(_H) - _all_cards)
    _thin = sorted(k for k, v in _H.items() if len(v["body"]) < 400)
    _unbalanced = []
    for _k, _v in _H.items():
        for _tag in ("p", "ul", "li", "span", "b", "i", "code"):
            # an opening tag may carry attributes, so match "<p>" and "<span class=..."
            if (len(_re.findall(r"<%s[ >]" % _tag, _v["body"]))
                    != _v["body"].count("</%s>" % _tag)):
                _unbalanced.append("%s:%s" % (_k, _tag))
    print("card explanations: %d, shortest %d chars"
          % (len(_H), min(len(v["body"]) for v in _H.values())))
    print("  cards without one:", ", ".join(_missing) or "none")
    print("  entries without a card:", ", ".join(_orphan) or "none")
    print("  too thin to be useful:", ", ".join(_thin) or "none")
    print("  unbalanced markup:", ", ".join(_unbalanced) or "none")
