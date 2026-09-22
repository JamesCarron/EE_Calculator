# Vendored files

`theme/` and `theme_inline.py` are copies of the Auterion house brand material, taken so this repo builds a fully self-contained page on a machine that does not have the `Tools` tree.

| File | Source | Copied |
|---|---|---|
| `theme/theme.css` | `C:\Auterion\Tools\brand\auterion.css` | 2026-09-10 |
| `theme/Inter.woff2`, `theme/InterTight.woff2` | `C:\Auterion\Tools\brand\` | 2026-08-14 |
| `theme_inline.py` | `C:\Auterion\Tools\brand\auterion_inline.py` | 2026-08-26 |

The copy has drifted: `theme.css` is 13.6 KB against 21 KB upstream, so brand fixes made since 2026-09-10 are not in this page. That is the cost of vendoring and the reason this file exists.

## How to refresh

Copy `auterion.css` over `theme/theme.css` and the two `.woff2` files over their counterparts, copy `auterion_inline.py` over `theme_inline.py` keeping the `from eecalc.vendor.theme_inline import inline_into` line in its docstring, then `pixi run test` and re-check the page in a browser: a stylesheet change alters every card, chart and diagram, which is exactly the case the repo's CLAUDE.md requires a browser pass for. Record the new date above.

Declared 2026-09-17 during the house-layout refactor; see `docs/private/Refactor_Plan.md`.
