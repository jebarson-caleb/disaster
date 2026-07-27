# Changelog

All notable changes to this project are documented here.

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
