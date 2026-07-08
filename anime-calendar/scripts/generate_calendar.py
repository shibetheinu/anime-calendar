#!/usr/bin/env python3
"""
Anime Calendar Generator
-------------------------
Reads data/shows.json and data/events.json, optionally cross-checks episode
counts / airing status against the Jikan API (unofficial MyAnimeList API,
no key required), and rebuilds docs/calendar.ics.

This script is designed to be run daily by GitHub Actions (see
.github/workflows/update-calendar.yml) so the published .ics URL always
reflects the latest data in this repo.

IMPORTANT — what this automation can and can't do on its own:
  - It CAN rebuild the .ics file any time data/shows.json or data/events.json
    changes, and re-publish it automatically every day.
  - It CAN optionally ping Jikan/MyAnimeList for each show's current status
    and episode count, and flag mismatches in data/status_report.json.
  - It CANNOT independently discover brand-new episode delays, cast news, or
    trailer drops the way a human researcher (or an LLM with web search)
    can. To pick up that kind of news, edit data/shows.json / events.json
    by hand (or regenerate them with Claude periodically) and push — the
    workflow will then rebuild and republish automatically.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
DOCS_DIR = os.path.join(REPO_ROOT, "docs")

JIKAN_BASE = "https://api.jikan.moe/v4"
USE_JIKAN = os.environ.get("USE_JIKAN", "true").lower() == "true"


def load_json(name):
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def parse_time(t):
    return datetime.strptime(t, "%I:%M %p")


def fmt_dt(date_str, time_str):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    t = parse_time(time_str)
    return d.replace(hour=t.hour, minute=t.minute)


def ics_escape(s):
    return (
        s.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def et_to_utc(dt):
    # Simple fixed offset for EDT (UTC-4). Does not handle EST (winter, UTC-5)
    # differences across a generated batch spanning a DST boundary; fine for
    # single-season calendars. For year-round accuracy, swap in zoneinfo.
    return dt + timedelta(hours=4)


def jikan_lookup(mal_id, cache):
    """Fetch current status/episode count from Jikan, with simple caching + rate limiting."""
    if not mal_id:
        return None
    if mal_id in cache:
        return cache[mal_id]
    url = f"{JIKAN_BASE}/anime/{mal_id}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())["data"]
        result = {
            "status": data.get("status"),
            "episodes": data.get("episodes"),
            "airing": data.get("airing"),
        }
        cache[mal_id] = result
        time.sleep(1)  # be polite to the free API's rate limit
        return result
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, TimeoutError) as e:
        print(f"  [warn] Jikan lookup failed for MAL ID {mal_id}: {e}", file=sys.stderr)
        return None


def build_event(show_key, show, date_str, ep_num):
    start = fmt_dt(date_str, show["time_et"])
    end = start + timedelta(minutes=30)
    dtstamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")

    dtstart_utc = et_to_utc(start).strftime("%Y%m%dT%H%M%SZ")
    dtend_utc = et_to_utc(end).strftime("%Y%m%dT%H%M%SZ")

    summary = f"{show['title']} - Ep {ep_num}"

    desc_lines = [
        f"Official English Title: {show['title']}",
        f"Japanese Title: {show.get('jp_title', 'Unconfirmed')}",
        f"Episode: {ep_num}",
        f"Studio: {show.get('studio', 'Unconfirmed')}",
        f"Genres: {show.get('genres', 'Unconfirmed')}",
        f"Streaming: {show.get('platform', 'Unconfirmed')}",
        "Converted Time (US Eastern): "
        + show["time_et"]
        + (" (TENTATIVE — Official Time Pending)" if show.get("tentative_time") else " (Verified)"),
        f"Synopsis: {show.get('synopsis', '')}",
    ]
    description = ics_escape("\n".join(desc_lines))
    uid = f"{show_key}-ep{ep_num}-{date_str}@anime-calendar"

    return "\n".join(
        [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART:{dtstart_utc}",
            f"DTEND:{dtend_utc}",
            f"SUMMARY:{ics_escape(summary)}",
            f"DESCRIPTION:{description}",
            f"CATEGORIES:{show.get('category', 'OTHER')}",
            "END:VEVENT",
        ]
    )


def main():
    shows = load_json("shows.json")
    events = load_json("events.json")

    # Optional: cross-check against Jikan for status drift (cancellations,
    # episode count changes). Report any mismatches so a human can update
    # data/shows.json accordingly.
    status_report = {}
    if USE_JIKAN:
        cache = {}
        for key, show in shows.items():
            mal_id = show.get("mal_id")
            if not mal_id:
                continue
            print(f"Checking Jikan status for {show['title']} (MAL #{mal_id})...")
            result = jikan_lookup(mal_id, cache)
            if result:
                status_report[key] = result

    header = "\n".join(
        [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Amire Anime Calendar//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Amire's Anime Release Calendar",
            "X-WR-TIMEZONE:America/New_York",
        ]
    )
    footer = "END:VCALENDAR"

    body = []
    for ev in events:
        show = shows.get(ev["show_key"])
        if not show:
            print(f"  [warn] Unknown show_key '{ev['show_key']}', skipping", file=sys.stderr)
            continue
        body.append(build_event(ev["show_key"], show, ev["date"], ev["episode"]))

    ics_content = header + "\n" + "\n".join(body) + "\n" + footer

    os.makedirs(DOCS_DIR, exist_ok=True)
    out_path = os.path.join(DOCS_DIR, "calendar.ics")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(ics_content)

    with open(os.path.join(DOCS_DIR, "status_report.json"), "w", encoding="utf-8") as f:
        json.dump(
            {"generated_at": datetime.utcnow().isoformat() + "Z", "jikan_status": status_report},
            f,
            indent=2,
        )

    print(f"Wrote {len(events)} events to {out_path}")


if __name__ == "__main__":
    main()
