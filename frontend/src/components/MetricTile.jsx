import React from 'react';

export default function MetricTile({ icon: Icon, label, value, detail }) {
  return (
    <section className="metric-tile" aria-label={label}>
      <div className="metric-icon">{Icon ? <Icon size={20} /> : null}</div>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
        <span>{detail}</span>
      </div>
    </section>
  );
}
