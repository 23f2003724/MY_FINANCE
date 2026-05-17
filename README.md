# Pink Pocket Tracker

A Flask expense tracker for monthly budgeting and daily spending control. The app lets a user record expenses, track daily limits, review recent spending, and see whether they are saving or going over budget.

## Highlights

- Add, edit, and delete expenses
- Blocks future dates for add/edit actions
- Tracks a monthly budget of `Rs. 3000`
- Tracks a daily spending limit of `Rs. 100`
- Shows daily saved or over-budget status
- Calculates a shopping balance from days where spending stays below the limit
- Uses SQLite locally and supports Postgres through `DATABASE_URL`
- Includes a Render-ready `Procfile`

## Tech Stack

- Python
- Flask
- SQLAlchemy ORM
- SQLite for local development
- Postgres support for deployment
- Bootstrap and custom CSS
- Gunicorn

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open the app at `http://127.0.0.1:5000`.

## Environment Variables

The app works locally without environment variables. For deployment, set:

```text
SECRET_KEY=your-secret-key
DATABASE_URL=your-postgres-connection-string
```

If `DATABASE_URL` is not provided, the app uses local SQLite at `database.db`.

## Deployment Notes

This project can be deployed as a free web service on Render with Neon Postgres.

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Required environment variables: `SECRET_KEY`, `DATABASE_URL`

## What This Project Shows

This project demonstrates beginner-friendly backend skills: Flask routing, SQLAlchemy models, server-side validation, database sessions, template rendering, deployment configuration, and clean local-vs-production database handling.

## Next Improvements

- Add user accounts and authentication
- Add charts for weekly and monthly spending trends
- Add automated tests for expense validation
- Make monthly budget and daily limit configurable from the UI
