# Changelog

All notable changes to this project are documented here.

## 1.1.0 - 2026-07-27

### Added

- Secure first-login password replacement for every administrator-provisioned or reset account.
- Facility assignment and atomic hospital, shelter, or ambulance creation during user provisioning.
- In-app active-session review and per-device revocation.
- Administrator Operational Setup forms and APIs for resources, responder units, and donation campaigns.
- Role-by-role onboarding acceptance coverage for all nine supported logins.

### Changed

- Citizen rescue queues are requester-scoped.
- Hospital, shelter, ambulance, and volunteer workspaces and mutations are assignment-scoped.
- Hospital preparation notices and responder dispatch data are filtered to the assigned operational identity.

### Security

- Existing administrator accounts are forced through one password rotation after the onboarding migration.
- Temporary-password restrictions are enforced server-side before MFA and operational authorization checks.

## 1.0.0 - 2026-07-27

### Added

- Production PostgreSQL migrations and readiness checks.
- Revocable cookie sessions, CSRF protection, MFA, recovery codes, account lockout, and security audit events.
- Administrator user provisioning, volunteer verification, password reset, session management, and role-aware access controls.
- CI gates for linting, dependency audits, migration drift, warning-free tests, backend coverage, and frontend production builds.
- Security policy, beta deployment runbook, environment template, and operational acceptance checks.

### Changed

- Upgraded vulnerable Python dependencies to audited fixed releases.
- Added frontend hook linting and corrected role-navigation effect handling.
- Split production and development Python dependencies and pinned direct runtime dependencies.

### Security

- Enforced production configuration requirements for persistent storage, independent secrets, secure cookies, disabled demo mode, MFA encryption, and bootstrap administration.
- Added security headers, request identifiers, no-store API responses, payload limits, rate limiting, and generic server errors.
