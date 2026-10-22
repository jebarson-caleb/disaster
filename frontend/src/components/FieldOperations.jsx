import React, { useState } from 'react';
import { CircleCheck, ClipboardList, Construction, Crosshair, Route, UserRound } from 'lucide-react';
import StatusPill from './StatusPill.jsx';
import { EmptyState, Input, PanelTitle, Select, Textarea } from './FormControls.jsx';
import { activeClosures, latestReadiness, readinessSummary, readinessTemplates } from '../services/fieldOperations.js';
import { formatRelativeTime } from '../services/format.js';

export function ReadinessChecklistPanel({ role, latest, defaultSubject, onSubmit }) {
  const template = readinessTemplates[role];
  const [subject, setSubject] = useState(defaultSubject || template?.subject || '');
  const [checked, setChecked] = useState(() => Object.fromEntries((template?.items || []).map((label) => [label, Boolean(latest?.items?.[label])])));
  const [notes, setNotes] = useState('');
  if (!template) return null;
  const summary = readinessSummary(latest);

  async function submit(event) {
    event.preventDefault();
    const saved = await onSubmit({ subject, items: checked, notes });
    if (saved) setNotes('');
  }

  return (
    <section className="panel readiness-checklist-panel">
      <PanelTitle eyebrow="Shift readiness" title={template.title}>
        <StatusPill value={summary.value} />
      </PanelTitle>
      <p className="muted-copy">
        {latest ? `Last recorded ${formatRelativeTime(latest.created_at)} for ${latest.subject}.` : 'No checklist has been recorded for this team yet.'}
      </p>
      <form className="readiness-form" onSubmit={submit}>
        <Input label="Team, vehicle or facility" value={subject} onChange={setSubject} required maxLength={160} />
        <fieldset className="readiness-items">
          <legend>Checklist</legend>
          {template.items.map((label) => (
            <label key={label} className="check-row">
              <input type="checkbox" checked={Boolean(checked[label])} onChange={(event) => setChecked((current) => ({ ...current, [label]: event.target.checked }))} />
              {label}
            </label>
          ))}
        </fieldset>
        <Textarea label="Notes or shortages (optional)" value={notes} onChange={setNotes} maxLength={500} />
        <button className="primary-action" type="submit"><ClipboardList size={17} /> Record readiness</button>
      </form>
    </section>
  );
}

export function ReadinessOverviewPanel({ checks = [] }) {
  const latestByRole = Object.keys(readinessTemplates).map((role) => ({ role, check: latestReadiness(checks, role) }));
  return (
    <section className="panel">
      <PanelTitle eyebrow="Department readiness" title="Latest checklists by department" />
      <div className="role-task-list">
        {latestByRole.map(({ role, check }) => {
          const summary = readinessSummary(check);
          return (
            <div className="role-task" key={role}>
              <StatusPill value={check ? (summary.missing.length ? 'Gaps' : 'Ready') : 'Not checked'} />
              <div>
                <strong>{role} · {summary.value}</strong>
                <span>{check ? `${check.subject} · ${formatRelativeTime(check.created_at)}${summary.missing.length ? ` · ${summary.detail}` : ''}` : 'No checklist recorded yet'}</span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

const emptyClosureDraft = { road_name: '', location: '', latitude: '', longitude: '', status: 'closed', reason: '', diversion: '', disaster_id: '' };

export function RoadClosurePanel({ closures = [], disasters = [], canEdit = false, onCreate, onUpdate, title = 'Road closures and diversions' }) {
  const [draft, setDraft] = useState(emptyClosureDraft);
  const [showForm, setShowForm] = useState(false);
  const visible = canEdit ? closures : activeClosures(closures);

  async function submit(event) {
    event.preventDefault();
    const saved = await onCreate(draft);
    if (saved) {
      setDraft(emptyClosureDraft);
      setShowForm(false);
    }
  }

  function useDeviceLocation() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(({ coords }) => {
      setDraft((current) => ({ ...current, latitude: coords.latitude.toFixed(6), longitude: coords.longitude.toFixed(6) }));
    });
  }

  return (
    <section className="panel road-closure-panel">
      <PanelTitle eyebrow={canEdit ? 'Road access control' : 'Roads to avoid'} title={title}>
        <StatusPill value={`${activeClosures(closures).length} active`} />
      </PanelTitle>
      <div className="hub-feed">
        {visible.map((item) => (
          <article className="hub-feed-item" key={item.id}>
            <div className="hub-item-heading">
              <div>
                <strong><Construction size={15} aria-hidden="true" /> {item.road_name}</strong>
                <span>{item.location} · updated {formatRelativeTime(item.updated_at || item.created_at)}</span>
              </div>
              <StatusPill value={item.status} />
            </div>
            <p>{item.reason}</p>
            {item.diversion && <small><Route size={13} aria-hidden="true" /> <strong>Diversion:</strong> {item.diversion}</small>}
            {canEdit && (
              <div className="inline-actions">
                {item.status !== 'restricted' && item.status !== 'reopened' && (
                  <button type="button" className="compact-button secondary-button" onClick={() => onUpdate(item, 'restricted')}>Emergency vehicles only</button>
                )}
                {item.status !== 'reopened' ? (
                  <button type="button" className="compact-button" onClick={() => onUpdate(item, 'reopened')}>Reopen road</button>
                ) : (
                  <button type="button" className="compact-button secondary-button" onClick={() => onUpdate(item, 'closed')}>Close again</button>
                )}
              </div>
            )}
          </article>
        ))}
        {!visible.length && <EmptyState title="No road closures" detail={canEdit ? 'Record a closure or diversion when a route becomes unsafe.' : 'No closures have been reported by police or fire control.'} />}
      </div>
      {canEdit && !showForm && (
        <button type="button" className="primary-action" onClick={() => setShowForm(true)}><Construction size={17} /> Report a closure</button>
      )}
      {canEdit && showForm && (
        <form className="road-closure-form" onSubmit={submit}>
          <Input label="Road or junction" value={draft.road_name} onChange={(value) => setDraft({ ...draft, road_name: value })} required maxLength={160} />
          <Input label="Location / landmark" value={draft.location} onChange={(value) => setDraft({ ...draft, location: value })} required maxLength={255} />
          <div className="form-row form-row-2">
            <Input label="Latitude" type="number" step="any" value={draft.latitude} onChange={(value) => setDraft({ ...draft, latitude: value })} required />
            <Input label="Longitude" type="number" step="any" value={draft.longitude} onChange={(value) => setDraft({ ...draft, longitude: value })} required />
          </div>
          <button className="location-consent-button" type="button" onClick={useDeviceLocation}><Crosshair size={17} /> Use my current location</button>
          <div className="form-row form-row-2">
            <Select label="Access" value={draft.status} options={[{ label: 'Closed to all traffic', value: 'closed' }, { label: 'Emergency vehicles only', value: 'restricted' }]} onChange={(value) => setDraft({ ...draft, status: value })} />
            <Select label="Related incident" value={draft.disaster_id} options={[{ label: 'Not linked', value: '' }, ...disasters.map((item) => ({ label: item.title, value: String(item.id) }))]} onChange={(value) => setDraft({ ...draft, disaster_id: value })} />
          </div>
          <Textarea label="Reason" value={draft.reason} onChange={(value) => setDraft({ ...draft, reason: value })} required maxLength={500} />
          <Input label="Diversion (optional)" value={draft.diversion} onChange={(value) => setDraft({ ...draft, diversion: value })} maxLength={255} />
          <div className="inline-actions">
            <button className="primary-action" type="submit"><Construction size={17} /> Publish closure</button>
            <button className="compact-button secondary-button" type="button" onClick={() => setShowForm(false)}>Cancel</button>
          </div>
        </form>
      )}
    </section>
  );
}

const incidentStatuses = ['active', 'monitoring', 'contained', 'closed'];

export function IncidentStatusPanel({ disasters = [], onUpdate }) {
  return (
    <section className="panel">
      <PanelTitle eyebrow="Scene status" title="Incident status board" />
      <div className="facility-list">
        {disasters.slice(0, 8).map((item) => (
          <div className="facility-item incident-status-row" key={item.id}>
            <div>
              <strong>{item.title}</strong>
              <span>{item.address} · {Number(item.people_affected || 0).toLocaleString('en-IN')} affected</span>
            </div>
            <label className="visually-labelled-select">
              <span className="sr-only">Status for {item.title}</span>
              <select className="form-select" value={item.status} onChange={(event) => onUpdate(item, event.target.value)}>
                {incidentStatuses.map((status) => <option key={status} value={status}>{status}</option>)}
              </select>
            </label>
          </div>
        ))}
        {!disasters.length && <EmptyState title="No incidents" detail="Incidents reported by the field appear here for status control." />}
      </div>
    </section>
  );
}

export function VolunteerDutyPanel({ volunteer, disasters = [], onAvailability, onAssignment }) {
  if (!volunteer) {
    return (
      <section className="panel">
        <PanelTitle eyebrow="Duty status" title="Volunteer profile" />
        <EmptyState title="No volunteer profile" detail="Ask an administrator to link a verified volunteer profile to this account." />
      </section>
    );
  }
  const status = volunteer.availability_status;
  const locked = ['assigned', 'pending verification'].includes(status);
  const openAssignments = (volunteer.assignments || []).filter((item) => ['assigned', 'in progress'].includes(item.status));
  const titleFor = (id) => disasters.find((item) => Number(item.id) === Number(id))?.title || `Incident #${id}`;
  return (
    <section className="panel volunteer-duty-panel">
      <PanelTitle eyebrow="Duty status" title="My availability and assignments">
        <StatusPill value={status} />
      </PanelTitle>
      <p className="muted-copy">
        {locked
          ? status === 'assigned'
            ? 'Complete your open assignments to return to the available pool.'
            : 'An administrator must verify your profile before you can be dispatched.'
          : 'Command and NGO coordinators dispatch only volunteers marked available.'}
      </p>
      <div className="inline-actions">
        <button type="button" className={`compact-button${status === 'available' ? '' : ' secondary-button'}`} disabled={locked || status === 'available'} onClick={() => onAvailability('available')}>
          <UserRound size={15} /> Available for tasks
        </button>
        <button type="button" className={`compact-button${status === 'off duty' ? '' : ' secondary-button'}`} disabled={locked || status === 'off duty'} onClick={() => onAvailability('off duty')}>
          Off duty
        </button>
      </div>
      <div className="hub-feed">
        {(volunteer.assignments || []).slice(0, 6).map((item) => (
          <article className="hub-feed-item" key={item.id}>
            <div className="hub-item-heading">
              <div><strong>{item.task}</strong><span>{titleFor(item.disaster_id)} · {formatRelativeTime(item.assigned_at)}</span></div>
              <StatusPill value={item.status} />
            </div>
            {['assigned', 'in progress'].includes(item.status) && (
              <div className="inline-actions">
                {item.status === 'assigned' && <button type="button" className="compact-button secondary-button" onClick={() => onAssignment(item, 'in progress')}>Start task</button>}
                <button type="button" className="compact-button" onClick={() => onAssignment(item, 'completed')}><CircleCheck size={15} /> Mark complete</button>
              </div>
            )}
          </article>
        ))}
        {!openAssignments.length && !(volunteer.assignments || []).length && <EmptyState title="No assignments yet" detail="New tasks appear here when a coordinator assigns you." />}
      </div>
    </section>
  );
}
