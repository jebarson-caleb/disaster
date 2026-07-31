# Software Requirements Specification

## Objective

Provide a centralized platform for citizens, hospitals, shelters, NGOs, police, fire services, ambulances, volunteers, and administrators to coordinate disaster response.

## Functional Requirements

- Users can register and log in by role.
- Users can request a non-enumerating, expiring, single-use password-reset link when an approved email provider is configured; completing recovery revokes existing sessions.
- Administrator-issued credentials must be replaced on first login; password authentication then opens the server-authorized role workspace.
- Hospital, shelter, and ambulance accounts are assigned to their managed operational record and cannot mutate another facility.
- Citizens can report disasters with location, type, affected people, severity hint, and optional image URL.
- Citizens can create rescue requests and track status.
- AI estimates disaster damage and ranks rescue urgency.
- Admin, police, fire service, and NGO users can view and assign rescue requests.
- Hospitals can update available beds, ICU beds, and emergency capacity.
- Shelters can update relief camp capacity, food availability, and medical support.
- Ambulances can update dispatch status.
- NGOs/admins can plan resource distribution and volunteer assignment.
- Admin dashboard shows active disasters, pending rescues, available ambulances, hospital beds, shelter capacity, and charts.
- Administrators can review secret-safe integration readiness and the active fallback for every external provider.
- Authorized command roles can issue consistent multi-channel public warnings and view receipt counts.
- Citizens can confirm warning receipt and find the nearest available shelter or hospital from request coordinates.
- Citizen reports remain usable during connectivity loss and synchronize when service returns.
- Anyone can view an India-wide feed of active alerts and verified disaster-area news or live sources.
- Relatives can open consent-based welfare checks, call the national emergency hotline, and track responder updates.
- New rescue requests automatically reserve the nearest available volunteer and ambulance when appropriate.
- The nearest hospital with capacity receives an incoming-patient preparation notice and can acknowledge readiness.
- Isolated survivors can request food, water, medicine, and essential supplies using device coordinates.
- Device location is captured only after explicit browser permission and stored with accuracy and consent evidence.
- People can pledge to verified donation campaigns; administrators can confirm payment status and totals.

## Non-Functional Requirements

- Responsive interface for mobile and desktop.
- Role-based authorization on protected API endpoints.
- Indexed database tables for status, role, disaster type, priority, and location queries.
- AI decisions must remain available without internet access.
- Backend configuration must support MySQL through environment variables.
- Tests must cover auth, core emergency workflows, facility updates, and AI endpoints.
- Acceptance tests must cover onboarding and workspace access for every supported role.
- Acceptance tests must cover password-recovery privacy, expiry, single-use enforcement, delivery failure, and session revocation.
- Sensitive welfare, supply, and location records must be filtered by authenticated role and requester ownership.

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
- National alerts show multiple affected states and verified area updates.
- A critical rescue produces proximity dispatch records and an advance hospital notice.
- A citizen can submit and track both a family welfare check and an isolated-survivor supply case.
- Location sharing fails without explicit consent and succeeds with permission and coordinates.
- A donation pledge receives a unique reference and confirmed payments update campaign totals.
- A password-reset request does not reveal whether an account exists, and a valid reset link can be used only once.
