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
| Role ambiguity | Demo sessions and backend-enforced permissions for all SRS actors | `POST /api/v1/auth/demo-session` in demo mode |

## Scope boundary

SMS, siren, radio, and volunteer relay are represented as delivery channels and operational records. Actual telecom or siren-provider dispatch requires provider credentials and is intentionally outside this local MVP. Navigation is advisory and explicitly defers to official closures and responder instructions.
