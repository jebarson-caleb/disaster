# Security and Privacy

## Implemented controls

Authentication uses scrypt password hashes, a 15–128 character password policy, constant-work invalid-user checks, per-endpoint throttling, and database-backed timed lockout. Administrator-issued and reset passwords are temporary: the account may access only identity, logout, and password-change endpoints until the user replaces the password. Browser sessions use random opaque tokens whose hashes are stored server-side. The session cookie is `HttpOnly`, `Secure` in production, `SameSite=Lax`, and has both idle and absolute expiry. State-changing cookie requests require a matching CSRF cookie/header token. Logout revokes the server record and clears cookies; users can review and revoke their sessions in the account panel. Self-service password changes require the existing password and rotate the current session; administrator resets require administrator re-authentication and revoke all target-user sessions.

RFC 6238 authenticator MFA is available to every account and mandatory by default for administrators and operational agency/facility roles. TOTP seeds are encrypted with an independent Fernet key, password-success challenges are random, database-backed, short-lived, and single use, accepted time steps cannot be replayed, and recovery codes are high-entropy, hashed, and consumed once. First-time privileged sessions can access only enrollment, status, and logout routes until setup succeeds. MFA setup, replacement, disable, and recovery-code rotation require re-authentication and are audit logged.

Operational roles are provisioned by administrators. Hospital, shelter, and ambulance identities are bound to a specific managed record; facility changes and hospital preparation notices are owner-scoped. Rescue cases are filtered to the citizen that created them or to the hospital, ambulance, or volunteer dispatch assignment. Self-registered volunteers remain inactive until an administrator verifies them; rejection or deactivation revokes their active sessions immediately. The in-app User Access directory prevents an administrator from deactivating their own account.

Short-lived JWT bearer tokens remain available for controlled API clients. They include issuer, audience, session ID, issued/not-before/expiry times, and a unique ID; the associated server session must still be active. The browser does not store credentials in `localStorage`.

The API enforces roles, returns generic server errors with request IDs, caps request bodies, emits security headers, disables API caching, and records minimal authentication audit events without passwords or tokens. Production readiness rejects temporary databases, weak/equal secrets, insecure cookies, wildcard credentialed CORS, demo mode, and missing administrator bootstrap configuration. Offline emergency submissions are capped at 50, expire after 24 hours, synchronize when connectivity returns, and are cleared on logout/session expiry; beta operators should still avoid shared-device use for sensitive reports.

Runtime dependencies are pinned and checked in CI with `pip-audit` and `npm audit`. Backend and frontend linting, migration drift detection, warning-free tests, a 75% backend coverage floor, and the production frontend build are release gates. Dependabot proposes weekly Python and npm updates and monthly GitHub Actions updates; every update must pass the same gates before merge.

This design follows the current [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html), [OWASP Multifactor Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html), and [IETF RFC 6238](https://www.rfc-editor.org/rfc/rfc6238).

## Personal and sensitive data

The platform may process names, emails, phone numbers, health/triage information, family welfare requests, and precise location. Collect only what an incident requires. Location must remain opt-in, purpose-bound, access-controlled, and time-limited. Do not put credentials, medical narratives, phone numbers, or coordinates into logs, error trackers, analytics, public alerts, source-control history, or AI prompts.

Before a real beta, the operating organization must publish a privacy notice covering controller/contact details, purpose and legal basis, recipients, retention, cross-border processing, user rights, incident reporting, and emergency exceptions applicable in its jurisdiction. Define deletion/export procedures and restrict database/log access to trained personnel.

## Known beta boundaries

- Email verification, self-service password recovery, phishing-resistant WebAuthn/passkeys, and external identity-provider federation require a verified mail/identity service or additional authenticator implementation and are not configured by this repository.
- Reviewed Alembic migrations create and upgrade the schema automatically with PostgreSQL/MySQL advisory locking. Every future schema change must still be rehearsed against a backed-up, production-like database before release.
- Redis-backed shared throttling is recommended for horizontally scaled traffic; persistent account lockout is already enforced in the primary database.
- No source-code change can certify a platform for official public warnings, emergency dispatch, payments, clinical decisions, or legal compliance. Provider contracts, organizational controls, accessibility testing, penetration testing, and incident exercises remain required.

Report suspected vulnerabilities privately to the beta operator. Do not include real victim data in a vulnerability report.
