import { formatRelativeTime } from './format.js';

export const readinessTemplates = {
  'Fire Service': {
    title: 'Equipment and crew readiness',
    subject: 'Rescue tender',
    items: ['Breathing apparatus (SCBA) charged', 'Rescue boat and life jackets', 'Rope, harness and throw bags', 'Hydraulic extrication tools', 'Crew PPE complete'],
  },
  Police: {
    title: 'Perimeter and crowd-control readiness',
    subject: 'Control room shift',
    items: ['Barricades and diversion signage deployed', 'Public-address system working', 'Radio check with control room', 'Crowd-control team briefed', 'Evacuation route marshals posted'],
  },
  Volunteer: {
    title: 'Pre-deployment safety check',
    subject: 'Today’s shift',
    items: ['Safety briefing completed', 'PPE issued (gloves, boots, reflective vest)', 'Buddy assigned', 'Emergency contact shared with supervisor', 'Fit for duty and hydrated'],
  },
  Ambulance: {
    title: 'Vehicle readiness',
    subject: 'Ambulance',
    items: ['Oxygen cylinders full', 'Defibrillator charged', 'Stretcher and spine board', 'Trauma and burns kit stocked', 'Fuel above half tank'],
  },
  Hospital: {
    title: 'Emergency surge readiness',
    subject: 'Emergency department shift',
    items: ['Triage desk staffed', 'Surge ward opened', 'Blood bank stock checked', 'Generator fuel for 24 hours', 'Inter-facility transfer plan confirmed'],
  },
  Shelter: {
    title: 'Camp services check',
    subject: 'Relief camp',
    items: ['Drinking water available', 'Toilets and sanitation cleaned', 'Registration desk staffed', 'First-aid kit and medic on call', 'Safe space for women and children'],
  },
  NGO: {
    title: 'Relief logistics check',
    subject: 'Relief operation',
    items: ['Warehouse stock verified', 'Transport vehicles arranged', 'Volunteer roster confirmed', 'Beneficiary distribution list ready'],
  },
};

export function latestReadiness(checks = [], role) {
  return checks.find((item) => item.role === role) || null;
}

export function readinessSummary(check) {
  if (!check) return { value: 'Not checked', detail: 'Complete the readiness checklist for this shift' };
  const missing = Object.entries(check.items || {}).filter(([, done]) => !done).map(([label]) => label);
  return {
    value: `${check.ready_count}/${check.total_count} ready`,
    detail: missing.length ? `Missing: ${missing.join(', ')}` : `${check.subject} · all items confirmed ${formatRelativeTime(check.created_at)}`,
    missing,
  };
}

export function activeClosures(closures = []) {
  return closures.filter((item) => item.status !== 'reopened');
}
