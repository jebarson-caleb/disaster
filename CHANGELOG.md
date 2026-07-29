# Changelog

All notable changes to this project are documented here.

## 1.1.2 - 2026-07-29

### Added

- Dry-run-first, dependency-guarded production acceptance-data cleanup with retained anonymized audit history.
- Regression coverage proving cleanup refuses to delete accounts or facilities referenced by operational records.

### Changed

- Production client state now begins empty and is populated only by the authenticated live API; demo incidents, teams, facilities, inventory, trends, ETAs, and readiness values remain isolated to explicit demo mode.
- Manual rescue assignment now selects only registered available responder units or ambulances.
- Live readiness and response trends are calculated from current operational records instead of presentation fixtures.

### Operations

- Removed the marked production acceptance accounts and facilities after a clean dependency preview and revoked their sessions while retaining anonymized security events.
- Verified the Vercel Marketplace Neon resource is installed, attached, and available.

## 1.1.1 - 2026-07-28

### Added

- Audited administrator-assisted MFA reset for users who have lost both their authenticator and recovery codes.
- MFA enrollment state in the administrator access directory.

### Changed

- Authenticated security and administrator action limits are isolated per account so users on one shared office network cannot exhaust one another’s quotas.

### Security

- Administrator MFA resets require password re-authentication, revoke the target user’s sessions and pending challenges, and force privileged roles through fresh MFA enrollment.

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
