# Software Requirements Specification

## Objective

Provide a centralized platform for citizens, hospitals, shelters, NGOs, police, fire services, ambulances, volunteers, and administrators to coordinate disaster response.

## Functional Requirements

- Users can register and log in by role.
- Citizens can report disasters with location, type, affected people, severity hint, and optional image URL.
- Citizens can create rescue requests and track status.
- AI estimates disaster damage and ranks rescue urgency.
- Admin, police, fire service, and NGO users can view and assign rescue requests.
- Hospitals can update available beds, ICU beds, and emergency capacity.
- Shelters can update relief camp capacity, food availability, and medical support.
- Ambulances can update dispatch status.
- NGOs/admins can plan resource distribution and volunteer assignment.
- Admin dashboard shows active disasters, pending rescues, available ambulances, hospital beds, shelter capacity, and charts.
- Authorized command roles can issue consistent multi-channel public warnings and view receipt counts.
- Citizens can confirm warning receipt and find the nearest available shelter or hospital from request coordinates.
- Citizen reports remain usable during connectivity loss and synchronize when service returns.

## Non-Functional Requirements

- Responsive interface for mobile and desktop.
- Role-based authorization on protected API endpoints.
- Indexed database tables for status, role, disaster type, priority, and location queries.
- AI decisions must remain available without internet access.
- Backend configuration must support MySQL through environment variables.
- Tests must cover auth, core emergency workflows, facility updates, and AI endpoints.

## Actors

- Citizen
- Admin
- Police
- Fire Service
- Hospital
- Shelter
- Ambulance
- NGO
- Volunteer

## Acceptance Criteria

- A citizen can report a flood and create a rescue request.
- AI marks a trapped vulnerable victim as critical priority.
- Admin can assign a rescue unit and update status history.
- Hospital and shelter capacity changes are visible to operations users.
- Dashboard displays maps, charts, and live operational counts.
