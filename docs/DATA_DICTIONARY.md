# Data Dictionary

| Table | Purpose | Important Attributes |
| --- | --- | --- |
| `users` | Stores login identity and role | `email`, `role`, `password_hash` |
| `role_profiles` | Stores the one-to-one organization/location profile and managed-facility assignment | `organization_name`, `verification_status`, `hospital_id`, `shelter_id`, `ambulance_id` |
| `disasters` | Stores reported disaster incidents | `disaster_type`, `people_affected`, `severity_hint`, `status` |
| `rescue_requests` | Stores victim rescue needs | `condition`, `trapped`, `priority_score`, `priority_label`, `assigned_unit` |
| `rescue_status_history` | Tracks rescue progress changes | `status`, `note`, `changed_by_id` |
| `hospitals` | Stores emergency medical capacity | `available_beds`, `icu_beds`, `emergency_capacity` |
| `hospital_capacity_logs` | Audits hospital capacity changes | `hospital_id`, `available_beds`, `created_at` |
| `shelters` | Stores relief camp capacity | `available_capacity`, `food_available`, `medical_support` |
| `shelter_capacity_logs` | Audits shelter capacity changes | `shelter_id`, `available_capacity` |
| `ambulances` | Stores ambulance dispatch readiness | `vehicle_number`, `status`, `hospital_id` |
| `ambulance_dispatches` | Links ambulances to rescue requests | `ambulance_id`, `rescue_request_id`, `status` |
| `resources` | Stores food, medicine, rescue supplies | `category`, `unit`, `available_quantity` |
| `resource_distribution` | Tracks relief supply movement | `resource_id`, `disaster_id`, `quantity`, `destination` |
| `volunteers` | Stores volunteer skills and availability | `skills`, `availability_status` |
| `volunteer_assignments` | Links volunteers to disaster tasks | `task`, `status`, `assigned_at` |
| `ai_assessments` | Stores AI outputs for auditability | `assessment_type`, `score`, `label`, `explanation` |
| `notifications` | Stores alerts for users or roles | `role`, `message`, `status` |
| `emergency_alerts` | Stores CAP-inspired authoritative public warnings | `identifier`, `audience`, `channels`, `urgency`, `severity`, `certainty`, `instruction` |
| `alert_acknowledgements` | Confirms last-mile receipt of warnings | `alert_id`, `user_id`, `response`, optional location |
| `disaster_news_updates` | Stores verified disaster-area news and live sources | `headline`, `source_name`, `stream_url`, `state`, `district`, `is_live` |
| `welfare_checks` | Tracks relative/next-of-kin tracing handled by call responders | `relative_name`, `last_known_location`, `requester_phone`, `status`, `responder_id` |
| `hospital_notifications` | Warns receiving hospitals of automatically routed patients | `hospital_id`, `rescue_request_id`, `expected_patients`, `priority`, `status` |
| `supply_requests` | Tracks food, water, medicine, and essential aid for isolated survivors | `category`, `people_count`, `urgency`, location, `assigned_unit`, `status` |
| `donation_campaigns` | Defines verified relief-funding campaigns | `goal_amount`, `currency`, `organizer`, `status` |
| `donations` | Audits pledges and confirmed/refunded contributions | `amount`, `reference`, `anonymous`, `status` |
| `location_pings` | Stores explicitly consented device locations and accuracy | `user_id`, optional rescue/supply case, coordinates, `consent_granted` |
| `response_dispatches` | Audits automatic proximity allocation | `rescue_request_id`, `responder_type`, `responder_name`, `distance_km`, `status` |
| `responder_units` | Registers professional rescue, fire, police, and medical field units | `unit_type`, `skills`, location, `availability_status` |
| `account_security` | Stores account lockout and temporary-password state | `failed_login_attempts`, `locked_until`, `password_changed_at`, `must_change_password` |
| `auth_sessions` | Stores hashed, revocable browser/API sessions | `token_hash`, `csrf_hash`, idle/absolute expiry, `mfa_state`, `revoked_at` |
