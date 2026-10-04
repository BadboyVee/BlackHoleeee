#!/usr/bin/env python3
"""Check that the text on every slide fits its box.

Each paragraph is wrapped the way PowerPoint wraps it, word by word, measured with fonts that
have exactly the widths of Office's: Carlito for Calibri, Caladea for Cambria and Liberation
Sans for Arial (fontconfig finds them). A box fails when a word is wider than the box, or when
its lines are taller than the box. Text boxes, placeholders and table cells are checked; chart
text is left to the chart.

Usage: python check_fit.py deck.pptx [deck.pptx ...]
Prints every box's lines and exits non-zero if any box overflows.
"""
import subprocess
import sys
from functools import lru_cache

from PIL import ImageFont
from pptx import Presentation
from pptx.oxml.ns import qn
from pptx.util import Emu

EMU_PER_PT = 12700
LINE = 1.2                      # line height as a multiple of the font size (single spacing)
BULLET_INDENT = 0.25 * 914400   # the 2013 Office Theme's first-level bullet indent (EMU)


@lru_cache(maxsize=None)
def font(name, bold, size):
    path = subprocess.run(["fc-match", "-f", "%{file}", f"{name}:weight={200 if bold else 80}"],
                          capture_output=True, text=True, check=True).stdout
    return ImageFont.truetype(path, size=int(size * 20))    # 20 units per point, for precision


def width(text, name, bold, size):
    return font(name, bold, size).getlength(text) / 20       # points


def runs_of(paragraph, default_size):
    for run in paragraph.runs:
        f = run.font
        yield run.text, f.name or "Calibri", bool(f.bold), (f.size.pt if f.size else default_size)


def lines_needed(paragraph, box_w, default_size):
    """Greedy word wrap of a paragraph's runs; returns (lines, tallest font size, longest word)."""
    tokens = []
    for text, name, bold, size in runs_of(paragraph, default_size):
        for k, word in enumerate(text.split(" ")):
            tokens.append((word, name, bold, size, k > 0 or (tokens and text.startswith(" "))))
    if not tokens:
        return 0, default_size, 0
    lines, x, tallest, longest = 1, 0.0, max(t[3] for t in tokens), 0.0
    for word, name, bold, size, after_space in tokens:
        w = width(word, name, bold, size)
        gap = width(" ", name, bold, size) if after_space and x > 0 else 0
        longest = max(longest, w)
        if x > 0 and x + gap + w > box_w:
            lines += 1
            x = w
        else:
            x += gap + w
    return lines, tallest, longest


def check_frame(label, frame, box_w, box_h, default_size=18, indent=0):
    """Returns a problem message, or None."""
    need, report = 0.0, []
    paragraphs = [p for p in frame.paragraphs if p.text.strip()]
    for i, para in enumerate(paragraphs):
        lines, size, longest = lines_needed(para, box_w - indent, default_size)
        if longest > box_w - indent:
            return f"{label}: a word in {para.text[:40]!r} is wider than the box"
        need += lines * size * LINE
        if i < len(paragraphs) - 1 and para.space_after is not None:
            need += para.space_after.pt
        report.append(f"{lines} line{'s' if lines > 1 else ''}")
    if need > box_h * 1.02:
        return f"{label}: needs {need:.0f} pt, has {box_h:.0f} pt ({', '.join(report)})"
    return None


def insets(body_pr):
    get = lambda attr, default: int(body_pr.get(attr, default)) if body_pr is not None else default
    return get("lIns", 91440) + get("rIns", 91440), get("tIns", 45720) + get("bIns", 45720)


def check(path):
    problems, boxes = [], 0
    prs = Presentation(path)
    for n, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            label = f"{path.rsplit('/', 1)[-1]} slide {n} '{shape.name}'"
            if shape.has_text_frame and shape.text_frame.text.strip():
                body_pr = shape.text_frame._txBody.find(qn("a:bodyPr"))
                dx, dy = insets(body_pr)
                # The content placeholder's text is bulleted, and indented by the bullet.
                is_body = shape.is_placeholder and shape.placeholder_format.idx == 1 and \
                    "SUBTITLE" not in str(shape.placeholder_format.type)
                problem = check_frame(label, shape.text_frame, (shape.width - dx) / EMU_PER_PT,
                                      (shape.height - dy) / EMU_PER_PT,
                                      indent=BULLET_INDENT / EMU_PER_PT if is_body else 0)
                boxes += 1
            elif shape.has_table:
                problem = None
                table = shape.table
                for r, row in enumerate(table.rows):
                    for c, cell in enumerate(row.cells):
                        if not cell.text.strip():
                            continue
                        w = table.columns[c].width - cell.margin_left - cell.margin_right
                        h = row.height - cell.margin_top - cell.margin_bottom
                        problem = problem or check_frame(f"{label} cell {r + 1},{c + 1}", cell.text_frame,
                                                         w / EMU_PER_PT, h / EMU_PER_PT)
                        boxes += 1
            else:
                continue
            if problem:
                problems.append(problem)
    return problems, boxes


def main():
    failed = False
    for path in sys.argv[1:]:
        problems, boxes = check(path)
        for p in problems:
            print(f"DOES NOT FIT  {p}")
        print(f"{path.rsplit('/', 1)[-1]}: {boxes} text boxes checked, {len(problems)} too small")
        failed |= bool(problems)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
