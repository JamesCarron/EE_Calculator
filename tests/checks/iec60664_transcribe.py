"""Transcribe KiCad's IEC 60664-1 lookup tables into JavaScript.

Written 2026-09-15 for C:\\Auterion\\Tools\\EE_Calculator. The tables in
IEC 60664-1:2020-05 are the substance of a clearance/creepage calculator, and
they run to several hundred rows. Retyping them by hand would introduce errors
that no test could catch, so they are translated mechanically from KiCad's
`pcb_calculator/calculator_panels/iec60664.cpp` (GPL-3.0; the user reviewed and
authorised this source).

The C++ is a plain ladder of `if( x <= n ) return v;` inside switch/if blocks,
so the translation is token-for-token and preserves the control flow exactly -
including the cumulative pollution-degree blocks, where a PD1 lookup that runs
past its voltage range falls through into the PD2 block and onwards.

Verified by round-tripping every table row: see iec_tests.js.

Usage: python iec60664_transcribe.py  (prints the JS to stdout)
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

SRC = REPO / "tests" / ".work" / "iec60664.cpp"

# the functions Compute() actually needs, and the JS name each becomes
WANTED = [
    ("GetMinGrooveWidth", "iecGrooveWidth", ["pd", "dist"]),
    ("GetClearanceAltitudeCorrectionFactor", "iecAltitudeFactor", ["alt"]),
    ("GetClearanceToWithstandTransientVoltage", "iecClearanceTransient", ["v", "pd", "field"]),
    ("GetClearanceToWithstandPeaks", "iecClearancePeak", ["v", "field"]),
    ("GetRatedImpulseWithstandVoltage", "iecRatedImpulse", ["v", "ovc"]),
    ("GetBasicCreepageDistance", "iecBasicCreepage", ["v", "pd", "mg", "pcb"]),
]

TOKENS = [
    (r"POLLUTION_DEGREE::PD(\d)", r"\1"),
    (r"MATERIAL_GROUP::MG_IIIb", "4"),
    (r"MATERIAL_GROUP::MG_IIIa", "3"),
    (r"MATERIAL_GROUP::MG_III", "3"),
    (r"MATERIAL_GROUP::MG_II", "2"),
    (r"MATERIAL_GROUP::MG_I", "1"),
    (r"OV_CATEGORY::OV_IV", "4"),
    (r"OV_CATEGORY::OV_III", "3"),
    (r"OV_CATEGORY::OV_II", "2"),
    (r"OV_CATEGORY::OV_I", "1"),
    (r"FIELD::INHOMOGENEOUS", '"inhomogeneous"'),
    (r"FIELD::HOMOGENEOUS", '"homogeneous"'),
    (r"\baVoltage\b", "v"),
    (r"\baDistIso\b", "dist"),
    (r"\baAltitude\b", "alt"),
    (r"\baPD\b", "pd"),
    (r"\baMG\b", "mg"),
    (r"\baField\b", "field"),
    (r"\bm_ratedVoltage\b", "v"),
    (r"\bm_overvoltageCat\b", "ovc"),
    (r"\bm_pcbMaterial\b", "pcb"),
    (r"\bIsPCBmaterial\b", "isPcb"),
    (r"\babs\(", "Math.abs("),
    (r"\bbool\b", "let"),
    (r"\bdouble\b", "let"),
]


def body_of(src, cpp_name):
    """The brace-balanced body of one IEC60664 member function."""
    i = src.index("IEC60664::" + cpp_name)
    start = src.index("{", i)
    depth, j = 0, start
    while True:
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    return src[start + 1:j]


def translate(body):
    out = []
    for line in body.splitlines():
        for pat, rep in TOKENS:
            line = re.sub(pat, rep, line)
        # C++ switch cases on enums become plain values; comparisons are the same
        line = line.replace("switch( ", "switch (").replace(" )", ")")
        line = line.replace("if( ", "if (")
        out.append(line.rstrip())
    # collapse the runs of blank lines the extraction leaves behind
    text = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip("\n")


def main():
    src = SRC.read_text(encoding="utf-8")
    parts = ["""/* ---------- IEC 60664-1 clearance and creepage ----------

   The tables are IEC 60664-1:2020-05 and they are the calculator: several
   hundred rows across impulse withstand, clearance against transient and
   peak voltage, and basic creepage by pollution degree and material group.
   They were transcribed mechanically from KiCad's implementation rather than
   retyped, because a typo in a safety table is not something a unit test
   would catch. See iec60664_transcribe.py.

   The pollution-degree blocks are cumulative on purpose: a PD1 lookup whose
   voltage runs past the PD1 rows falls through into PD2 and onwards, which is
   how the standard's tables are laid out. */
"""]
    for cpp, js, args in WANTED:
        parts.append("function %s(%s) {\n%s\n}\n" % (js, ", ".join(args),
                                                     translate(body_of(src, cpp))))
    sys.stdout.write("\n".join(parts))


if __name__ == "__main__":
    main()
