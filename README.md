# 🔥 Habit Tracker

A small FastAPI app for tracking daily habits: check off a habit each day, the
streak is counted automatically, and the whole history is rendered as a
GitHub-style contribution grid.

## Stack

FastAPI + SQLAlchemy 2.0 + SQLite, Jinja2 templates, vanilla JS, plain CSS.
No authentication — this is a single-user app.

## Running locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

App: http://127.0.0.1:8000
Swagger UI: http://127.0.0.1:8000/docs

The `habit_tracker.db` database file is created automatically on first start.

## API

| Method | Path                  | Description                                        |
|--------|-----------------------|----------------------------------------------------|
| GET    | `/`                   | list of habits with their current streaks          |
| POST   | `/habits`             | create a habit (HTML form or JSON)                 |
| GET    | `/habits/{id}`        | habit page with the last year's grid               |
| POST   | `/habits/{id}/toggle` | check/uncheck a day (no body — today)              |
| DELETE | `/habits/{id}`        | delete a habit together with its history           |
| GET    | `/habits/{id}/data`   | JSON with the completion dates for the last year   |

Examples:

```bash
curl -X POST localhost:8000/habits -H 'Content-Type: application/json' -d '{"name":"Reading"}'
curl -X POST localhost:8000/habits/1/toggle
curl -X POST localhost:8000/habits/1/toggle -H 'Content-Type: application/json' -d '{"date":"2026-09-09"}'
```

## How the streak is calculated

Starting from today, we walk backwards while the days are checked without gaps.
If today has not been checked yet, the count starts from yesterday, so the streak
does not reset in the middle of the day. It is computed on the fly on every
request — no caching.

## Features

- GitHub-style contribution grid for the last 52 weeks
- Current streak, longest streak and total number of days per habit
- Click any square in the grid to check or uncheck that day
- Reminder on the home page listing habits not yet done today
- Light/dark theme, remembered in `localStorage`
- A custom color per habit

## Project structure

```
app/
├── main.py       # FastAPI routes
├── models.py     # Habit, Completion
├── database.py   # engine and sessions
├── schemas.py    # Pydantic schemas
├── crud.py       # database access + streak calculation
├── templates/    # base, index, habit, 404
└── static/       # style.css
```

## Notes

- SQLite ignores foreign keys unless they are explicitly enabled, so
  `PRAGMA foreign_keys=ON` is set on every connection in `database.py`.
- Dates in the frontend are built from local date components rather than
  `toISOString()`, which would shift the grid by a day in timezones east of UTC.
