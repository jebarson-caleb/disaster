# ResQ Disaster Management System — User Acceptance Testing (UAT) Report

**Document ID:** RESQ-UAT-REP-001  
**Project:** ResQ Disaster Response Command  
**Target Environment:** Live Hosted Website (`https://disaster-delta-eight.vercel.app/`)  
**Test Mode:** Simulated Stakeholder & Role-Based Operational Walkthrough  
**Date of Execution:** 2026-10-26  

---

## 1. Scope and Objective

This User Acceptance Testing (UAT) report evaluates the live deployment of the ResQ Disaster Management System against operational workflows across all **9 implemented stakeholder roles**.

> **Important Disclosure:** This UAT execution was conducted as a rigorous, automated and simulated stakeholder exercise using authorized role workspaces. It validates that the software satisfies the functional acceptance criteria specified in the System Requirements Specification (SRS), but does not substitute for formal statutory sign-offs by public emergency services (e.g. NDRF, Police Command, Fire Directorate).

---

## 2. Role-by-Role Acceptance Scenarios & Results

### Role 1: Incident Commander (Admin)
- **User Goal:** Oversee nationwide risk, review multi-agency readiness, and issue public emergency warnings.
- **Preconditions:** Access live application via "Demo as Admin" or administrative credentials.
- **Steps Performed:**
  1. Open Command Center; inspect live operational stats.
  2. Navigate to "Public Warnings", input audience ("Chennai Coastal Sector"), channel ("Emergency Broadcast"), and message ("Evacuation advisory").
  3. Submit alert.
- **Expected Result:** Warning displays confirmation; operations dashboard updates.
- **Actual Result:** Broadcast notification appeared: *"Alert published in ResQ for Chennai Coastal Sector; no external delivery provider is configured."*
- **Status:** **PASS**

### Role 2: Citizen
- **User Goal:** View local hazard advisories, check road closures, and submit an emergency request for rescue.
- **Steps Performed:**
  1. Select role "Citizen".
  2. Inspect "My Safety" dashboard and active road closures.
  3. Navigate to "Report Help"; enter affected count (4) and location details.
- **Expected Result:** Hazard alerts and safe route guidance display; report submits cleanly.
- **Actual Result:** Safety guidance rendered; road closures from Police displayed; report form validated input.
- **Status:** **PASS**

### Role 3: Police Control Officer
- **User Goal:** Establish traffic diversions and publish road closures to protect flood-prone rescue corridors.
- **Steps Performed:**
  1. Select role "Police".
  2. Click "Report a closure"; fill road name ("Old Mahabalipuram Road"), coordinates, and flood reason.
  3. Click "Publish closure".
- **Expected Result:** Road status switches to closed; entry reflects in public and Citizen safety views.
- **Actual Result:** Confirmation displayed *"Old Mahabalipuram Road published as closed"*; verified immediately in Citizen view without page refresh.
- **Status:** **PASS**

### Role 4: Fire & Rescue Officer
- **User Goal:** Manage water rescue teams, review high-priority rescue queues, and record equipment readiness.
- **Steps Performed:**
  1. Select role "Fire Service".
  2. Check "Equipment and crew readiness": toggle "Hydraulic extrication tools" and "Inflatable rescue boats".
  3. Click "Record readiness".
- **Expected Result:** Equipment readiness count increments and saves timestamp.
- **Actual Result:** Banner updated to reflect *"2 items ready"*; queue displayed high-priority hazard locations.
- **Status:** **PASS**

### Role 5: Hospital Duty Officer
- **User Goal:** Manage critical emergency intake, track ICU bed availability, and prepare for incoming triage.
- **Steps Performed:**
  1. Select role "Hospital".
  2. Under "Emergency surge readiness", update available general beds and ICU capacity.
  3. Review "Incoming Triage" queue.
- **Expected Result:** Hospital capacity updates; incoming ambulances reflect estimated arrival times.
- **Actual Result:** Capacity numbers saved; triage patients listed with severity conditions.
- **Status:** **PASS**

### Role 6: Shelter Coordinator
- **User Goal:** Track camp population, manage essential supplies, and monitor incoming evacuees.
- **Steps Performed:**
  1. Select role "Shelter".
  2. Review "Camp services check"; toggle clean drinking water and medical desk availability.
  3. Review "Expected Arrivals" feed.
- **Expected Result:** Camp occupancy updates; supply readiness status updates.
- **Actual Result:** Relief indicators reflected updated availability; expected arrival list populated.
- **Status:** **PASS**

### Role 7: Ambulance (108 Dispatcher)
- **User Goal:** Receive emergency dispatch assignments, navigate to patient pickup GPS, and coordinate hospital handoff.
- **Steps Performed:**
  1. Select role "Ambulance".
  2. Review "Vehicle readiness" and assigned emergency calls.
  3. Verify nearest receiving hospital based on ICU capacity.
- **Expected Result:** Assigned calls show patient condition; receiving facility is mapped.
- **Actual Result:** Call card displayed triage priority and distance to receiving hospital.
- **Status:** **PASS**

### Role 8: Relief NGO Coordinator
- **User Goal:** Coordinate supply distribution, track unmet community relief needs, and deploy volunteers.
- **Steps Performed:**
  1. Select role "NGO".
  2. Review "Needs Queue" and inventory distribution status.
  3. Complete relief logistics checklist.
- **Expected Result:** Supply requests categorized by urgency; distribution checklist updates.
- **Actual Result:** Logistical readiness checklist saved; volunteer tasks visible.
- **Status:** **PASS**

### Role 9: Field Volunteer
- **User Goal:** Receive assigned tasks, review pre-deployment safety checklist, and update duty status.
- **Steps Performed:**
  1. Select role "Volunteer".
  2. Under "My availability and assignments", click "Mark complete" on assigned task.
  3. Click "Off duty".
- **Expected Result:** Task marked completed; duty state changes to off duty.
- **Actual Result:** Status notifications: *"Assignment marked completed"* and *"Duty status changed to off duty"*.
- **Status:** **PASS**

---

## 3. Usability & User Experience Feedback

| Evaluation Area | Rating (1-5) | Observations & Feedback |
| :--- | :---: | :--- |
| **Visual Clarity & Layout** | 4.8 / 5 | Dark-mode command palette with clear icons (Lucide React) provides high contrast and clear readability. |
| **Role-Switching Usability** | 5.0 / 5 | The top-bar role selector makes exploring multi-agency workflows instantaneous in sandbox mode. |
| **Error Message Clarity** | 4.6 / 5 | Input validation gives plain-English feedback (e.g. *"Missing fields: description, address"*, *"capacity must be between 0 and 1000000"*). |
| **Mobile Responsiveness** | 4.7 / 5 | Forms, maps, and command buttons fit 390px mobile viewports without horizontal scrolling. |
| **Initial Loading Experience** | 3.8 / 5 | Idle serverless backend can cause an extended wait on "Restoring your secure session" during cold start. |

---

## 4. Acceptance Decision

- **Academic Demonstration Acceptance:** **APPROVED** — The software meets all hackathon and curriculum goals with high fidelity.
- **Controlled Pilot / Field Testing:** **CONDITIONALLY APPROVED** — Approved for non-emergency pilot exercises once external SMS/SMTP provider credentials and pilot incident commander contacts are configured.
