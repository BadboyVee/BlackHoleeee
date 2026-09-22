#!/usr/bin/env python3
"""Inline three.js and the soundtrack into one self-contained HTML file.

    python3 tools/build-standalone.py [out.html] [--fragment]

--fragment drops the <!DOCTYPE>/<html>/<head>/<body> wrapper (for hosts that supply their own).
"""
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
args = [a for a in sys.argv[1:] if not a.startswith("--")]
out = Path(args[0]) if args else root / "a-day-in-the-life-of-claude-code.html"
html = (root / "index.html").read_text()


def inline(src):
    code = (root / src).read_text().replace("</script", "<\\/script")
    return "<script>\n" + code + "\n</script>"


html = html.replace('<script src="../vendor/three.r159.min.js"></script>', inline("../vendor/three.r159.min.js"))
html = html.replace('<script src="soundtrack.js"></script>', inline("soundtrack.js"))
assert '<script src=' not in html, "an external script is still referenced"

if "--fragment" in sys.argv:
    html = re.sub(r"<!DOCTYPE html>\s*|<html[^>]*>\s*|</html>\s*|<head>\s*|</head>\s*|<body>\s*|</body>\s*", "", html)
    html = re.sub(r'<meta charset[^>]*>\s*|<meta name="viewport"[^>]*>\s*', "", html)

out.write_text(html)
print(f"wrote {out} ({out.stat().st_size / 1e6:.2f} MB)")
