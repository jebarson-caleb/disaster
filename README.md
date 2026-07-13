# Disaster Management & Emergency Response Platform

A full-stack B.Tech CSE capstone MVP for coordinating rescue and relief operations during floods, earthquakes, cyclones, landslides, and fires.

## What It Includes

- React + Vite frontend with Bootstrap, Leaflet maps, Chart.js analytics, role-aware workflows, disaster reporting, rescue queue, and facility management.
- Flask REST API with JWT auth, SQLAlchemy models, role authorization, disaster/rescue/facility/admin routes, and local AI scoring services.
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

The frontend runs as an interactive demo with local seeded data. The backend has registration/login endpoints and a `seed_demo_data()` helper in `backend/app/seed.py` for app-level seeding.

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
