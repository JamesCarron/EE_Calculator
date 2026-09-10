"""Inject the house tokens + webfonts into a self-contained HTML page.

Written 2026-08-26; vendored into this tool 2026-09-10 so the page has no
dependency outside its own folder.

    from theme_inline import inline_into
    html = inline_into(html)          # adds <style> right after <head>

Why the fonts are embedded
--------------------------
The tool emits ONE self-contained HTML file -- no external stylesheet, no
network -- so the page carries its own copy of the stylesheet and of the two
webfaces, base64'd as `data:` URIs (~124 KB total, latin subset). That is the
price of a page that keeps its typography when it is emailed or moved. If the
.woff2 files are missing the CSS still works and the page falls back to Segoe
UI -- `inline_into` says so on stderr rather than failing.

`Inter Tight` is the display/heading face and `Inter` the body face. Do not
collapse them into one stack.
"""

from __future__ import annotations

import base64
import re
import sys
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent / "theme"
CSS = HERE / "theme.css"
FONTS = ("InterTight.woff2", "Inter.woff2")


@lru_cache(maxsize=2)
def css_with_fonts(embed: bool = True) -> str:
    """The stylesheet, with the @font-face URLs turned into data: URIs.

    `embed=False` returns it untouched, for a page that will sit next to the
    .woff2 files and can just reference them.
    """
    css = CSS.read_text(encoding="utf-8")
    if not embed:
        return css
    for name in FONTS:
        f = HERE / name
        if not f.exists():
            print(f"theme_inline: {name} missing - that face will fall back",
                  file=sys.stderr)
            continue
        uri = "data:font/woff2;base64," + base64.b64encode(f.read_bytes()).decode("ascii")
        css = css.replace(f'url("{name}")', f"url({uri})")
    return css


def inline_into(html: str, embed_fonts: bool = True) -> str:
    """Return `html` with the house stylesheet inserted as the FIRST style block.

    First, deliberately: the page's own rules must win over the house defaults,
    so the page can override a token or a component without fighting
    specificity.

    Idempotent -- a page that already carries the marker is returned unchanged.
    """
    marker = "<!--house-css-->"
    if marker in html:
        return html
    css = css_with_fonts(embed_fonts)
    if "</style" in css.lower():
        raise ValueError("theme.css contains </style - cannot inline safely")
    block = f"{marker}\n<style>\n{css}\n</style>\n"

    m = re.search(r"<head[^>]*>", html, re.I)
    if m:
        return html[:m.end()] + "\n" + block + html[m.end():]
    m = re.search(r"<html[^>]*>", html, re.I)
    if m:
        return html[:m.end()] + "\n" + block + html[m.end():]
    return block + html


if __name__ == "__main__":
    css = css_with_fonts()
    embedded = sum(1 for n in FONTS if (HERE / n).exists())
    print(f"theme.css {CSS.stat().st_size:,} bytes -> {len(css):,} with "
          f"{embedded}/{len(FONTS)} fonts embedded")
