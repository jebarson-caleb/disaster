# ResQ Command

[![CI](https://github.com/jebarson-caleb/disaster/actions/workflows/ci.yml/badge.svg)](https://github.com/jebarson-caleb/disaster/actions/workflows/ci.yml)
[![Production smoke](https://github.com/jebarson-caleb/disaster/actions/workflows/production-smoke.yml/badge.svg)](https://github.com/jebarson-caleb/disaster/actions/workflows/production-smoke.yml)

Live beta: [disaster-delta-eight.vercel.app](https://disaster-delta-eight.vercel.app)

ResQ Command is a full-stack disaster-response platform for citizen reporting, rescue triage and dispatch, public warnings, hospitals, shelters, relief logistics, family welfare checks, supply requests, and donation pledges.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fjebarson-caleb%2Fdisaster&project-name=resq-command&repository-name=resq-command&env=DATABASE_URL%2CSECRET_KEY%2CJWT_SECRET_KEY%2CMFA_ENCRYPTION_KEY%2CBOOTSTRAP_ADMIN_EMAIL%2CBOOTSTRAP_ADMIN_PASSWORD&envDescription=Persistent%20PostgreSQL%2C%20two%20independent%2032%2B-character%20application%20secrets%2C%20a%20Fernet%20MFA%20key%2C%20and%20the%20first%20administrator.%20See%20the%20deployment%20guide.&envLink=https%3A%2F%2Fgithub.com%2Fjebarson-caleb%2Fdisaster%2Fblob%2Fmain%2Fdocs%2FBETA_DEPLOYMENT.md)

## Deploy on Vercel

The repository is configured as a Vercel Services project: Vite serves `/`, Flask serves `/api`, and both share one domain. Click the button, keep the preset as **Services** and the root as `./`, enter the six prompted production values, then click **Deploy**.

A persistent PostgreSQL database is mandatory for a real beta. Vercel Functions only provide temporary `/tmp` storage, so SQLite is intentionally rejected by the production readiness check. The exact setup, secret-generation commands, and post-deploy checks are in [Beta deployment](docs/BETA_DEPLOYMENT.md).

## Production safeguards

- Revocable server-side sessions in `Secure`, `HttpOnly`, `SameSite=Lax` cookies
- CSRF validation for cookie-authenticated writes and short-lived bearer tokens for API clients
- 15-character minimum passwords, scrypt hashing, login throttling, and timed account lockout
- Mandatory replacement of administrator-issued temporary passwords before any operational API is available
- Encrypted RFC 6238 authenticator MFA, single-use challenges, replay protection, recovery codes, and mandatory privileged-role enrollment
- Hashed, expiring, single-use email password-recovery tokens with full session revocation after reset
- Server-side idle and absolute session expiry, logout, in-app session listing, and per-device revocation
- Role authorization, facility-bound operational accounts, volunteer approval, password reset/change, and security audit events
- Request IDs, generic error responses, payload limits, security headers, no-store API responses, and readiness gates
- Production login wall; demo data and role switching require explicit demo build/runtime flags
- CI for linting, migration drift, warning-free tests, backend coverage, production builds, and dependency vulnerability audits
- Pinned runtime dependencies with automated weekly update proposals
- Versioned, data-preserving database migrations with serialized PostgreSQL/MySQL startup upgrades

These controls are aligned with the OWASP session and authentication guidance linked in [Security and privacy](docs/SECURITY_PRIVACY.md). This is beta software, not a certified public-warning or emergency-dispatch system.

## Features

- Role-aware workspaces for citizens, administrators, police, fire, hospitals, shelters, ambulances, NGOs, and volunteers
- Administrator account directory with activation/deactivation, pending-volunteer verification, facility assignment, re-authenticated password and lost-MFA recovery, and automatic session revocation
- Operational Setup workspace for live resource inventory, responder units, and verified donation campaigns
- Incident reporting, deterministic damage scoring, rescue priority, automatic nearest-team/volunteer/ambulance dispatch, and hospital preparation
- CAP-inspired public alerts, acknowledgements, India-wide alert aggregation, verified field updates, and safe-route advice
- Optional signed, idempotent outbound alert webhook for an approved SMS, siren, radio, or public-warning gateway, with tracked attempts and safe manual retry
- Hospital/shelter capacity, resource inventory, transactional distribution, volunteer assignment, welfare checks, and isolated-survivor supply cases
- Consent-based device location, auditable donation campaigns, offline citizen submission queue, reconnect replay, Leaflet maps, and Chart.js analytics
- Optional Ollama explanations; operational decisions continue with deterministic rules if Ollama is unavailable
- Standard SMTP password recovery that remains disabled until a verified sender, public URL, and provider credentials are configured

The feature-to-problem mapping is documented in [Hackathon alignment](docs/HACKATHON_ALIGNMENT.md).
The provisioning, MFA, workspace, and authorization expectations for every login are documented in [Role access](docs/ROLE_ACCESS.md).

## Local development

Backend:

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env
python run.py
```

Frontend, in another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. For the controlled local role-switching demo, keep `DEMO_MODE=true` in `backend/.env` and start Vite with `VITE_DEMO_MODE=true`. Seeded demo accounts use `DemoPassword123!` with addresses such as `admin@rescue.local` and `citizen@rescue.local`. Never enable demo mode on a public deployment.

## Verification

```bash
cd backend
python -m ruff check .
python -m pip_audit -r requirements-dev.txt
flask --app run:app db upgrade
flask --app run:app db check
pytest -q -W error --cov=app --cov-report=term-missing --cov-fail-under=75

cd ../frontend
npm ci
npm audit --audit-level=high
npm run lint
npm run build
npx playwright install chromium
BASE_URL=https://disaster-delta-eight.vercel.app npm run test:e2e -- --project=chromium
```

The browser smoke only fills synthetic values and does not submit registration, login, or recovery forms. On PowerShell, set `$env:BASE_URL` before the test command. The liveness endpoint is `/api/v1/health`; the database/configuration readiness endpoint is `/api/v1/ready`.

## Documentation

- [Beta deployment and operations](docs/BETA_DEPLOYMENT.md)
- [Security and privacy](docs/SECURITY_PRIVACY.md)
- [Role access and onboarding](docs/ROLE_ACCESS.md)
- [Hackathon problem alignment](docs/HACKATHON_ALIGNMENT.md)
- [Software requirements](docs/SRS.md)
- [Relational schema](docs/RELATIONAL_SCHEMA.md)
- [Data dictionary](docs/DATA_DICTIONARY.md)
