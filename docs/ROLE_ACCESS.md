# Role Access and Onboarding

## Account lifecycle

Citizens and volunteers may self-register. Citizen accounts are active immediately. Volunteer accounts remain inactive until an administrator verifies the volunteer’s identity and affiliation.

Administrators provision every agency, facility, ambulance, NGO, and additional administrator account. The supplied password is temporary. A newly provisioned or reset account may access only identity, logout, and password-change endpoints until its user chooses a private replacement. Password authentication then opens the workspace authorized for that account role.

Hospital, shelter, and ambulance accounts must be linked to their managed record. An administrator may select an existing record or create the record in the same transaction as the account. Multiple authorized staff may be assigned to the same facility.

## Login and workspace matrix

| Role | How access starts | Sign-in | Primary live workspace | Server-enforced scope |
| --- | --- | --- | --- | --- |
| Citizen | Self-registration | Password | Safety, incident reporting, rescue tracking, family and aid | Own rescue, welfare, and supply cases |
| Volunteer | Self-registration plus administrator verification, or administrator provisioning | Password | Assigned tasks and response hub | Dispatch-assigned rescues; verified account only |
| Police | Administrator provisioning | Password | Public safety, incident queue, warnings | Command rescue queue and welfare/supply response |
| Fire Service | Administrator provisioning | Password | Fire rescue, incidents, warnings | Command rescue queue and welfare/supply response |
| Hospital | Administrator provisioning plus hospital assignment | Password | Capacity, incoming triage, hospital notices | Assigned hospital, its notices, and routed rescues |
| Shelter | Administrator provisioning plus shelter assignment | Password | Capacity and relief support | Assigned shelter and authorized supply coordination |
| Ambulance | Administrator provisioning plus ambulance assignment | Password | Assigned calls, vehicle status, hospital handoff | Assigned ambulance and its dispatch-linked rescues |
| NGO | Administrator provisioning | Password | Relief queue, distribution, volunteers, warnings | Command relief and rescue coordination |
| Admin | Bootstrap or administrator provisioning | Password | All workspaces, User Access, Operational Setup | Full authorized beta tenant |

## Administrator setup sequence

1. Replace the bootstrap password.
2. In **User Access**, create or verify the accounts the incident organization has authorized.
3. Bind hospital, shelter, and ambulance users to the correct operational record.
4. Deliver each temporary password through an approved secure channel; never send it in a public channel or commit it to source control.
5. When SMTP recovery is enabled, verify that **Forgot password** delivers an expiring, single-use link from the approved sender. Otherwise, use the administrator-assisted reset flow after an out-of-band identity check.
6. In **Operational Setup**, review **Integration readiness**, then add resource inventory, professional responder units, and any verified donation campaign. The readiness view reports active and fallback modes without exposing provider endpoints, accounts, or secrets.
7. Ask every user to replace the temporary password and review active sessions.
8. Deactivate departed or unverified users immediately. A deactivation or password reset revokes their active sessions.

## Acceptance evidence

The backend acceptance suite provisions all nine roles, exercises temporary-password replacement and secure self-service recovery, opens each role’s bootstrap workspace, verifies facility ownership, checks citizen case isolation, and exercises resource/responder/campaign setup. One isolated full-stack Chromium acceptance job opens every advertised view for every role, verifies the Shelter arrivals and Volunteer hazard-report shortcuts, and publishes an isolated warning through the command-role interface. A second production-mode Chromium job signs every role directly into its role-locked live workspace. The production smoke workflow separately verifies the public UI, liveness, database/configuration readiness, authentication and recovery boundaries, demo-mode isolation, and security headers.
