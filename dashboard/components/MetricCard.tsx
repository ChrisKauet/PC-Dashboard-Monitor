"use client";

import { IconCpu, IconDatabase, IconDeviceDesktop, IconServer } from "@tabler/icons-react";

interface MetricCardProps {
  label: string;
  icon: React.ReactNode;
  value: string | number | null;
  unit: string;
  subtitle: string;
  percent: number | null;
  colorClass: "cpu" | "ram" | "gpu" | "disk";
}

export default function MetricCard({ label, icon, value, unit, subtitle, percent, colorClass }: MetricCardProps) {
  const displayValue = value !== null && value !== undefined ? value : "—";
  const displayPercent = percent !== null ? percent : 0;

  return (
    <div className={`metric-card mc-${colorClass}`}>
      <div className="metric-label">
        {icon} {label}
      </div>
      <div className="metric-value-row">
        <span className="metric-value">{displayValue}</span>
        <span className="metric-unit">{unit}</span>
      </div>
      <div className="metric-sub">{subtitle}</div>
      <div className="bar-track">
        <div className={`bar-fill bf-${colorClass}`} style={{ width: `${displayPercent}%` }} />
      </div>
    </div>
  );
}
