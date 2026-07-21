# Hackathon Problem Alignment

This implementation treats the repository SRS as its primary acceptance statement and uses public disaster-management challenge statements to validate that the solution addresses operational problems rather than only presenting a dashboard.

## Referenced problems

1. **Dynamic evacuation and uncertain public behaviour.** A Smart India Hackathon 2022 NDRF problem description notes that disasters are dynamic and that evacuation during floods and cyclones is complicated by uncertain human behaviour. Source: [Agni College SIH 2022 summary](https://act.edu.in/achievements/smart-india-hackathon-2022-software-edition/).
2. **Risk assessment and cross-organization coordination.** Techathon 3.0 lists disaster risk assessment before an event and coordination of rescue, relief, and volunteers during disasters as separate software challenges. Source: [Techathon 3.0 problem statements](https://innovateyou.in/problem-statement-for-techathon-3-0-latest-hackathon-in-maharashtra-india/).
3. **End-to-end, inclusive early warning.** The UN Early Warnings for All initiative defines four connected pillars: risk knowledge, monitoring and forecasting, warning dissemination, and preparedness/response. Source: [United Nations Early Warnings for All](https://www.un.org/en/climatechange/early-warnings-for-all).
4. **Last-mile reach and authoritative messaging.** The UN multi-hazard early-warning status report highlights CAP, multiple technology and community channels, inter-agency coordination, an authoritative voice, and acknowledgement of last-mile connectivity gaps. Source: [UN report](https://www.un.org/ohrlls/sites/www.un.org.ohrlls/files/2._status_of_multi-hazard_early_warning_systems_in_the_least_developed_countries.pdf).

## Implemented response

| Problem | Implemented feature | Verification |
| --- | --- | --- |
| Fragmented operational data | Authenticated one-request bootstrap for incidents, rescues, facilities, resources, and alerts | `GET /api/v1/operations/bootstrap` |
| Delayed or lost citizen reports | Local offline queue, optimistic UI, online/offline state, and reconnect replay | Disconnect backend, submit a report, reconnect |
| Unclear or conflicting warnings | CAP-inspired alert fields with authoritative role restrictions, audience, channels, message, action instruction, urgency, severity, and certainty | `POST /api/v1/alerts` |
| Unknown warning reach | Idempotent per-user alert receipt confirmation with optional coordinates and aggregate acknowledgement count | `POST /api/v1/alerts/{id}/acknowledge` |
| Unsafe or capacity-blind evacuation | Nearest available shelter/hospital selection, nearby-hazard context, advisory guidance, and navigation link | `GET /api/v1/safe-route` |
| Resource and volunteer silos | Shared inventory/distribution/volunteer snapshot; allocation decrements inventory and assignments change availability atomically | `GET /api/v1/coordination` |
| Slow prioritization | Deterministic, offline-capable damage and rescue scoring with audit records | `/api/v1/ai/*` and `ai_assessments` |
| Role ambiguity | Production login wall, administrator-provisioned operational roles, backend authorization, and controlled demo sessions | `/api/v1/auth/*`; demo endpoint only when explicitly enabled |
| Loss of trust through insecure shared access | Revocable server-side sessions, mandatory privileged-role authenticator MFA, CSRF defense, lockout, audit events, request IDs, reviewed migrations, and production readiness gates | `/api/v1/auth/mfa/*`, `/api/v1/auth/sessions`, `/api/v1/ready`, `audit_events` |
| Regional information silos | Public India-wide active incident, warning, and verified field-news aggregation | `GET /api/v1/national-alerts` |
| Unverified or missing disaster-area coverage | Authorized, source-labelled field updates with optional live-stream URLs and verification state | `GET/POST /api/v1/news-updates` |
| Families cannot trace relatives in affected areas | Consent-based welfare-check cases, emergency calling, responder ownership, notes, and status tracking | `/api/v1/welfare-checks` |
| Manual dispatch delays | Transactional nearest professional rescue unit, registered volunteer, and required ambulance allocation using incident coordinates; assets are released when the rescue closes | `POST /api/v1/rescue-requests`, `responder_units`, and `response_dispatches` |
| Hospitals receive patients without warning | Automatic nearest-capacity hospital notice with patient count, priority, condition, and acknowledgement | `/api/v1/hospital-notifications` |
| Victims are isolated but not medically trapped | Dedicated food, water, medicine, and essential-supply cases with coordinator status tracking | `/api/v1/supply-requests` |
| Responders cannot locate remote callers | Explicit browser-consent geolocation capture with accuracy and case linkage | `POST /api/v1/location-pings` |
| Rescue funding lacks an auditable path | Campaign, pledge, payment handoff, confirmation, refund status, and aggregate totals | `/api/v1/donation-campaigns` and `/api/v1/donations` |

## Scope boundary

SMS, siren, radio, and volunteer relay are represented as delivery channels and operational records. Actual telecom or siren-provider dispatch requires provider credentials and is intentionally outside this local MVP. Navigation is advisory and explicitly defers to official closures and responder instructions. Donation pledges are auditable without a payment provider; actual online collection is enabled only when an approved `DONATION_PAYMENT_URL` is configured. Device location is never requested or stored without an explicit user action and consent.
