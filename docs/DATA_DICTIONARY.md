# Data Dictionary

| Table | Purpose | Important Attributes |
| --- | --- | --- |
| `users` | Stores login identity and role | `email`, `role`, `password_hash` |
| `role_profiles` | Stores organization/location profile | `organization_name`, `verification_status` |
| `disasters` | Stores reported disaster incidents | `disaster_type`, `people_affected`, `severity_hint`, `status` |
| `rescue_requests` | Stores victim rescue needs | `condition_label`, `trapped`, `priority_score`, `priority_label`, `assigned_unit` |
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
