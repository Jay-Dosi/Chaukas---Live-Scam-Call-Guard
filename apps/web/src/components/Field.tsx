import { forwardRef } from 'react';

export interface FieldProps {
  label: string;
  help?: string;
  error?: string;
  children: React.ReactNode;
  className?: string;
}

export function Field({ label, help, error, children, className = '' }: FieldProps) {
  return (
    <div className={`field ${className}`}>
      <label className="field__label">{label}</label>
      {children}
      {(error || help) && (
        <p className={`field__help ${error ? 'field__error' : ''}`} style={{color: error ? 'var(--danger)' : 'var(--ink-3)'}}>
          {error || help}
        </p>
      )}
    </div>
  );
}

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  help?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, help, error, className = '', id, ...rest }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');
    return (
      <Field label={label} help={help} error={error}>
        <input
          ref={ref}
          id={inputId}
          className={`form__input ${className}`}
          aria-describedby={help ? `${inputId}-help` : error ? `${inputId}-error` : undefined}
          aria-invalid={!!error}
          {...rest}
        />
      </Field>
    );
  }
);
Input.displayName = 'Input';

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  help?: string;
  error?: string;
  options: Array<{ value: string; label: string }>;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, help, error, options, className = '', id, ...rest }, ref) => {
    const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');
    return (
      <Field label={label} help={help} error={error}>
        <select
          ref={ref}
          id={selectId}
          className={`form__select ${className}`}
          aria-describedby={help ? `${selectId}-help` : error ? `${selectId}-error` : undefined}
          aria-invalid={!!error}
          {...rest}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </Field>
    );
  }
);
Select.displayName = 'Select';