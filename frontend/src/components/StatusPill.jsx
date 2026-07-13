import React from 'react';

export default function StatusPill({ value }) {
  const normalized = String(value || 'low').toLowerCase();
  const tone =
    normalized.includes('critical') || normalized.includes('pending')
      ? 'danger'
      : normalized.includes('high') || normalized.includes('assigned') || normalized.includes('busy')
        ? 'warning'
        : normalized.includes('medium') || normalized.includes('route') || normalized.includes('monitoring')
          ? 'info'
          : 'success';
  return <span className={`status-pill status-pill-${tone}`}>{value}</span>;
}
