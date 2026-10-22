import React from 'react';
import { Ambulance, Building2, Home, Package, Play, ShieldAlert, Siren, UserRound, Users } from 'lucide-react';

const DEMO_ROLE_SUMMARIES = {
  Admin: 'Command dashboard, user access, setup and every department view',
  Citizen: 'Report emergencies, track rescue, warnings, family tracing and aid',
  Hospital: 'Bed and ICU capacity, incoming patient notices and surge readiness',
  Shelter: 'Occupancy, arrivals, camp services and supply coordination',
  Ambulance: 'Assigned calls, ETA, vehicle status and hospital handoff',
  NGO: 'Relief stock, distributions, volunteer assignment and needs queue',
  Volunteer: 'Duty status, safety checklist, assigned tasks and hazard reports',
  Police: 'Road closures, perimeters, public warnings and incident queue',
  'Fire Service': 'Rescue queue, equipment readiness, scene status and warnings',
};

const roleIcons = {
  Admin: ShieldAlert,
  Citizen: Home,
  Hospital: Building2,
  Shelter: Home,
  Ambulance,
  NGO: Package,
  Volunteer: Users,
  Police: ShieldAlert,
  'Fire Service': Siren,
};

export default function DemoLauncher({ onStart, starting }) {
  return (
    <section className="panel demo-launcher" aria-labelledby="demo-launcher-title">
      <div className="demo-launcher-heading">
        <div className="demo-launcher-icon"><Play size={20} aria-hidden="true" /></div>
        <div>
          <p className="eyebrow">No account needed</p>
          <h2 id="demo-launcher-title">Try the interactive demo</h2>
          <span>Pick a role to explore its workspace with fictional sample data. Everything stays in this browser tab; nothing is sent to live operations.</span>
        </div>
      </div>
      <div className="demo-role-grid">
        {Object.keys(DEMO_ROLE_SUMMARIES).map((role) => {
          const Icon = roleIcons[role] || UserRound;
          return (
            <button
              key={role}
              type="button"
              className="demo-role-button"
              disabled={Boolean(starting)}
              aria-label={`Demo as ${role}`}
              onClick={() => onStart(role)}
            >
              <Icon size={20} aria-hidden="true" />
              <span>
                <strong>{role}</strong>
                <small>{DEMO_ROLE_SUMMARIES[role]}</small>
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
