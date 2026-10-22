import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

export function PanelTitle({ eyebrow, title, children }) {
  return (
    <div className="panel-header">
      <div>
        <p>{eyebrow}</p>
        <h2>{title}</h2>
      </div>
      {children}
    </div>
  );
}

export function EmptyState({ title, detail }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      <span>{detail}</span>
    </div>
  );
}

export function ProgressBar({ value }) {
  const safeValue = Number.isFinite(Number(value)) ? Number(value) : 0;
  return (
    <div className="progress-track" aria-label={`${Math.round(safeValue)}%`}>
      <span style={{ width: `${Math.max(3, Math.min(100, safeValue))}%` }} />
    </div>
  );
}

export function Input({ label, name, value, onChange, type = 'text', required = false, step, min, max, minLength, maxLength, autoComplete, inputMode, placeholder }) {
  const [showPassword, setShowPassword] = useState(false);
  const isPassword = type === 'password';
  const inputType = isPassword && showPassword ? 'text' : type;

  return (
    <label className="form-field">
      <span>{label}</span>
      <div className="input-with-toggle">
        <input
          className="form-control"
          name={name}
          type={inputType}
          step={step}
          min={min}
          max={max}
          minLength={minLength}
          maxLength={maxLength}
          autoComplete={autoComplete}
          inputMode={inputMode}
          placeholder={placeholder}
          value={value}
          required={required}
          onChange={(event) => onChange(event.target.value)}
        />
        {isPassword && (
          <button
            type="button"
            className="password-toggle"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            aria-pressed={showPassword}
            title={showPassword ? 'Hide password' : 'Show password'}
            onClick={() => setShowPassword((visible) => !visible)}
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </div>
    </label>
  );
}

export function Textarea({ label, value, onChange, required = false, maxLength }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <textarea className="form-control" rows="4" value={value} required={required} maxLength={maxLength} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

export function Select({ label, value, options, onChange }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <select className="form-select" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => {
          const normalized = typeof option === 'string' ? { label: option, value: option } : option;
          return (
            <option key={normalized.value} value={normalized.value}>
              {normalized.label}
            </option>
          );
        })}
      </select>
    </label>
  );
}
