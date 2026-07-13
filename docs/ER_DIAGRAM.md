# ER Diagram Notes

Use these relationships to draw the ER diagram:

- `users` 1--1 `role_profiles`
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
