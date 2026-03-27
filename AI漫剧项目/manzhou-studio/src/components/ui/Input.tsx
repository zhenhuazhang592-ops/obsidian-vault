import type { InputHTMLAttributes } from 'react';

interface InputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  multiline?: boolean;
  rows?: number;
  type?: InputHTMLAttributes<HTMLInputElement>['type'];
}

export function Input({
  value,
  onChange,
  placeholder,
  multiline = false,
  rows = 4,
  type = 'text',
}: InputProps) {
  const className = 'field-input';

  if (multiline) {
    return (
      <textarea
        className={className}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
      />
    );
  }

  return (
    <input
      className={className}
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
    />
  );
}
