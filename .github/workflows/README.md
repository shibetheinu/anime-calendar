# Amire's Anime Calendar

A self-updating anime release calendar. This repo automatically rebuilds and
republishes a `.ics` calendar file every day using GitHub Actions.

## How it works

1. `data/shows.json` — metadata for each show (title, studio, streaming
   platform, genres, synopsis, broadcast time, etc.)
2. `data/events.json` — the actual episode-by-episode schedule (which show
   airs on which date, at what episode number).
3. `scripts/generate_calendar.py` — reads both files and builds
   `docs/calendar.ics`, optionally cross-checking episode counts against the
   free Jikan (MyAnimeList) API.
4. `.github/workflows/update-calendar.yml` — a GitHub Actions workflow that
   runs the script automatically every day at 09:00 UTC, and commits the
   refreshed `docs/calendar.ics` back to the repo.
5. **GitHub Pages** (enabled from the `docs/` folder) serves that file at a
   stable URL that never changes — that's the URL you subscribe to in your
   calendar app.

## Keeping the data current

This automation rebuilds the *file* every day, but it can't independently
discover new anime news (delays, cast reveals, trailers) — that part needs a
human (or an LLM research session) to update `data/shows.json` /
`data/events.json` and push the change. Once pushed, the workflow picks it up
automatically on the next run (or immediately, since pushes to `data/` or
`scripts/` also trigger a rebuild).

To ask Claude to refresh the data for you later, you can upload a new
screenshot or ask it to re-verify the shows in this repo, then paste the
updated JSON back into `data/shows.json` and `data/events.json`.

## Manually triggering a rebuild

Go to the **Actions** tab → **Update Anime Calendar** → **Run workflow**.

## Files

```
anime-calendar/
├── .github/workflows/update-calendar.yml   # daily automation
├── data/
│   ├── shows.json                          # show metadata
│   └── events.json                         # episode schedule
├── scripts/
│   └── generate_calendar.py                # builds the .ics
├── docs/
│   ├── calendar.ics                        # the published calendar (auto-generated)
│   └── status_report.json                  # last Jikan cross-check (auto-generated)
├── requirements.txt
└── README.md
```

See `DEPLOYMENT_GUIDE.md` for the full beginner-friendly setup and
subscription instructions.
