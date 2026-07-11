#!/usr/bin/env python3
"""
make_ascii_svg.py [input.png] [output.svg]

Step 2 of the portrait pipeline. Converts a grayscale photo into a monochrome
ASCII-art portrait rendered as SVG <text> characters, styled like it's being
typed into a terminal (rows fade/reveal in sequence via CSS animation).

Defaults: reads source-prepped.png -> writes avi-ascii.svg

TUNE THESE:
  COLS         - width of the ascii grid in characters (more = more detail, bigger file)
  CONTRAST     - >1 punches up mid-tone separation, <1 flattens it
  GAMMA        - <1 brightens midtones/shadows (helps dark/underlit photos),
                 >1 darkens them
  WHITE_FLOOR  - minimum brightness (0-255) treated as "pure white" -- raise this
                 if the brightest parts of the face are getting crushed to a mid
                 character instead of reading as highlight
  CHARSET      - density ramp, dark -> light. Reorder/replace to change texture.
  FG / BG      - foreground / background colors (keep monochrome per the brief)

Preview the FINAL frame (no typing animation, fully revealed) by setting the
STATIC env var:
    STATIC=1 python scripts/make_ascii_svg.py
"""
import os
import sys
import numpy as np
from PIL import Image

COLS = 110
CHAR_ASPECT = 0.52          # monospace char width/height ratio, keeps portrait proportions right
CONTRAST = 1.55
GAMMA = 0.75
WHITE_FLOOR = 210
CHARSET = " .'`^,:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW%@8"
FG = "#c9d1d9"               # light gray-white text (GitHub dark-mode friendly)
BG = "#0d1117"               # GitHub dark background
FONT_SIZE = 7
LINE_HEIGHT = FONT_SIZE * 1.0
CHAR_WIDTH = FONT_SIZE * CHAR_ASPECT


def load_and_grid(path, cols):
    img = Image.open(path).convert("L")
    w, h = img.size
    rows = max(1, round(cols * (h / w) * CHAR_ASPECT))
    img = img.resize((cols, rows), Image.LANCZOS)
    arr = np.array(img).astype(np.float32) / 255.0
    return arr


def tone_map(arr):
    # gamma
    arr = np.clip(arr, 0, 1) ** GAMMA
    # contrast around midpoint
    arr = np.clip((arr - 0.5) * CONTRAST + 0.5, 0, 1)
    # white floor: rescale so WHITE_FLOOR/255 and above clip to 1.0
    floor = WHITE_FLOOR / 255.0
    arr = np.clip(arr / floor, 0, 1)
    return arr


def to_ascii_rows(arr):
    n = len(CHARSET) - 1
    rows = []
    for row in arr:
        line = "".join(CHARSET[int(round(v * n))] for v in row)
        rows.append(line)
    return rows


def escape_xml(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build_svg(rows, static=False):
    n_rows = len(rows)
    n_cols = max(len(r) for r in rows)
    width = n_cols * CHAR_WIDTH + 20
    height = n_rows * LINE_HEIGHT + 20

    row_reveal_dur = 0.028   # seconds per row reveal
    total_anim = n_rows * row_reveal_dur

    css = f"""
    .ascii-line {{
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      font-size: {FONT_SIZE}px;
      white-space: pre;
      fill: {FG};
    }}
    """
    if not static:
        css += f"""
    .ascii-line {{
      opacity: 0;
      animation: reveal 0.35s ease-out forwards;
    }}
    @keyframes reveal {{
      to {{ opacity: 1; }}
    }}
    .cursor {{
      fill: {FG};
      animation: blink 0.9s steps(1) infinite;
      animation-delay: {total_anim:.2f}s;
    }}
    @keyframes blink {{
      50% {{ opacity: 0; }}
    }}
    """

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" width="{width:.0f}" height="{height:.0f}">')
    parts.append(f'<style>{css}</style>')
    parts.append(f'<rect x="0" y="0" width="{width:.0f}" height="{height:.0f}" fill="{BG}" rx="6"/>')

    for i, row in enumerate(rows):
        y = 14 + i * LINE_HEIGHT
        delay = i * row_reveal_dur
        style = "" if static else f' style="animation-delay:{delay:.3f}s"'
        parts.append(f'<text x="10" y="{y:.1f}" class="ascii-line"{style}>{escape_xml(row)}</text>')

    if not static:
        cy = 14 + (n_rows - 1) * LINE_HEIGHT
        cx = 10 + len(rows[-1]) * CHAR_WIDTH
        parts.append(f'<rect class="cursor" x="{cx:.1f}" y="{cy - FONT_SIZE + 1:.1f}" width="{CHAR_WIDTH:.1f}" height="{FONT_SIZE:.1f}"/>')

    parts.append('</svg>')
    return "\n".join(parts)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    dst = sys.argv[2] if len(sys.argv) > 2 else "avi-ascii.svg"
    static = os.environ.get("STATIC") == "1"

    print(f"[make_ascii_svg] reading {src}, cols={COLS}")
    arr = load_and_grid(src, COLS)
    arr = tone_map(arr)
    rows = to_ascii_rows(arr)

    svg = build_svg(rows, static=static)
    with open(dst, "w") as f:
        f.write(svg)
    print(f"[make_ascii_svg] wrote {dst} ({len(rows)} rows x {COLS} cols, static={static})")


if __name__ == "__main__":
    main()
