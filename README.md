# fallen_budgie — Open-source Vulnerability Management Prototype

This repository contains a starter prototype for fallen_budgie: a vulnerability management tool combining network (nmap) and web (nuclei) scanning with a FastAPI backend, Celery task queue, SQLite storage and a React+Tailwind frontend.

## Project layout

- `backend/` — FastAPI app, Celery tasks and scanner wrapper
- `frontend/` — React component scaffolding (Dashboard)

## Quickstart (developer)

Prerequisites:
- Python 3.11+
- Redis running locally (default: `redis://localhost:6379/0`)
- nmap installed and in PATH
- (optional, for web scans) nuclei installed and in PATH

On Windows, you can install nmap from: https://nmap.org/download.html
For nuclei, see: https://github.com/projectdiscovery/nuclei

1. Backend: create a virtualenv and install requirements

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

2. Start Redis (e.g., via WSL, Docker, or local install). Example (Docker):

```bash
docker run -p 6379:6379 --name redis -d redis:7
```

3. Start FastAPI (development):

```bash
uvicorn backend.app.main:app --reload --port 8000
```

4. Start Celery worker from repository root:

```bash
celery -A backend.app.tasks.celery_app.celery worker -Q scans -l info
```

Note: The Celery entrypoint may differ depending on your shell; an equivalent Python invocation is:

```bash
python -m celery -A backend.app.celery_app.celery worker -Q scans -l info
```

5. Frontend: the `frontend/` folder contains a minimal scaffold. We recommend creating a Vite or CRA project and copying `src/components/Dashboard.jsx` and `src/App.jsx` in. Install `axios` and Tailwind as needed.

## Frontend (Vite + Tailwind) — setup and run

Prerequisites:
- Node.js 18+ and npm or yarn

Quick start (from repo root):

```bash
cd frontend
npm install
# Create a .env file from the example to override API base if needed
cp .env.example .env
npm run dev
```

If you see an error like "It looks like you're trying to use `tailwindcss` directly as a PostCSS plugin", install the Tailwind PostCSS adapter and re-run install:

```bash
cd frontend
npm install --save-dev @tailwindcss/postcss
npm install
npm run dev
```

By default the frontend expects the backend API at the URL in `VITE_API_BASE` (defaults to `http://localhost:8000`). You can edit `.env` to point to a different host/port.

The frontend uses `src/lib/api.js` which reads `import.meta.env.VITE_API_BASE` and sets a central axios base client. This keeps components free of hardcoded hosts.


## How it works

- POST `/scan` with JSON `{ "target": "1.2.3.4", "scan_type": "network" }` creates a DB record and enqueues a Celery task.
- Celery worker runs `app.tasks.scan_task`, which performs an nmap scan (top 100 ports) and stores the structured JSON result in SQLite.
- GET `/scans` returns scan summaries. Frontend poll or reload to display updates.

## Security & Best Practices (notes)

- Running scanners (nmap, nuclei) requires care: scan only assets you own or have permission to test.
- For production, replace SQLite with a server-class DB (Postgres), secure Redis with auth and TLS, and run workers in isolated environments.
- Sanitize and rate-limit scanning API endpoints to avoid abuse.

## Next steps / TODO

- Add nuclei integration for `web` scan_type (invoke nuclei subprocess asynchronously and parse results).
- Add user auth and RBAC for multi-tenant scanning.
- Add richer severity mapping and CVE correlation.
