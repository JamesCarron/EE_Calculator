"""Geometry lint for every diagram in the EE Calculator page.

Written 2026-09-10 for C:\\Auterion\\Tools\\EE_Calculator while adding Saturn-style
parameter diagrams. It exists because the drawings are hand-placed SVG: nothing
throws when a label lands outside the viewBox or on top of another one, so the
only other way to catch it is to open the page and look, which does not survive
into CI and was unavailable when the Chrome extension refused file:// URLs.

Checks, over the static <svg class="schem"> blocks in the generated HTML *and*
the SVG that the switching draw* functions produce for every mode:

  1. every coordinate lies inside the viewBox
  2. no two horizontal text labels overlap, and no line runs through one
  3. each switching drawing actually differs between its modes, and carries the
     symbol unique to the mode it is drawing

Verified by deliberately moving a label outside the viewBox and off another
label, and confirming each check fails.

Usage: python eecalc_diagram_check.py
"""

import json
import re
import subprocess
import sys
from pathlib import Path

HTML = Path(r"C:\Auterion\Tools\EE_Calculator\EE_Calculator.html")
SCRATCH = Path(r"C:\Auterion\Tools\EE_Calculator\test\.work")
HARNESS = SCRATCH / "harness.js"

# the switching drawings, and the substring each mode must carry
MODES = [
    ("drawZ", "z-diagram", [("ms", ">w<"), ("mscov", "cover"), ("sl", ">b<"),
                            ("asym", ">c<"), ("cpwg", "ground pour")]),
    ("drawDiff", "dp-diagram", [("ms", "reference plane"), ("sl", "Planes above and below")]),
    ("drawTrace", "tw-diagram", [("ext", "k = 0.048"), ("int", "k = 0.024")]),
    ("drawVia", "via-diagram", [(True, "stub"), (False, "stub: none given")]),
    ("drawSP", "sp-diagram", [("R", "Series"), ("C", "1/C"), ("L", "Parallel")]),
    ("drawPad", "pad-diagram", [("pi", "PI pad"), ("t", "T pad"), ("bridge", "bridging"),
                                ("l", "L pad"), ("split", "out 1")]),
]

NUM = r"-?\d*\.?\d+"


def path_points(d):
    """Coordinates from a path, handling the M/L/H/V/A/Z subset we emit."""
    pts, x, y = [], 0.0, 0.0
    for cmd, body in re.findall(r"([MLHVAZ])([^MLHVAZ]*)", d):
        n = [float(v) for v in re.findall(NUM, body)]
        if cmd == "M" or cmd == "L":
            for i in range(0, len(n) - 1, 2):
                x, y = n[i], n[i + 1]
                pts.append((x, y))
        elif cmd == "H":
            for v in n:
                x = v
                pts.append((x, y))
        elif cmd == "V":
            for v in n:
                y = v
                pts.append((x, y))
        elif cmd == "A":
            for i in range(0, len(n) - 6, 7):
                x, y = n[i + 5], n[i + 6]
                pts.append((x, y))
    return pts


def text_box(tag, body):
    """An approximate box for a text label; mono, so width tracks length."""
    x = float(re.search(r'x="(%s)"' % NUM, tag).group(1))
    y = float(re.search(r'y="(%s)"' % NUM, tag).group(1))
    fs = re.search(r'font-size="(%s)"' % NUM, tag)
    size = float(fs.group(1)) if fs else 11.0
    plain = re.sub(r"<[^>]+>", "", body)
    plain = re.sub(r"&[#\w]+;", "x", plain)
    w = len(plain) * size * 0.58
    anchor = re.search(r'text-anchor="(\w+)"', tag)
    if anchor and anchor.group(1) == "middle":
        x -= w / 2
    elif anchor and anchor.group(1) == "end":
        x -= w
    return x, y - size, x + w, y + 2


def path_segments(d):
    """Axis-aligned segments from a path, as (x0, y0, x1, y1)."""
    segs, x, y = [], 0.0, 0.0
    for cmd, body in re.findall(r"([MLHVAZ])([^MLHVAZ]*)", d):
        n = [float(v) for v in re.findall(NUM, body)]
        if cmd == "M":
            for i in range(0, len(n) - 1, 2):
                if i:
                    segs.append((x, y, n[i], n[i + 1]))
                x, y = n[i], n[i + 1]
        elif cmd == "L":
            for i in range(0, len(n) - 1, 2):
                segs.append((x, y, n[i], n[i + 1]))
                x, y = n[i], n[i + 1]
        elif cmd == "H":
            for v in n:
                segs.append((x, y, v, y))
                x = v
        elif cmd == "V":
            for v in n:
                segs.append((x, y, x, v))
                y = v
    return segs


def crosses(box, seg):
    """Does an axis-aligned segment pass through a text box?"""
    x0, y0, x1, y1 = box
    ax, ay, bx, by = seg
    if abs(ay - by) < 0.01:                       # horizontal
        return y0 < ay < y1 and min(ax, bx) < x1 - 1 and max(ax, bx) > x0 + 1
    if abs(ax - bx) < 0.01:                       # vertical
        return x0 < ax < x1 and min(ay, by) < y1 - 1 and max(ay, by) > y0 + 1
    return False


def check(name, svg):
    """Return a list of problems with one <svg> block."""
    bad = []
    vb = re.search(r'viewBox="0 0 (%s) (%s)"' % (NUM, NUM), svg)
    if not vb:
        return ["%s: no viewBox" % name]
    W, H = float(vb.group(1)), float(vb.group(2))
    pts = []
    for d in re.findall(r'\sd="([^"]+)"', svg):
        pts += path_points(d)
    for m in re.finditer(r'<rect[^>]*>', svg):
        g = dict(re.findall(r'(\w+)="(%s)"' % NUM, m.group(0)))
        if {"x", "y", "width", "height"} <= set(g):
            x, y = float(g["x"]), float(g["y"])
            pts += [(x, y), (x + float(g["width"]), y + float(g["height"]))]
    for m in re.finditer(r'<circle[^>]*>', svg):
        g = dict(re.findall(r'(\w+)="(%s)"' % NUM, m.group(0)))
        if {"cx", "cy", "r"} <= set(g):
            cx, cy, r = float(g["cx"]), float(g["cy"]), float(g["r"])
            pts += [(cx - r, cy - r), (cx + r, cy + r)]
    for x, y in pts:
        if x < -0.5 or y < -0.5 or x > W + 0.5 or y > H + 0.5:
            bad.append("%s: point (%g, %g) outside the %gx%g viewBox" % (name, x, y, W, H))

    boxes = []
    for tag, body in re.findall(r"(<text[^>]*>)(.*?)</text>", svg, re.S):
        if "transform" in tag:          # the wheel's radial labels; not comparable
            continue
        b = text_box(tag, body)
        if b[0] < -0.5 or b[2] > W + 0.5 or b[1] < -0.5 or b[3] > H + 0.5:
            bad.append("%s: label %r runs outside the viewBox" % (name, re.sub(r"<[^>]+>", "", body)[:24]))
        boxes.append((b, re.sub(r"<[^>]+>", "", body)[:20]))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i][0], boxes[j][0]
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                bad.append("%s: labels %r and %r overlap" % (name, boxes[i][1], boxes[j][1]))

    # A label with a wire or dimension line running through it reads as a
    # mess, and the box-versus-box check above cannot see it. Rectangles are
    # excluded: a label sitting inside one (substrate, junction) is the point.
    segs = []
    for d in re.findall(r'\sd="([^"]+)"', svg):
        segs += path_segments(d)
    for box, label in boxes:
        for seg in segs:
            if crosses(box, seg):
                bad.append("%s: a line runs through the label %r" % (name, label))
                break
    return bad


def dynamic_svgs():
    """Call every switching draw function and collect what it renders."""
    calls = []
    for fn, host, modes in MODES:
        for mode, _ in modes:
            calls.append((fn, host, mode))
    script = [HARNESS.read_text(encoding="utf-8"), "const OUT = {};"]
    for fn, host, mode in calls:
        script.append("%s(%s); OUT[%s] = document.getElementById(%s).innerHTML;"
                      % (fn, json.dumps(mode), json.dumps(fn + ":" + str(mode)), json.dumps(host)))
    script.append("console.log(JSON.stringify(OUT));")
    run = SCRATCH / "diagram_dump.js"
    run.write_text("\n".join(script), encoding="utf-8")
    res = subprocess.run(["node", str(run)], capture_output=True, text=True, encoding="utf-8")
    if res.returncode:
        print(res.stderr[-1500:])
        sys.exit("node failed")
    return json.loads(res.stdout.strip().splitlines()[-1])


def main():
    html = HTML.read_text(encoding="utf-8")
    problems, n = [], 0

    # the page's own JS builds SVG from string literals; only the markup in
    # the body is a real diagram, so stop at the script
    body = html.split("<script>")[0]
    for m in re.finditer(r'<svg class="schem".*?</svg>', body, re.S):
        label = re.search(r'aria-label="([^"]{0,40})', m.group(0))
        n += 1
        problems += check("static/" + (label.group(1) if label else "?"), m.group(0))

    got = dynamic_svgs()
    for key, markup in got.items():
        n += 1
        problems += check(key, markup)

    for fn, host, modes in MODES:
        seen = {}
        for mode, needle in modes:
            markup = got[fn + ":" + str(mode)]
            if needle not in markup:
                problems.append("%s(%s) is missing %r" % (fn, mode, needle))
            if markup in seen.values():
                problems.append("%s(%s) draws the same thing as another mode" % (fn, mode))
            seen[mode] = markup

    print("%d diagrams checked" % n)
    for q in problems:
        print("  FAIL", q)
    print("clean" if not problems else "%d problems" % len(problems))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
