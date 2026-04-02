# Pink Pocket Tracker

Flask expense tracker with:

- Monthly budget: `Rs. 3000`
- Daily limit: `Rs. 100`
- Add expenses (`item + amount + date`)
- Edit/delete past and current dates
- Future dates blocked for add/edit
- Daily saved/over-budget status
- Shopping balance cart (sum of daily savings where spend is below Rs. 100)

## Local run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open: `http://127.0.0.1:5000`

## Database

- Local default: SQLite (`database.db`)
- Production recommended: Neon Postgres via `DATABASE_URL`

The app auto-detects:
- `sqlite:///database.db` fallback if no `DATABASE_URL` is provided
- Postgres when `DATABASE_URL` is set

## Free deployment (Render + Neon)

### 1. Create Neon database (free)
1. Create a project in Neon.
2. Copy the connection string from Neon dashboard.
3. Keep `sslmode=require` in that URL.

### 2. Deploy app on Render (free web service)
1. Push this project to GitHub.
2. In Render dashboard: `New` -> `Web Service`.
3. Connect your GitHub repo.
4. Use:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
   - Plan: `Free`
5. Add environment variables:
   - `SECRET_KEY` = any strong random value
   - `DATABASE_URL` = Neon connection string
6. Deploy.

After deploy, your data stays in Neon (not in Render filesystem), so it survives app restarts/redeploys.
