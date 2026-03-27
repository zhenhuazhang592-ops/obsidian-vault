import type { ReactNode } from 'react';

interface StepPanelProps {
  title: string;
  icon: string;
  children: ReactNode;
}

export function StepPanel({ title, icon, children }: StepPanelProps) {
  return (
    <div className="step-panel">
      <h2 className="step-title">
        <span className="step-icon">{icon}</span>
        {title}
      </h2>
      {children}
    </div>
  );
}
