# Deployment Guide — No GitHub Experience Needed

## Part 1 — Create the GitHub repository

1. Go to [github.com](https://github.com) and sign up for a free account if you don't have one.
2. Click the **+** icon in the top-right corner → **New repository**.
3. Name it something like `anime-calendar`.
4. Set it to **Public** (required for the free hosted calendar URL to work).
5. Do **not** check "Add a README" — you'll upload your own files.
6. Click **Create repository**.

## Part 2 — Upload the files

You should have a folder called `anime-calendar/` containing:
`.github/workflows/update-calendar.yml`, `data/shows.json`, `data/events.json`,
`scripts/generate_calendar.py`, `requirements.txt`, `README.md`, and this guide.

1. On your new (empty) repo page, click **uploading an existing file**.
2. Drag the entire `anime-calendar` folder's contents into the browser window.
   > GitHub's web uploader doesn't always preserve folder structure well from
   > a drag-and-drop of a top-level folder. If files land in the wrong place,
   > it's easier to create each subfolder first: type `data/shows.json` into
   > the "Add file → Create new file" name box (GitHub auto-creates the
   > `data/` folder), paste the content, then repeat for each file.
3. Scroll down, write a commit message like "Initial upload," and click
   **Commit changes**.

## Part 3 — Enable GitHub Actions

Actions are enabled by default on public repos. To confirm:

1. Click the **Actions** tab at the top of your repo.
2. You should see a workflow called **Update Anime Calendar**.
3. Click it, then click **Run workflow** → **Run workflow** to trigger the
   first build manually (don't wait for tomorrow's scheduled run).
4. Wait ~30 seconds, refresh, and you should see a green checkmark.

## Part 4 — Enable GitHub Pages

This is what gives you a stable public URL for the `.ics` file.

1. Go to your repo's **Settings** tab.
2. In the left sidebar, click **Pages**.
3. Under "Build and deployment" → **Source**, choose **Deploy from a branch**.
4. Under **Branch**, choose `main` and folder `/docs`. Click **Save**.
5. Wait a minute, then refresh the page — GitHub will show you a URL like:
   ```
   https://YOUR-USERNAME.github.io/anime-calendar/
   ```
6. Your calendar file will be at:
   ```
   https://YOUR-USERNAME.github.io/anime-calendar/calendar.ics
   ```
   **This is the URL you'll subscribe to.** Save it somewhere handy.

## Part 5 — How the daily automation works

Every day at 09:00 UTC (5:00 AM Eastern), GitHub automatically:
1. Spins up a temporary computer (a "runner").
2. Runs `scripts/generate_calendar.py`, which rebuilds `docs/calendar.ics`
   from the data files.
3. Commits the updated file back to your repo.
4. GitHub Pages automatically re-publishes it at the same URL — no action
   needed from you.

Anyone subscribed to the URL (rather than having just downloaded the file
once) will see the update the next time their calendar app refreshes.

## Part 6 — Subscribe so updates appear automatically

### Google Calendar
1. Open [calendar.google.com](https://calendar.google.com) on desktop (mobile
   app doesn't support adding by URL).
2. Left sidebar → **Other calendars** → **+** → **From URL**.
3. Paste your `calendar.ics` URL. Click **Add calendar**.
4. It may take several hours for Google to refresh; Google Calendar controls
   the refresh frequency and doesn't offer a manual "refresh now" button.

### Apple Calendar (Mac/iPhone)
1. On Mac: **Calendar app → File → New Calendar Subscription**.
2. Paste the URL, click **Subscribe**.
3. Set **Auto-refresh** to "Every day." Click **OK**.
4. This subscription will also sync to your iPhone/iPad via iCloud if your
   calendars are set to sync.

### Outlook
1. Outlook.com: **Add calendar → Subscribe from web**.
2. Paste the URL, give it a name, click **Import**.
3. Desktop Outlook: **Home → Add Calendar → From Internet**, paste the URL.

### TimeTree
1. Open the TimeTree app → the calendar you want to add it to → **Settings**.
2. **Calendar Settings → iCalendar Sharing / Import iCalendar**.
3. Paste your `calendar.ics` URL.
   > TimeTree's iCalendar import can be a one-time snapshot depending on your
   > app version/plan rather than a live subscription — check the in-app
   > description before relying on it for automatic updates. If it's
   > snapshot-only, you'll need to re-import periodically or use Google/Apple
   > Calendar as your live source and share that into TimeTree.

## Part 7 — Verifying automatic updates are working

1. Edit `data/events.json` directly on GitHub (click the file → pencil icon
   → make a small change → **Commit changes**).
2. Go to the **Actions** tab — you should see a new workflow run start within
   a few seconds (pushes to `data/` trigger it immediately).
3. Once it finishes (green check), open your `calendar.ics` URL in a browser
   — you should see the new content (Ctrl+F / Cmd+F for what you changed).
4. Your subscribed calendar app will pick it up on its own refresh schedule
   (varies by app — Apple Calendar is fastest since you can force "every
   day," Google can lag).

## Part 8 — Troubleshooting

| Problem | Likely cause / fix |
|---|---|
| Actions tab shows a red X | Click into the failed run to see the error. Most common: a typo in `shows.json`/`events.json` breaking JSON parsing — validate at [jsonlint.com](https://jsonlint.com). |
| GitHub Pages 404s on the .ics URL | Double check Settings → Pages source is `main` branch, `/docs` folder, and that `docs/calendar.ics` exists in the repo. |
| Calendar app shows old data | Subscriptions refresh on the app's own schedule, not instantly. Force it: Apple Calendar → right-click calendar → **Refresh**; Google Calendar has no manual refresh. |
| "Repository not found" when pushing from Actions | Make sure the workflow has `permissions: contents: write` (already set in the provided YAML) and that Settings → Actions → General → Workflow permissions is set to "Read and write." |
| Times look off by an hour | The generator uses a fixed EDT (UTC-4) offset for simplicity. During US Eastern Standard Time (winter), you'd need to adjust the offset to UTC-5, or upgrade the script to use `zoneinfo` for automatic DST handling. |
