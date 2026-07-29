# ER Diagram Notes

Use these relationships to draw the ER diagram:

- `users` 1--1 `role_profiles`
- `role_profiles` N--1 optional `hospitals`, `shelters`, or `ambulances` for managed-facility access
- `users` 1--1 `account_security`
- `users` 1--N `auth_sessions`, `password_reset_tokens`, `audit_events`, `mfa_challenges`, and 1--1 `mfa_credentials`
- `users` 1--N `disasters` through `reported_by_id`
- `users` 1--N `rescue_requests` through `requester_id`
- `disasters` 1--N `rescue_requests`
- `rescue_requests` 1--N `rescue_status_history`
- `hospitals` 1--N `hospital_capacity_logs`
- `hospitals` 1--N `ambulances`
- `shelters` 1--N `shelter_capacity_logs`
- `ambulances` 1--N `ambulance_dispatches`
- `rescue_requests` 1--N `ambulance_dispatches`
- `resources` 1--N `resource_distribution`
- `disasters` 1--N `resource_distribution`
- `users` 1--N `volunteers`
- `volunteers` 1--N `volunteer_assignments`
- `disasters` 1--N `volunteer_assignments`
- Operational entities 1--N `ai_assessments` through `(entity_type, entity_id)`
- `users` 1--N `emergency_alerts` through `sender_id`
- `emergency_alerts` 1--N `alert_acknowledgements`
- `users` 1--N `alert_acknowledgements`
- `disasters` 1--N `disaster_news_updates`
- `users` 1--N `welfare_checks` as requester and optional responder
- `disasters` 1--N `welfare_checks`
- `hospitals` 1--N `hospital_notifications`
- `rescue_requests` 1--N `hospital_notifications`
- `users` 1--N `supply_requests`
- `disasters` 1--N `supply_requests`
- `disasters` 1--N `donation_campaigns`
- `donation_campaigns` 1--N `donations`
- `users` 1--N `location_pings`
- `rescue_requests` 1--N `location_pings`
- `supply_requests` 1--N `location_pings`
- `rescue_requests` 1--N `response_dispatches`
- `responder_units` are allocated through `response_dispatches.responder_type/responder_id`
