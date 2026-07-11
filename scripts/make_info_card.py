#!/usr/bin/env python3
"""
make_info_card.py

Step 3: generates info-card.svg -- a monochrome terminal-style card that sits
next to the ASCII portrait. NOT github stats (the contribution graph already
covers that) -- this is freeform: role, stack, focus areas, whatever you want
a visitor to read in 5 seconds.

EDIT ROWS BELOW with your real info. Each row is (label, value).
HOST controls the fake terminal prompt line at the top (e.g. "rohit@github").

If content overflows the card, bump H (card height) below.
"""
import sys

HOST = "rohitpr05@github"

ROWS = [
    ("role", "CS Undergrad (B.Tech + Psych minor)"),
    ("focus", "Backend systems, AI/LLM pipelines"),
    ("stack", "Python, TypeScript, GCP, AWS"),
    ("infra", "Grafana / Loki / Prometheus"),
    ("current", "RAG pipelines, observability tooling"),
    ("club", "CanSat telemetry, Rocketry Club"),
    ("linkedin", "linkedin.com/in/rohitpr05"),
]

W = 490
H = 400
FG = "#c9d1d9"
DIM = "#6e7681"
ACCENT = "#58a6ff"
BG = "#0d1117"
FONT = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"
FONT_SIZE = 14
LINE_H = 26
PAD_X = 24
PAD_TOP = 40


def escape_xml(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg():
    label_w = max(len(r[0]) for r in ROWS) + 1

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    lines.append(f'''<style>
      .mono {{ font-family: {FONT}; font-size: {FONT_SIZE}px; }}
      .prompt {{ fill: {ACCENT}; }}
      .label  {{ fill: {DIM}; }}
      .value  {{ fill: {FG}; }}
      .row {{ opacity: 0; animation: fadein 0.4s ease-out forwards; }}
      @keyframes fadein {{ to {{ opacity: 1; }} }}
    </style>''')
    lines.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="8" fill="{BG}" stroke="#30363d" stroke-width="1"/>')

    # fake terminal title bar
    lines.append(f'<circle cx="20" cy="18" r="5" fill="#ff5f56"/>')
    lines.append(f'<circle cx="38" cy="18" r="5" fill="#ffbd2e"/>')
    lines.append(f'<circle cx="56" cy="18" r="5" fill="#27c93f"/>')
    lines.append(f'<line x1="0" y1="32" x2="{W}" y2="32" stroke="#30363d" stroke-width="1"/>')

    y = PAD_TOP
    lines.append(f'<text x="{PAD_X}" y="{y}" class="mono prompt row" style="animation-delay:0s">{escape_xml(HOST)}:~$ whoami</text>')
    y += LINE_H * 1.4

    for i, (label, value) in enumerate(ROWS):
        delay = 0.15 + i * 0.12
        label_padded = (label + ":").ljust(label_w + 1)
        lines.append(
            f'<text x="{PAD_X}" y="{y:.0f}" class="mono row" style="animation-delay:{delay:.2f}s">'
            f'<tspan class="label">{escape_xml(label_padded)}</tspan>'
            f'<tspan class="value"> {escape_xml(value)}</tspan>'
            f'</text>'
        )
        y += LINE_H

    y += LINE_H * 0.6
    cursor_delay = 0.15 + len(ROWS) * 0.12 + 0.2
    lines.append(
        f'<text x="{PAD_X}" y="{y:.0f}" class="mono prompt row" style="animation-delay:{cursor_delay:.2f}s">'
        f'{escape_xml(HOST)}:~$ <tspan class="value">_</tspan></text>'
    )

    lines.append('</svg>')
    return "\n".join(lines)


def main():
    dst = sys.argv[1] if len(sys.argv) > 1 else "info-card.svg"
    svg = build_svg()
    with open(dst, "w") as f:
        f.write(svg)
    print(f"[make_info_card] wrote {dst} ({len(ROWS)} rows, {W}x{H})")


if __name__ == "__main__":
    main()
