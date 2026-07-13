# Relational Schema

## Core Identity

- `users(id, name, email, phone, role, password_hash, is_active, created_at)`
- `role_profiles(id, user_id, organization_name, address, latitude, longitude, verification_status)`

## Disaster And Rescue

- `disasters(id, title, disaster_type, description, address, latitude, longitude, people_affected, severity_hint, status, image_url, reported_by_id, created_at, updated_at)`
- `rescue_requests(id, disaster_id, requester_id, victim_name, victim_age, people_count, condition_label, trapped, vulnerable_people, notes, latitude, longitude, status, priority_score, priority_label, assigned_unit, created_at, updated_at)`
- `rescue_status_history(id, rescue_request_id, status, note, changed_by_id, created_at)`

## Facilities And Resources

- `hospitals(id, name, address, latitude, longitude, total_beds, available_beds, icu_beds, emergency_capacity, contact_phone, updated_at)`
- `hospital_capacity_logs(id, hospital_id, available_beds, icu_beds, emergency_capacity, created_at)`
- `shelters(id, name, address, latitude, longitude, total_capacity, available_capacity, food_available, medical_support, contact_phone, updated_at)`
- `shelter_capacity_logs(id, shelter_id, available_capacity, created_at)`
- `ambulances(id, vehicle_number, driver_name, phone, latitude, longitude, status, hospital_id, updated_at)`
- `ambulance_dispatches(id, ambulance_id, rescue_request_id, status, dispatched_at)`
- `resources(id, name, category, unit, available_quantity, storage_location)`
- `resource_distribution(id, resource_id, disaster_id, quantity, destination, status, created_at)`

## Volunteers, AI, Notifications

- `volunteers(id, user_id, skills, availability_status, latitude, longitude)`
- `volunteer_assignments(id, volunteer_id, disaster_id, task, status, assigned_at)`
- `ai_assessments(id, entity_type, entity_id, assessment_type, score, label, explanation, created_at)`
- `notifications(id, user_id, role, message, status, created_at)`

## Normalization Notes

- User identity is separated from role-specific profile data.
- Disaster reports, rescue requests, facilities, resources, and assignments are separate entities.
- Audit/history tables preserve time-varying capacity and rescue status.
- Many operational events reference parent entities through foreign keys.
