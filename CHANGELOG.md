# Changelog

All notable changes to this project are documented here.

## 1.3.4 - 2026-07-31

### Added

- Guarded, dry-run-first provisioning and credential verification for the requested live test-role cohort.
- Credential reissue limited to accounts previously created by the managed test-account command.
- Production verification of password hashes, direct-login state, verified profiles, and required facility or volunteer bindings.

### Changed

- Sign-in accepts existing account passwords without applying the new-password length constraint in the browser; registration and password changes still enforce 15 or more characters.
- Password authentication now opens the user’s server-authorized role workspace directly.
- Managed live test accounts use reusable credentials and no first-login password-replacement gate.

### Removed

- MFA login challenges, enrollment, recovery-code controls, administrator MFA reset, and the production MFA-key requirement.

### Security

- Live test-role accounts require unique policy-compliant passwords and remain restricted by server-side role authorization.
- Non-operational facility bindings start with zero capacity or offline status so incomplete configuration cannot be represented as an available emergency resource.

## 1.3.3 - 2026-07-30

### Added

- A production-mode full-stack browser acceptance gate that signs every supported role in through the real account UI.
- End-to-end MFA enrollment, recovery-code challenge, role-locking, and live-workspace verification for every privileged role.

## 1.3.2 - 2026-07-30

### Added

- Public version and Git-commit provenance in the liveness response without exposing configuration or secrets.
- A Vercel readiness requirement for a valid Git commit SHA.
- Production smoke enforcement that the public alias serves the exact pushed commit and application version.

## 1.3.1 - 2026-07-30

### Added

- Administrator-only integration readiness reporting with active/fallback modes and required environment-variable names.
- A secret-safe Operational Setup panel covering the database, public-warning gateway, email recovery, hosted payments, shared throttling, private AI, and maps.
- Authorization, privacy, configured-provider, and full-stack browser acceptance coverage for the readiness view.

## 1.3.0 - 2026-07-29

### Added

- Signed, idempotent HTTPS delivery of public-warning payloads to an approved external communications gateway.
- Fail-closed webhook configuration checks, bounded provider timeouts, sanitized audit outcomes, persistent attempt status, and safe manual retry.
- Public-warning workspaces for every authorized command role, plus full-stack browser coverage for in-app publishing and delivery state.

## 1.2.2 - 2026-07-29

### Fixed

- Made Shelter expected-arrival tracking and Volunteer hazard reporting directly reachable from both role navigation and dashboard actions.

### Added

- Isolated full-stack Chromium acceptance coverage for every advertised workspace across all nine supported roles.

## 1.2.1 - 2026-07-29

### Fixed

- Authentication mode changes now remount and clear credential fields so browser-autofilled sign-in secrets cannot carry into public registration.
- Leaving a password-reset link now removes its token from the address bar and clears the recovery draft.
- Account registration and recovery screens now present mode-specific guidance and explicit autofill field names.
- Production smoke now exercises account-mode credential isolation, recovery navigation, and mobile login usability in Chromium without creating users.

## 1.2.0 - 2026-07-29

### Added

- Standard SMTP self-service password recovery with hashed, expiring, single-use tokens and a complete browser flow.
- Data-preserving password-recovery migration and upgrade coverage from every previously supported schema release.
- Production validation for optional payment, Ollama, Redis, SMTP, and public-base URL configuration.

### Changed

- Completing password recovery revokes all active sessions and pending password-derived MFA challenges while preserving configured MFA.
- Optional Ollama prompts now use a strict allowlist of non-identifying operational fields.
- Hosted donation checkout URLs preserve approved provider parameters and fragments while safely adding the auditable reference, amount, and currency.

### Security

- Password-reset requests use generic anti-enumeration responses and rate limits; failed mail delivery invalidates the generated token.
- Donation inputs reject non-finite amounts, malformed email addresses, and invalid donor names.
- Donation status changes are recorded in the security/operations audit trail.

## 1.1.3 - 2026-07-29

### Added

- Password confirmation and optional-coordinate validation in public and first-login account flows.
- Production smoke probes for demo-data leakage, disabled demo sessions, malformed JSON bodies, privileged self-registration, public feeds, readiness, and security headers.
- Regression coverage for idle/absolute session expiry and MFA-challenge invalidation across password changes, administrator resets, and account deactivation.

### Changed

- Rescue and supply assignment now reserves only registered, currently available operational assets and exposes the server-confirmed asset state to coordinators.
- Rescue, ambulance, hospital, shelter, volunteer, and facility actions update the interface only after the API confirms the mutation.
- Offline rescue and incident submissions are visibly marked as device-queued until synchronization succeeds.

### Security

- Password rotation, administrator password reset, and deactivation invalidate every pending password-derived MFA challenge.
- Current-device session revocation instructs the browser to clear cookies, cache, and storage.
- JSON API endpoints reject non-object request bodies before route processing.

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
