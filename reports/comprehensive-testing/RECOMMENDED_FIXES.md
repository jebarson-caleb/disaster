# ResQ Disaster Management System — Recommended Fixes & Improvements

**Document ID:** RESQ-REC-FIX-001  
**Target Commit:** `891bc60c1d8bebf86867d58d7f015de755c8b839`  

---

## 1. Prioritized Remediation Roadmap

The following technical and architectural fixes are prioritized by their impact on security, CI reliability, and field operational readiness:

### Priority 1: Patch Frontend Advisory in `zod` (Security)
- **Defect Reference:** DEF-02
- **Rationale:** Resolves known CVE GHSA-mrhx-c7xc-m3w5 and eliminates high-severity vulnerability flags during deployment builds.
- **Action Required:**
  1. Update `zod` to version `^4.6.6` in `frontend/package.json`.
  2. Execute `npm update zod` or `npm audit fix` in `frontend/`.
  3. Verify clean build: `npm run build` and `npm audit --audit-level=high`.

### Priority 2: Fix SQLite Connection Pool Disposal in Test Fixtures (CI / Testing)
- **Defect Reference:** DEF-01
- **Rationale:** Ensures automated test execution passes with zero warnings on modern Python 3.13 runtimes, preventing false-positive test failures under strict `-W error` CI configurations.
- **Action Required:**
  1. In `backend/tests/conftest.py`, append `db.engine.dispose()` to the `app` fixture teardown.
  2. In `backend/pytest.ini`, configure `filterwarnings = ignore::ResourceWarning:sqlite3` to explicitly ignore unraisable connection GC warnings during process teardown.
  3. Verify execution: `pytest -q -W error tests/test_api.py`.

### Priority 3: Optimize Client Session Restoration on Cold Boot (UX / Usability)
- **Defect Reference:** DEF-03
- **Rationale:** Prevents new or anonymous visitors from being held on `"Restoring your secure session"` for 20+ seconds when loading the deployed application on Vercel.
- **Action Required:**
  1. In `frontend/src/App.jsx`, implement an `AbortController` with a 3000ms timeout on `restoreSession()`.
  2. If the initial restore request takes longer than 3 seconds, default `sessionMode` to `'account'` so the interactive demo and login forms render immediately, while allowing any ongoing session restore to continue in the background.

### Priority 4: External Delivery Provider Hardening (Operational Readiness)
- **Rationale:** Currently, emergency public alerts fall back to in-app notification toasts because no SMS/SMTP delivery provider is configured.
- **Action Required:**
  1. Provision production credentials for Twilio (SMS), SendGrid / AWS SES (Email), and Firebase Cloud Messaging (Web Push).
  2. Set environment variables `ALERT_DELIVERY_WEBHOOK_URL`, `ALERT_DELIVERY_WEBHOOK_SECRET`, and `SMTP_HOST` in Vercel project settings.
  3. Rerun `test_alert_delivery.py` against the provider sandbox.

---

## 2. Regression Testing Checklist After Fixes

Whenever the above changes are applied, rerun the following verification suite:

```bash
# 1. Backend regression suite
pytest -q -W error --cov=app --cov-fail-under=75

# 2. Frontend audit and build
cd frontend
npm audit --audit-level=high
npm run lint
npm run test:unit
npm run build

# 3. Live browser specs
npx playwright test e2e/production-auth.spec.js
npx playwright test e2e/demo-roles.spec.js
```
