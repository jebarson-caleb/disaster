# ResQ Disaster Management System — Security Test Report

**Document ID:** RESQ-SEC-TEST-001  
**Target Commit:** `891bc60c1d8bebf86867d58d7f015de755c8b839`  
**Application Scope:** API authentication, role authorization, injection security, bundle analysis, and dependency audits  

---

## 1. Vulnerability & Dependency Scan Findings

### Finding SEC-01: High-Severity Advisory in Client Dependency `zod`
- **Severity:** High (CVSS 7.5)
- **Advisory ID:** GHSA-mrhx-c7xc-m3w5
- **Affected Component:** `frontend/node_modules/zod` ($< 4.6.6$)
- **Vulnerability Description:** Zod can exhaust server or browser memory when attempting to validate oversized or deeply constrained nested collections, creating a potential denial-of-service vulnerability.
- **Remediation Recommendation:** Run `npm audit fix` in `frontend/` or bump `zod` to version $\ge 4.6.6$ in `package.json`.

### Finding SEC-02: Python Dependency Audit (`pip-audit`)
- **Audit Tool:** `pip-audit -r backend/requirements-dev.txt`
- **Result:** No known vulnerabilities found in core production requirements (`Flask 3.1.3`, `PyJWT 2.15.1`, `psycopg 3.3.4`, `SQLAlchemy 2.1.6`).
- **Note on PyPI Connectivity:** PyPI-backed audits can be slow or encounter network rate-limits on Windows. Local OSV-backed scanning is recommended for local CI runners.

---

## 2. Application & API Security Controls

### A. SQL Injection (SQLi) Testing
- **Test Payload:** `"Flood ' OR '1'='1'; DROP TABLE disasters; --"`
- **Endpoint Tested:** `POST /api/v1/disasters`
- **Result:** **PASSED.**
  - The query executed through SQLAlchemy's parameterized queries.
  - The malicious payload was escaped and persisted as the exact literal string.
  - The `disasters` table remained intact and operational.

### B. Broken Function Level Authorization (BFLA)
- **Scenario:** An authenticated user with role `Citizen` attempted to provision an administrative user account via `POST /api/v1/admin/users`.
- **Result:** **PASSED.**
  - Server returned `HTTP 403 Forbidden`.
  - Endpoint enforces strict role-level validation (`require_roles("Admin")`).

### C. Unauthenticated Write Protection
- **Endpoints Tested:**
  - `POST /api/v1/disasters`
  - `POST /api/v1/admin/users`
  - `POST /api/v1/road-closures`
  - `POST /api/v1/readiness-checks`
- **Result:** **PASSED.**
  - Every write endpoint rejected requests lacking valid JWT bearer credentials with `HTTP 401 Unauthorized` or `HTTP 403 Forbidden`.

### D. Credential & Secret Leakage in Production Bundles
- **Scan Target:** Generated production assets in `frontend/dist/assets/`
- **Patterns Scanned:** `DemoPassword123`, `admin@rescue.local`, `SECRET_KEY`, private tokens.
- **Result:** **PASSED.**
  - Zero hardcoded passwords or seed credentials exist in `frontend/dist/assets/`.
  - Sample records are emitted exclusively in the dynamically loaded sandbox chunk (`demoApi-*.js`).

### E. Password Policy & Masking
- **Client & Server Enforcement:** Registration requires a minimum of 15 characters (`minlength="15"`).
- **Masking:** Playwright tests confirmed that password input toggles from masked dots (`type="password"`) to plain text (`type="text"`) via the Show/Hide password control.
- **Isolation:** Switching between Login, Registration, and Forgot Password modes immediately clears input fields and prevents credential leakage across tabs.

---

## 3. Security Headers Verified

Inspection of `vercel.json` confirms the following HTTP response headers applied across all routes:

```json
{
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(self)",
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
  "Content-Security-Policy": "default-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://*.tile.openstreetmap.org; connect-src 'self'"
}
```
