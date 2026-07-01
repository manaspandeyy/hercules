# Hercules — Daily Tracker

A premium, fully offline desktop productivity app you make your own. Native
window, launch splash, animated analytics — no browser, no terminal needed once
it's running. Build **your own schedule**, track daily check-ins, watch a live
**Momentum Score**, plan course/goal completion, log practice tests, climb a
self-defined leaderboard, and analyse progress reports. Everything is stored
locally in JSON — nothing is hard-coded to any one person.

> Built with Python + [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter).
> Windows-first (desktop shortcut + taskbar icon), but the app itself runs
> anywhere Python + Tk does.

## Run it

**Windows — just double-click `run.bat`.**

The first launch creates a local virtual environment, installs everything,
generates the app icon, and drops a **Hercules** shortcut on your desktop.
Every launch after that opens instantly into a splash screen, then the app.

> Requires Python 3.10+ installed with "Add Python to PATH" checked.
> Get it from [python.org](https://www.python.org/downloads/).

### Manual run (any OS)

```bash
pip install -r requirements.txt
python main.py
```

## Make it yours

Everything personal is editable inside the app — no code required:

| What | Where |
|------|-------|
| **Your daily schedule** | Settings → Daily Schedule → **Edit Schedule**. Build a plan for every day of the week: add / edit / reorder / delete time slots, or copy one day to all weekdays. |
| **Your name & photo** | Settings → Profile. Sets the greetings and the avatar/icon. |
| **Goals** (target date, study hours/day, points target) | Settings → Goals. |
| **Course units** | Goals & Course tab → **Add unit** / rename / delete, and edit lecture/assignment/assessment counts inline. |
| **Leaderboard** | Analytics → Leaderboard → **Edit standings**. Add the people (or targets) you're competing with; your own row updates automatically. |
| **Motivational quotes** | Edit the list in `quotes.py`. |
| **App name / branding** | Change `APP_NAME`, `APP_TAGLINE`, `SCORE_NAME` at the top of `theme.py`. |

## Sections (top navigation bar)

| Section | What it does |
|---------|--------------|
| **📅 Schedule** | Loads the plan for today's weekday. Check off tasks; the progress bar fills. Optional smart popups fire on keyword match — a task containing "dsa" opens a points popup; a study/course task opens a lecture popup; "portal", "referral" and "cold email" tasks open their trackers. Don't use those keywords and tasks simply toggle. |
| **📊 Analytics** | A tabbed dashboard: insights engine, daily **Momentum Score** (out of 100), goal timeline, and CSV/PDF/share-card **export**. Tabs — **Daily**, **Weekly**, **Monthly** (heatmap), **Comparison**, **Leaderboard**, **Habits** (contribution graphs, streaks), and **Unit Deep Dive**. Charts animate and show tooltips. |
| **🎯 Goals & Course** | Your units as expandable colour-coded cards, overall **donut charts**, and a **completion planner** projecting finish dates vs your target date. |
| **📝 Mocks & Assessments** | Track practice tests — score, %, pass/fail (60%+), notes — with a trend chart. |
| **🧠 Progress Report** | Upload a report (PDF/image) or just type the numbers. Extracts assignments / assessments / lectures / avg score, compares to the previous report, and gives recommendations. History kept. |
| **⚙ Settings** | Colour theme, profile, schedule editor, goals, notifications, performance, and data (backup / import / reset). |

A **weekly self-assessment reminder** pops up on Sundays — log one or more
papers (topic, score, difficulty, time, notes); they feed the Analytics trends.

## How the auto-calculations work

- **DSA popup** → Easy ×30 + Medium ×40 + Hard ×50 points, added automatically
  to your leaderboard total. Re-editing the same day adjusts by the difference.
- **Study popup** → lectures watched bump your course lecture count and show up
  immediately in Goals.
- **Leaderboard ETA** → estimated days to overtake the leader based on your
  average points/day (needs at least two days of logged points).
- **Momentum Score** → a 0–100 daily score from schedule completion, DSA,
  lectures, gym, job apps and outreach.

## Your data

Everything lives in a `data/` folder created next to the app (git-ignored, so
it never leaves your machine):

- `daily_log.json` — schedule check-offs, DSA + study sessions
- `goals.json` — course units, leaderboard points + competitors, study pace, target
- `mocks.json` — practice test attempts
- `sunday.json` — weekly self-assessment entries
- `schedules.json` — your per-weekday schedule
- `reports.json` + `reports/` — uploaded progress reports
- `settings.json` — name, theme, and other preferences
- `app_icon.ico` / `app_icon.png` — generated icon

Back up that folder (or use Settings → Data → Export) to keep your history.
Delete it to start fresh.

## Project layout

```
hercules/
├── run.bat                 # double-click launcher (venv + icon + shortcut)
├── requirements.txt
├── main.py                 # app shell: splash, top nav, transitions, theme
├── splash.py               # launch splash
├── dialogs.py              # check-in popups + schedule / leaderboard editors
├── schedules.py            # per-weekday schedule storage (data-driven)
├── data_manager.py         # local JSON storage + analytics math + planner
├── metrics.py              # analytics engine (series, streaks, Momentum Score…)
├── course_data.py          # example units + mock seed data (edit in-app)
├── leaderboard_data.py     # user-defined standings helpers
├── report_parser.py        # PDF parsing + recommendation engine
├── quotes.py               # motivational quote notifications
├── animations.py           # fade / slide / count-up / progress helpers
├── icon.py                 # generates the app icon
├── theme.py                # palettes, colour system, and app identity
└── views/
    ├── schedule_view.py
    ├── analytics_view.py    # tabbed analytics orchestrator
    ├── goals_view.py        # Goals & Course
    ├── mocks_view.py
    ├── report_view.py       # Progress Report
    ├── settings_view.py
    ├── portal_counter.py
    └── analytics/           # one module per analytics tab
        ├── charts.py  overview.py  export.py
        ├── daily.py   weekly.py    monthly.py  comparison.py
        └── leaderboard.py  habits.py  jobhunt.py  unit_deepdive.py
```

## License

Released under the [MIT License](LICENSE). Use it, fork it, make it yours.
