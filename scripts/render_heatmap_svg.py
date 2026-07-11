#!/usr/bin/env python3
"""
render_heatmap_svg.py

Step 5b: reads contributions.json (from fetch_contributions.py) and renders
contrib-heatmap.svg -- a GitHub-style grid of week columns / day-of-week rows,
monochrome, cells reveal one-by-one (column by column) like they're being
drawn in. Includes a Less->More legend and real streak stats as a caption.
"""
import json
import sys
from datetime import datetime, timedelta

CELL = 11
GAP = 3
FG = "#c9d1d9"
DIM = "#6e7681"
BG = "#0d1117"
BORDER = "#30363d"
# monochrome intensity ramp, empty -> max (GitHub uses green; brief asks monochrome)
LEVEL_COLORS = ["#161b22", "#30363d", "#58a6ff55", "#58a6ffaa", "#58a6ff"]
FONT = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"

MARGIN_LEFT = 28
MARGIN_TOP = 16
MARGIN_BOTTOM = 46


def load_data(path="contributions.json"):
    with open(path) as f:
        return json.load(f)


def bucket_by_week(days):
    """Arrange days into GitHub-style columns starting on Sunday."""
    parsed = [
        {**d, "dt": datetime.strptime(d["date"], "%Y-%m-%d")}
        for d in days
    ]
    parsed.sort(key=lambda d: d["dt"])

    first = parsed[0]["dt"]
    # back up to the preceding Sunday so week columns align
    start = first - timedelta(days=(first.weekday() + 1) % 7)

    weeks = []
    week = [None] * 7
    cursor = start
    di = 0
    while di < len(parsed) or any(c is not None for c in week):
        for dow in range(7):
            if di < len(parsed) and parsed[di]["dt"] == cursor:
                week[dow] = parsed[di]
                di += 1
            cursor += timedelta(days=1)
        weeks.append(week)
        week = [None] * 7
        if di >= len(parsed):
            break
    return weeks


def build_svg(data):
    days = data["days"]
    stats = data["stats"]
    username = data["username"]
    weeks = bucket_by_week(days)
    n_weeks = len(weeks)

    width = MARGIN_LEFT + n_weeks * (CELL + GAP) + 10
    height = MARGIN_TOP + 7 * (CELL + GAP) + MARGIN_BOTTOM

    total_cells = sum(1 for w in weeks for d in w if d is not None)
    reveal_span = 1.4  # seconds for the whole grid to draw in
    per_cell_delay = reveal_span / max(total_cells, 1)

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" width="{width:.0f}" height="{height:.0f}">')
    parts.append(f'''<style>
      text {{ font-family: {FONT}; fill: {DIM}; }}
      .cell {{ opacity: 0; animation: pop 0.25s ease-out forwards; }}
      @keyframes pop {{ to {{ opacity: 1; }} }}
      .stat-num {{ fill: {FG}; font-weight: bold; }}
    </style>''')
    parts.append(f'<rect x="0" y="0" width="{width:.0f}" height="{height:.0f}" rx="6" fill="{BG}"/>')

    month_labels_done = set()
    ci = 0
    for wi, week in enumerate(weeks):
        x = MARGIN_LEFT + wi * (CELL + GAP)
        for dow, d in enumerate(week):
            y = MARGIN_TOP + dow * (CELL + GAP)
            if d is None:
                continue
            level = min(int(d.get("level", 0)), 4)
            color = LEVEL_COLORS[level]
            delay = ci * per_cell_delay
            ci += 1
            title = f'{d["count"]} contributions on {d["date"]}'
            parts.append(
                f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{color}" stroke="{BORDER}" stroke-width="0.5" '
                f'style="animation-delay:{delay:.3f}s"><title>{title}</title></rect>'
            )
            mkey = (d["dt"].year, d["dt"].month) if "dt" in d else None
            month = datetime.strptime(d["date"], "%Y-%m-%d")
            mkey = (month.year, month.month)
            if dow == 0 and mkey not in month_labels_done:
                month_labels_done.add(mkey)
                parts.append(f'<text x="{x}" y="{MARGIN_TOP - 4}" font-size="9">{month.strftime("%b")}</text>')

    # legend: Less -> More
    legend_y = height - 28
    parts.append(f'<text x="{MARGIN_LEFT}" y="{legend_y + 9}" font-size="10">Less</text>')
    lx = MARGIN_LEFT + 32
    for level, color in enumerate(LEVEL_COLORS):
        parts.append(f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}" stroke="{BORDER}" stroke-width="0.5"/>')
        lx += CELL + GAP
    parts.append(f'<text x="{lx + 4}" y="{legend_y + 9}" font-size="10">More</text>')

    # stats caption
    stat_str = (
        f'{stats["total"]} contributions   ·   '
        f'longest streak {stats["longest_streak"]}d   ·   '
        f'current streak {stats["current_streak"]}d'
    )
    parts.append(f'<text x="{MARGIN_LEFT}" y="{height - 8}" font-size="11">{stat_str}</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "contributions.json"
    dst = sys.argv[2] if len(sys.argv) > 2 else "contrib-heatmap.svg"
    data = load_data(src)
    svg = build_svg(data)
    with open(dst, "w") as f:
        f.write(svg)
    print(f"[render_heatmap_svg] wrote {dst}")


if __name__ == "__main__":
    main()
