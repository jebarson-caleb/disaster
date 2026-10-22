import React, { useState } from 'react';
import { Crosshair, Save } from 'lucide-react';
import StatusPill from './StatusPill.jsx';
import { ProgressBar } from './FormControls.jsx';
import { formatRelativeTime } from '../services/format.js';

const ambulanceStatuses = [
  { value: 'available', label: 'Available' },
  { value: 'dispatched', label: 'On a call' },
  { value: 'maintenance', label: 'Maintenance' },
  { value: 'offline', label: 'Off duty' },
];

function NumberField({ label, value, onChange, max }) {
  return (
    <label className="form-field compact-number-field">
      <span>{label}</span>
      <input className="form-control" type="number" min="0" max={max} step="1" required value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

export function HospitalCapacityEditor({ hospital, onSave }) {
  const [draft, setDraft] = useState({
    available_beds: String(hospital.available_beds),
    icu_beds: String(hospital.icu_beds),
    emergency_capacity: String(hospital.emergency_capacity),
  });
  const occupancy = hospital.total_beds ? Math.round(((hospital.total_beds - hospital.available_beds) / hospital.total_beds) * 100) : 0;

  function submit(event) {
    event.preventDefault();
    onSave(hospital.id, {
      available_beds: Number(draft.available_beds),
      icu_beds: Number(draft.icu_beds),
      emergency_capacity: Number(draft.emergency_capacity),
    });
  }

  return (
    <form className="facility-editor" onSubmit={submit} aria-label={`${hospital.name} capacity`}>
      <div className="facility-editor-heading">
        <div>
          <strong>{hospital.name}</strong>
          <span>{hospital.total_beds} licensed beds · {occupancy}% occupied · updated {formatRelativeTime(hospital.updated_at)}</span>
        </div>
        <StatusPill value={hospital.available_beds > 0 ? 'Accepting' : 'Full'} />
      </div>
      <ProgressBar value={occupancy} />
      <div className="facility-editor-fields">
        <NumberField label="Available beds" value={draft.available_beds} max={hospital.total_beds} onChange={(value) => setDraft({ ...draft, available_beds: value })} />
        <NumberField label="ICU beds free" value={draft.icu_beds} onChange={(value) => setDraft({ ...draft, icu_beds: value })} />
        <NumberField label="Emergency intake" value={draft.emergency_capacity} onChange={(value) => setDraft({ ...draft, emergency_capacity: value })} />
        <button className="primary-action" type="submit"><Save size={16} /> Save capacity</button>
      </div>
    </form>
  );
}

export function ShelterControls({ shelter, onMovement, onServices }) {
  const [count, setCount] = useState('10');
  const occupied = shelter.total_capacity - shelter.available_capacity;
  const occupancy = shelter.total_capacity ? Math.round((occupied / shelter.total_capacity) * 100) : 0;
  const people = Math.max(1, Number(count) || 1);
  return (
    <div className="facility-editor" aria-label={`${shelter.name} operations`}>
      <div className="facility-editor-heading">
        <div>
          <strong>{shelter.name}</strong>
          <span>{occupied}/{shelter.total_capacity} occupied · {shelter.available_capacity} places free · updated {formatRelativeTime(shelter.updated_at)}</span>
        </div>
        <StatusPill value={shelter.available_capacity > 0 ? 'Open' : 'Full'} />
      </div>
      <ProgressBar value={occupancy} />
      <div className="facility-editor-fields">
        <NumberField label="People" value={count} onChange={setCount} />
        <button type="button" className="compact-button" disabled={shelter.available_capacity < people} onClick={() => onMovement(shelter.id, -people)}>Record arrivals</button>
        <button type="button" className="compact-button secondary-button" disabled={occupied < people} onClick={() => onMovement(shelter.id, people)}>Record departures</button>
      </div>
      <div className="facility-service-toggles">
        <label className="check-row">
          <input type="checkbox" checked={shelter.food_available} onChange={(event) => onServices(shelter.id, { food_available: event.target.checked })} />
          Meals and drinking water available
        </label>
        <label className="check-row">
          <input type="checkbox" checked={shelter.medical_support} onChange={(event) => onServices(shelter.id, { medical_support: event.target.checked })} />
          Medical desk on site
        </label>
      </div>
    </div>
  );
}

export function AmbulanceControls({ ambulance, onStatus, onShareLocation }) {
  return (
    <div className="facility-editor" aria-label={`${ambulance.vehicle_number} status`}>
      <div className="facility-editor-heading">
        <div>
          <strong>{ambulance.vehicle_number}</strong>
          <span>{ambulance.driver_name} · location updated {formatRelativeTime(ambulance.updated_at)}</span>
        </div>
        <StatusPill value={ambulance.status} />
      </div>
      <div className="segmented-control" role="group" aria-label={`Set ${ambulance.vehicle_number} status`}>
        {ambulanceStatuses.map((option) => (
          <button
            type="button"
            key={option.value}
            className={ambulance.status === option.value ? 'active' : ''}
            aria-pressed={ambulance.status === option.value}
            onClick={() => ambulance.status !== option.value && onStatus(ambulance.id, option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
      {onShareLocation && (
        <button type="button" className="location-consent-button" onClick={() => onShareLocation(ambulance.id)}>
          <Crosshair size={16} /> Update vehicle location from this device
        </button>
      )}
    </div>
  );
}
