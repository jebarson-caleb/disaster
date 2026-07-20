# Disaster Management & Emergency Response Platform

A full-stack B.Tech CSE capstone MVP for coordinating rescue and relief operations during floods, earthquakes, cyclones, landslides, and fires.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fjebarson-caleb%2Fdisaster&project-name=resq-command&repository-name=resq-command)

## One-click Vercel deployment

Click **Deploy with Vercel** above and then click **Deploy** in Vercel. The repository contains a Vercel Services configuration for the Vite frontend and Python 3.12 Flask backend, API routing, same-origin browser configuration, and demo data initialization. Keep the detected application preset set to **Services**. No environment variables are required for the judging/demo deployment.

The zero-configuration deployment uses SQLite in Vercel's writable `/tmp` directory. It is fully interactive, but serverless restarts can reset demo changes. For durable production data, add a managed database and set `DATABASE_URL` to either a MySQL `mysql+pymysql://...` URL or PostgreSQL `postgresql://...` URL. For a real public deployment, also set `SECRET_KEY` and `JWT_SECRET_KEY` to strong random values and set `DEMO_MODE=false`.

## What It Includes

- React + Vite frontend with Bootstrap, Leaflet maps, Chart.js analytics, role-aware workflows, disaster reporting, rescue queue, and facility management.
- Flask REST API with JWT auth, SQLAlchemy models, role authorization, disaster/rescue/facility/admin routes, and local AI scoring services.
- Live frontend/API synchronization with offline-safe citizen submissions and automatic reconnect replay.
- CAP-inspired multi-channel public alerts, citizen receipt confirmation, nearest-capacity safe routing, and resource/volunteer coordination.
- India-wide alert aggregation, verified disaster-area live-news sources, and responder-managed family welfare checks.
- Automatic proximity dispatch for volunteers and ambulances, plus advance receiving-hospital preparation notices.
- Consent-based device location, isolated-survivor food/supply requests, and auditable relief donation campaigns.
- MySQL DBMS deliverables: normalized schema, views, stored procedures, triggers, sample data, complex queries, and a 5,000+ record seed generator.
- Academic docs: SRS, relational schema, data dictionary, and query notes.

## Quick Start

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

The frontend connects to `http://localhost:5000/api/v1` by default. Override it with `VITE_API_BASE_URL`. Start the backend as well to use persistent live operations; if it is unavailable, citizen reports are queued locally and replayed after reconnect.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

The API runs at `http://localhost:5000/api/v1`.

Without a `DATABASE_URL`, the backend uses a local SQLite dev database and seeds demo data automatically. For MySQL, create the database using `database/01_schema.sql`, load the supporting SQL files, and set `DATABASE_URL` in `backend/.env`.

### Backend Tests

```bash
cd backend
pytest
```

Tests use in-memory SQLite so they do not require MySQL.

## Demo Users

The frontend includes both real registration/login and a clearly labeled role-switching demo. Seeded demo accounts use `password123` and role-specific addresses such as `admin@rescue.local` and `citizen@rescue.local`. The account button in the top bar opens the real authentication form.

`DEMO_MODE=true` enables the role-switching demo-session endpoint for local judging and is included in `.env.example`; the secure application default is `false`. Keep it disabled outside a controlled demo environment. Public self-registration is limited to Citizen and Volunteer accounts; operational authority roles must be provisioned by an administrator.

## Local AI

AI decisions are deterministic and explainable by default:

- Damage estimation
- Rescue prioritization
- Resource allocation

Optional Ollama enrichment is supported through:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

If Ollama is unavailable, the backend automatically falls back to rules-based explanations.

## Hackathon alignment

The feature-to-problem mapping and source rationale are documented in [`docs/HACKATHON_ALIGNMENT.md`](docs/HACKATHON_ALIGNMENT.md).
