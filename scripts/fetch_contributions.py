#!/usr/bin/env python3
"""
fetch_contributions.py

Step 5a: scrapes public contribution-calendar data from a GitHub profile page
(no auth / no token required -- this is the same data GitHub renders into the
public profile HTML). Writes contributions.json for render_heatmap_svg.py.

Set GH_PROFILE_USER env var, or edit USERNAME below.
"""
import os
import sys
import json
import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_PROFILE_USER", "Rohitpr05")


def fetch_calendar(username):
    url = f"https://github.com/users/{username}/contributions"
    headers = {"User-Agent": "Mozilla/5.0 (profile-readme-bot)"}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Counts live in sibling <tool-tip for="cell-id">N contributions on ...</tool-tip>
    # elements rather than a data-count attribute (GitHub markup as of 2026).
    tooltip_text_by_id = {}
    for tt in soup.select("tool-tip"):
        target_id = tt.get("for")
        if target_id:
            tooltip_text_by_id[target_id] = tt.get_text(strip=True)

    count_re = re.compile(r"^(No|\d+)\s+contributions?", re.IGNORECASE)

    days = []
    cells = soup.select("td.ContributionCalendar-day")
    for c in cells:
        date = c.get("data-date")
        if date is None:
            continue
        level = c.get("data-level")
        cell_id = c.get("id")

        count = 0
        tip = tooltip_text_by_id.get(cell_id, "")
        m = count_re.match(tip)
        if m:
            count = 0 if m.group(1).lower() == "no" else int(m.group(1))

        days.append({
            "date": date,
            "count": count,
            "level": int(level) if level is not None else 0,
        })

    if not days:
        raise RuntimeError(
            "No contribution cells found -- GitHub may have changed markup, "
            "or the profile page is unreachable from this network."
        )

    days.sort(key=lambda d: d["date"])
    return days


def compute_streaks(days):
    total = sum(d["count"] for d in days)
    longest = cur = 0
    for d in days:
        if d["count"] > 0:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0

    # current streak: walk backwards from the last day
    current = 0
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        else:
            break

    return {"total": total, "longest_streak": longest, "current_streak": current}


def main():
    print(f"[fetch_contributions] fetching calendar for {USERNAME}...")
    try:
        days = fetch_calendar(USERNAME)
    except Exception as e:
        print(f"[fetch_contributions] ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    stats = compute_streaks(days)
    out = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "stats": stats,
    }

    with open("contributions.json", "w") as f:
        json.dump(out, f, indent=2)

    print(f"[fetch_contributions] wrote contributions.json "
          f"({len(days)} days, total={stats['total']}, "
          f"longest={stats['longest_streak']}, current={stats['current_streak']})")


if __name__ == "__main__":
    main()
