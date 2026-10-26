# ResQ Disaster Management System — Defect Log

**Document ID:** RESQ-DEF-LOG-001  
**Target Commit:** `891bc60c1d8bebf86867d58d7f015de755c8b839`  

---

## Defect Summary Table

| Defect ID | Severity | Component | Summary | Status |
| :--- | :---: | :--- | :--- | :---: |
| **DEF-01** | High | Backend Test Runner (`pytest` / SQLite) | Python 3.13 SQLite `ResourceWarning` crashes test suite under `-W error` | Identified / Workaround Verified |
| **DEF-02** | High | Frontend Dependencies (`zod`) | GHSA-mrhx-c7xc-m3w5: Zod memory exhaustion vulnerability in constrained collections | Identified / Upgrade Required |
| **DEF-03** | Medium | Deployment / UX (Vercel Serverless) | Serverless cold start latency on `/api/v1/auth/me` causes auth gate loading delay | Identified / Architecture Consideration |

---

## Defect Details

### DEF-01: Python 3.13 SQLite ResourceWarning with `-W error`
- **Severity:** High (Blocks CI on Python 3.13 runtimes)
- **Environment:** Windows, Python 3.13.14, Pytest 9.1.1, SQLAlchemy 2.1.6
- **Preconditions:** Run `pytest -q -W error` on Python 3.13.
- **Reproduction Steps:**
  1. Set up a Python 3.13 environment with `requirements-dev.txt`.
  2. Execute: `pytest -q -W error tests/test_api.py -k "test_resource_distribution_and_volunteer_assignment_are_transactional"`.
- **Expected Result:** Test session completes with exit code 0.
- **Actual Result:** Pytest exits with code 1:
  ```text
  ResourceWarning: unclosed database in <sqlite3.Connection object>
  pytest.PytestUnraisableExceptionWarning: Exception ignored in: <sqlite3.Connection object>
  ```
- **Root Cause:** Python 3.13 introduced stricter garbage collection checks for unclosed SQLite connection handles. SQLAlchemy's connection pool in test fixtures does not explicitly invoke `db.engine.dispose()` during teardown in `backend/tests/conftest.py`. When `-W error` is passed, the warning is treated as an error by pytest.
- **Recommended Fix:**
  In `backend/tests/conftest.py`, update the `app` fixture teardown:
  ```python
  @pytest.fixture()
  def app():
      application = create_app(TestConfig)
      with application.app_context():
          db.create_all()
          yield application
          db.session.remove()
          db.drop_all()
          db.engine.dispose()  # Explicitly close and dispose connection pool
  ```
  Additionally, add `filterwarnings = ignore::ResourceWarning:sqlite3` in `backend/pytest.ini`.

---

### DEF-02: High-Severity Advisory in Client Dependency `zod`
- **Severity:** High
- **Advisory ID:** GHSA-mrhx-c7xc-m3w5
- **Affected Component:** `frontend/package.json` (`zod < 4.6.6`)
- **Vulnerability Description:** Zod can exhaust memory while validating oversized constrained collections, enabling potential client-side denial of service.
- **Reproduction Steps:**
  1. Navigate to `frontend/`.
  2. Run `npm audit`.
  3. Notice `1 high severity vulnerability in zod`.
- **Expected Result:** 0 vulnerabilities reported by `npm audit`.
- **Actual Result:** 1 High severity advisory reported.
- **Recommended Fix:**
  Run `npm audit fix` or update `package.json` to specify `"zod": "^4.6.6"`, followed by `npm install` and verification of `npm run build`.

---

### DEF-03: Serverless Cold Start Causes Auth Gate Loading Delay
- **Severity:** Medium (Usability / User Experience)
- **Environment:** Live Hosted Application (`https://disaster-delta-eight.vercel.app/`)
- **Preconditions:** Application backend has been idle on Vercel for $>15$ minutes.
- **Reproduction Steps:**
  1. Open a new incognito browser window.
  2. Navigate to `https://disaster-delta-eight.vercel.app/`.
- **Expected Result:** Sign-in screen appears within 2-3 seconds.
- **Actual Result:** The screen remains on `"Restoring your secure session"` with a loading spinner for 15-25 seconds while the Vercel Python Serverless Function cold-boots and responds to `GET /api/v1/auth/me` with 401.
- **Root Cause:** Single-page app frontend blocks the sign-in form until `restoreSession()` resolves. During a serverless cold boot, the WSGI container takes time to initialize.
- **Recommended Fix:**
  1. In `frontend/src/App.jsx`, add an initial timeout (e.g. 3.5 seconds) to `restoreSession()`; if not resolved within that window, render the login/demo screen with a background session check, rather than blocking the user.
  2. Configure a periodic health check cron or keep-alive ping to maintain at least one warm container instance.
