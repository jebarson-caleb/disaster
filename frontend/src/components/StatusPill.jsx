import React from 'react';

export default function StatusPill({ value }) {
  const normalized = String(value || 'low').toLowerCase();
  const tone =
    normalized.includes('critical') || normalized.includes('pending') || normalized.includes('maintenance') || normalized.includes('failed') || normalized.includes('unavailable') || normalized.includes('offline')
      ? 'danger'
      : normalized.includes('high') || normalized.includes('assigned') || normalized.includes('busy') || normalized.includes('dispatched') || normalized.includes('not configured')
        ? 'warning'
        : normalized.includes('medium') || normalized.includes('route') || normalized.includes('monitoring') || normalized.includes('triage') || normalized.includes('gis')
          ? 'info'
          : 'success';
  return <span className={`status-pill status-pill-${tone}`}>{value}</span>;
}
