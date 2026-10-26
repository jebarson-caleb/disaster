# ResQ Disaster Management System — Database & DBMS Test Report

**Document ID:** RESQ-DB-TEST-001  
**Target Commit:** `891bc60c1d8bebf86867d58d7f015de755c8b839`  
**ORM / DBMS Engine:** SQLAlchemy 2.1.6, Flask-SQLAlchemy 3.1.1, PostgreSQL (Production) / SQLite 3 (Testing)  

---

## 1. Schema Architecture & Models Verified

The ResQ database schema consists of 30 distinct entity models declared in [`backend/app/models.py`](file:///C:/Users/LUKSON/.gemini/antigravity/scratch/disaster/backend/app/models.py):

1. **Authentication & Identity:** `User`, `RoleProfile`, `AuthSession`, `AccountSecurity`, `PasswordResetToken`, `AuditEvent`, `MfaCredential`, `MfaChallenge`.
2. **Disaster Core & Operations:** `Disaster`, `RescueRequest`, `RescueStatusHistory`, `LocationPing`, `ResponseDispatch`, `ResponderUnit`.
3. **Emergency Facilities & Fleet:** `Hospital`, `HospitalCapacityLog`, `HospitalNotification`, `Shelter`, `ShelterCapacityLog`, `Ambulance`, `AmbulanceDispatch`.
4. **Logistics & Volunteer Operations:** `Resource`, `ResourceDistribution`, `SupplyRequest`, `Volunteer`, `VolunteerAssignment`.
5. **Field & Public Safety:** `RoadClosure`, `ReadinessCheck`, `EmergencyAlert`, `AlertAcknowledgement`, `DisasterNewsUpdate`, `WelfareCheck`, `DonationCampaign`, `Donation`, `AiAssessment`.

---

## 2. CRUD & Data Persistence Evaluation

### A. Incidents & Disasters (`/api/v1/disasters`)
- **Create:** Validated with required fields (`title`, `disaster_type`, `description`, `address`, `latitude`, `longitude`). Successfully flushes to database, persists record, and automatically generates an `AiAssessment` damage estimation entry.
- **Read:** Supports individual retrieval via `/api/v1/disasters/<id>` and filtered listing. Response contains parsed geographic coordinates, severity level, and creation timestamp.
- **Update:** Status transitions (`active` $\rightarrow$ `monitoring` $\rightarrow$ `contained` $\rightarrow$ `closed`) are enforced.
- **Persistence Verification:** Verified via `test_sql_injection_payload_in_disaster_title_is_safely_escaped` — created record was fetched independently from the database session and matched persisted values.

### B. Road Closures (`/api/v1/road-closures`)
- **Create:** Published by Police or Fire Service with location landmark, reason, and coordinates.
- **Read:** Visible publicly across all roles, including anonymous feeds and Citizen safety views.
- **Update:** Status transitions between `closed`, `restricted`, and `reopened` update timestamps and auditing records.

### C. Shelter & Hospital Surge Capacity
- **Hospital Intake:** Capacity logs (`HospitalCapacityLog`) record historical available beds and ICU bed count updates. Verified that negative numbers are blocked at the validation layer.
- **Shelter Services:** Tracks total capacity, current occupancy, and camp service availability flags (`food`, `water`, `medical`).

### D. Volunteer Availability & Tasks
- **Duty Toggle:** Volunteers can toggle `is_available` between True and False via `PATCH /api/v1/volunteers/me/availability`.
- **Task Progression:** Assignments transition from `assigned` $\rightarrow$ `en route` $\rightarrow$ `rescued` / `completed`.

---

## 3. Data Integrity, Constraints, and Transactions

### A. Coordinate Bounds Validation
- **Requirement:** Latitude must be in $[-90.0, 90.0]$, Longitude must be in $[-180.0, 180.0]$.
- **Execution Evidence:** Submitting `latitude=95.5` or `longitude=185.0` raises `ValueError`, resulting in a client-safe `HTTP 400 Bad Request` with message: `"latitude is outside valid bounds"`.

### B. Non-Negative Constraints
- **Requirement:** Capacities and counts must be whole numbers $\ge 0$.
- **Execution Evidence:** Tested in `test_additional_gap_checks.py`. Passing `-10` capacity or `-5` ICU beds fails validation before hitting the SQL engine.

### C. Referential Integrity & Foreign Keys
- All relational child tables (`RescueStatusHistory`, `HospitalCapacityLog`, `VolunteerAssignment`, `LocationPing`) enforce strict foreign keys to parent entities (`user_id`, `rescue_id`, `hospital_id`).
- Foreign key constraints prevent orphaned operational records.

### D. Transactional Atomicity & Rollback
- Verified in `test_api.py::test_resource_distribution_and_volunteer_assignment_are_transactional`:
  - When a multi-step operation (e.g. allocating emergency supplies while assigning responder units) experiences an intentional error on step 2, step 1 is rolled back completely.
  - No partial or corrupted state remains in the database.

---

## 4. Migration History & Schema Alignment

Eight sequential Alembic migrations are tracked and verified:
1. `20260721_01`: Initial beta schema baseline.
2. `20260721_02`: Authentication security tables (`AuthSession`, `AccountSecurity`, `AuditEvent`).
3. `20260721_03`: Multi-factor authentication credentials and challenge tracking.
4. `20260727_04`: Temporary password lifecycle and operational asset binding.
5. `20260729_05`: Expiring password recovery tokens.
6. `20260729_06`: Signed outbound alert delivery tracking.
7. `20260905_07`: Removal of persistent account lockout state (mitigating lock-out DoS).
8. `20261022_08`: Department field operations (road closures and readiness checklists).

**Verification Result:**  
Running `flask --app run:app db check` against a freshly upgraded SQLite database returned `No new upgrade operations detected.` This confirms that the Python model declarations in `models.py` and the migration scripts in `migrations/versions/` are in 100% agreement.
