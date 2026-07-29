# Beta Deployment and Operations

## Vercel release checklist

1. Provision PostgreSQL through a Vercel Marketplace integration such as Neon, or another managed provider. Copy its pooled, TLS-enabled connection URL to `DATABASE_URL`. Do not use SQLite on Vercel; the writable `/tmp` directory is temporary.
2. Generate two different application secrets. For example, run `openssl rand -hex 32` twice and assign the results to `SECRET_KEY` and `JWT_SECRET_KEY`.
3. Generate the independent MFA encryption key with `python -c "import base64,secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"` and assign it to `MFA_ENCRYPTION_KEY`.
4. Set `BOOTSTRAP_ADMIN_EMAIL` and a unique `BOOTSTRAP_ADMIN_PASSWORD` of at least 15 characters. Set `BOOTSTRAP_ADMIN_NAME` and `BOOTSTRAP_ADMIN_PHONE` if desired.
5. Leave `DEMO_MODE=false`, `APP_ENV=production`, `AUTO_MIGRATE=true`, and `COOKIE_SECURE=true`. These are already the Vercel defaults. Do not set `VITE_DEMO_MODE` on production builds.
6. Optional but recommended for multi-instance beta traffic: provision Redis and set `RATELIMIT_STORAGE_URI` to its TLS `rediss://` URL. Database-backed account lockout remains active even when this is not configured.
7. Keep the Vercel application preset as **Services**, root directory `./`, frontend service `frontend` (Vite), and backend service `backend` (`index:app`). Deploy.

## Required environment variables

| Variable | Requirement |
| --- | --- |
| `DATABASE_URL` | Persistent `postgresql://...` or `mysql+pymysql://...` database; PostgreSQL is recommended |
| `SECRET_KEY` | Random 32+ character secret, different from the JWT secret |
| `JWT_SECRET_KEY` | A second independent random 32+ character secret |
| `MFA_ENCRYPTION_KEY` | URL-safe base64 encoding of 32 independent random bytes; use the command above |
| `BOOTSTRAP_ADMIN_EMAIL` | First authorized administrator email |
| `BOOTSTRAP_ADMIN_PASSWORD` | Unique 15–128 character initial administrator password |

Optional production variables include `RATELIMIT_STORAGE_URI`, `CORS_ORIGINS`, `EMERGENCY_HOTLINE`, `DONATION_PAYMENT_URL`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `PUBLIC_BASE_URL`, `PASSWORD_RESET_MINUTES`, and the `SMTP_*` settings documented in `backend/.env.example`.

## Database migrations

Checked-in Alembic migrations run automatically before the backend accepts requests. PostgreSQL and MySQL deployments use a database advisory lock so concurrent cold starts cannot apply the same migration at once. A database created by an earlier `db.create_all()` release is detected, validated against the supported legacy schema, stamped, upgraded, and kept intact. Startup fails instead of guessing when an unversioned database is incomplete or only partially upgraded.

Before merging a model change, generate and review its migration, test it against a production-like backup, and run:

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
```

Keep `AUTO_MIGRATE=true` for the Vercel one-click flow. Teams that later move migrations into a dedicated release job may set it to `false` only after replacing the startup step and updating the readiness/release procedure.

## Acceptance checks

After deployment:

1. Open `https://<deployment>/api/v1/health`; expect HTTP 200 and `status: ok`.
2. Open `https://<deployment>/api/v1/ready`; expect HTTP 200, `status: ready`, and both checks `true`. A 503 means the release must not receive beta traffic; inspect Vercel function logs using the returned request ID.
3. Open the site in a private browser. Confirm operational data is hidden behind the login screen.
4. Sign in as the bootstrap administrator and replace the bootstrap password. The temporary-password gate must prevent access to operational data until this succeeds.
5. Enroll an authenticator, save the one-time recovery codes offline, sign out, and verify both authenticator-code and recovery-code login. Every privileged role listed in `MFA_REQUIRED_ROLES` is restricted to MFA setup until enrollment completes. If SMTP recovery is enabled, request a password-reset link, verify its expiry/single-use behavior, and confirm completion revokes every prior session while leaving MFA required.
6. Open **User Access** and provision one account for each operational role in use. Hospital, shelter, and ambulance accounts must be assigned to an existing facility or create their facility atomically. Confirm every issued password must be replaced on first sign-in.
7. For hospital, shelter, and ambulance accounts, confirm the workspace shows only the assigned operational record and rejects attempts to update another facility. For citizens, confirm rescue lists contain only cases created by that citizen.
8. Open **Operational Setup** and register at least one resource and professional responder unit. Create a non-critical incident and verify automatic dispatch, hospital preparation, capacity updates, and role-specific status actions. Manual rescue and supply assignment must accept only a registered available asset, reserve it while active, and release it after completion or cancellation.
9. Test account deactivation/reactivation, administrator-assisted password reset, active-session revocation, a non-critical alert, Citizen registration and tracking, mobile layout, location consent denial/approval, offline submission/reconnect, and the emergency hotline.

The complete expected login and workspace matrix is in [Role access](ROLE_ACCESS.md).

The checked-in production smoke workflow runs after every `main` push and daily. It rejects known demo strings in the browser bundle, a reachable demo-session endpoint, malformed JSON acceptance, privileged self-registration, failed readiness/database checks, and missing security headers.

## Real-user cutover and acceptance-data removal

Never delete production-looking rows with an ad hoc SQL statement. The checked-in maintenance command recognizes only the exact `.training@resq-command.local` acceptance cohort and the three explicitly named training facilities. It blocks if any target is linked to an incident, rescue, dispatch, welfare case, supply request, donation, location ping, alert, news update, or other operational record. Security audit rows are retained with their deleted user reference anonymized.

Run the read-only preview first with the production environment loaded:

```bash
cd backend
vercel env run -e production -- python -m scripts.purge_training_data
```

Proceed only when `state` is `ready`, `problems` and `blockers` are empty, and every listed email/facility is an intended acceptance fixture:

```bash
vercel env run -e production -- python -m scripts.purge_training_data \
  --execute --confirmation PURGE_TRAINING_DATA
vercel env run -e production -- python -m scripts.purge_training_data
```

The final preview must report `state: already_clean`. Keep demo accounts, demo seed code, and test fixtures in source control only; they are required for deterministic CI and controlled local demonstrations. `DEMO_MODE=false`, an unset `VITE_DEMO_MODE`, a disabled production demo-session endpoint, and the production bundle smoke check prevent those credentials and records from entering the public runtime.

After cleanup, keep the bootstrap administrator as the only initial identity. Citizens and volunteers may register through the public account flow; volunteers remain pending until an administrator verifies them. Provision every privileged or facility role through **User Access**, using unique real email/phone details, first-login password replacement, and mandatory MFA.

## Integration cutover matrix

| Capability | Live requirement | Safe fallback |
| --- | --- | --- |
| Application hosting | Vercel Services project with frontend and backend services | None; both services are required |
| Persistent database | Attached managed PostgreSQL/Neon resource and pooled TLS `DATABASE_URL` | None; readiness rejects SQLite in production |
| Maps | Browser access to OpenStreetMap tiles; external navigation is advisory | Typed coordinates and address remain available |
| Shared throttling | TLS Redis URL in `RATELIMIT_STORAGE_URI` for horizontally scaled traffic | Per-instance throttling plus database-backed account lockout |
| Public alert delivery | Approved SMS/siren/radio provider, recipient governance, credentials, and a delivery adapter | CAP-inspired alert and acknowledgement records inside the authenticated application only |
| Online donations | Approved hosted checkout in `DONATION_PAYMENT_URL` plus the provider's independent settlement/reconciliation process | Auditable pledge records; no money is represented as collected |
| AI explanations | Reachable, privacy-approved Ollama service in `OLLAMA_BASE_URL` | Deterministic, tested scoring without transmitting personal data |
| Email recovery | Standard SMTP host/port, verified `SMTP_FROM_EMAIL`, `PUBLIC_BASE_URL`, credentials when required, delivery monitoring, and support ownership | Administrator-assisted password reset with re-authentication and session revocation |

Do not label an optional provider as integrated merely because an environment-variable slot exists. Activation requires provider credentials, contractual/organizational approval, a non-production delivery test, failure/retry monitoring, and a production reconciliation test. Provider secrets must remain in Vercel environment storage and never appear in source control or browser payloads.

## Operational boundaries

- Call/SMS/siren/radio values are coordination records; actual delivery needs an approved communications provider and credentials.
- `DONATION_PAYMENT_URL` is only a handoff to an approved checkout. Without it, donations are recorded as pledges and no money is collected.
- Safe routes are advisory and must not override official closures or responder instructions.
- Device location is captured only after an explicit browser action and consent.
- Ollama is optional; deterministic scoring remains available without it.

## Beta operations

- Limit the first cohort, name an incident commander and privacy contact, and publish support/escalation channels before inviting users.
- Monitor Vercel errors, readiness, database capacity, failed login/audit events, dispatch queues, and unacknowledged hospital notices.
- Back up PostgreSQL daily and perform a restoration drill before handling real incidents.
- Rotate initial administrator credentials after first use. Rotate application secrets through a coordinated maintenance window because doing so invalidates active sessions.
- Review pending volunteer registrations in **User Access** and verify identity/affiliation out of band before approving access.
- Verify organization and facility ownership out of band before assigning an operational account to an existing hospital, shelter, or ambulance.
- Define retention periods for location, welfare, contact, and audit data before collecting real personal information.
- Roll back the Vercel deployment if readiness fails or critical workflows regress. Do not silently fall back to demo data in production.

## Release gate

The code is beta-deployable when CI passes, the production dependency audits report no known vulnerabilities, and `/ready` is green. Public emergency use additionally requires organizational authorization, accessibility/user testing, threat modeling, provider integrations, data-protection review, service-level monitoring/on-call coverage, backup recovery evidence, and field exercises. Those are operational approvals and cannot be supplied by source code alone.
