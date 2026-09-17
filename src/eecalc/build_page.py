"""Generate EE_Calculator.html - a self-contained tabbed EE calculator page.

Written 2026-08-26.

All calculator logic is in-page JavaScript because the page is interactive at
runtime with no server; Python here is only the build harness. The house
stylesheet and its two webfonts are inlined via the vendored `theme_inline`
module, so the output works offline, opened straight from the filesystem.

Verified by: building and exercising every tab in a browser (divider results
cross-checked by hand: 12 V, 10k/4k7 -> 3.837 V, 816.3 uA).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# the page is the product, so it is written to the repo root; everything
# that builds it lives under src/eecalc/
OUT = HERE.parents[1] / "EE_Calculator.html"

TEMPLATES = HERE / "templates"
STATIC = HERE / "static"


def load_page() -> str:
    """The page template with its stylesheet and script substituted in.

    Until 2026-09-17 all three lived in one raw string in this file, which cost
    every editor tool that understands HTML, CSS or JavaScript and made backslash
    escaping a standing hazard. They are real files now; this reassembles them
    byte for byte, so the generated page is unchanged.
    """
    page = (TEMPLATES / "page.html").read_text(encoding="utf-8")
    for token, part in (("{{page.css}}", STATIC / "page.css"),
                        ("{{page.js}}", STATIC / "page.js")):
        if token not in page:
            raise AssertionError(f"{token} missing from page.html")
        page = page.replace(token, part.read_text(encoding="utf-8"))
    return page


HTML = load_page()



# The mono face this page uses draws U+221A without its overbar, so in a
# formula plate, an equation block or an SVG label "sqrt(L/C)" renders as
# something an engineer reads as an integral. Those are exactly the places a
# radical appears, so the page writes sqrt() throughout and never the glyph.
# Longest patterns first: the general "radical followed by ( " rule would
# otherwise leave the bare-symbol forms untouched.
RADICALS = [
    ("&radic;&epsilon;<sub>eff</sub>(&epsilon;<sub>r</sub>, cover)",
     "sqrt(&epsilon;<sub>eff</sub>(&epsilon;<sub>r</sub>, cover))"),
    ("&radic;&epsilon;<sub>eff</sub>", "sqrt(&epsilon;<sub>eff</sub>)"),
    ("&radic;&epsilon;<sub>r</sub>", "sqrt(&epsilon;<sub>r</sub>)"),
    ("\u221a\u03b5<sub>eff</sub>", "sqrt(\u03b5<sub>eff</sub>)"),
    ("\u221a\u03b5<sub>r</sub>", "sqrt(\u03b5<sub>r</sub>)"),
    ("√1000 h", "sqrt(1000 h)"),
    ("1/√t", "1/sqrt(t)"),
    ("&radic;(", "sqrt("),
    ("\u221a(", "sqrt("),
]


def write_sqrt(html: str) -> str:
    for old_, new_ in RADICALS:
        html = html.replace(old_, new_)
    assert "&radic;" not in html and "\u221a" not in html, "a radical glyph escaped the rewrite"
    return html


def main() -> None:
    html = write_sqrt(HTML)
    try:
        from eecalc.vendor.theme_inline import inline_into
        html = inline_into(html)
    except ImportError:
        print("build_page: vendor.theme_inline not found - writing page without house styling", file=sys.stderr)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
