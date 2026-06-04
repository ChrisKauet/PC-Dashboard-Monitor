"use client";

interface BarCardProps {
  title: string;
  used: number | null;
  total: number | null;
  unit: string;
  color: string;
  percent: number | null;
  icon?: string;
  subtitle?: string;
}

export default function BarCard({ title, used, total, unit, color, percent, icon, subtitle }: BarCardProps) {
  const safe = percent ?? 0;

  return (
    <div
      className="card"
      style={{ display: "flex", flexDirection: "column", gap: 12, position: "relative", overflow: "hidden" }}
    >
      {/* Ambient glow */}
      <div style={{
        position: "absolute", bottom: -20, left: -20,
        width: 100, height: 100, borderRadius: "50%",
        background: `${color}0e`, filter: "blur(28px)", pointerEvents: "none",
      }} />

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{
            fontSize: 11, fontWeight: 600, letterSpacing: "0.09em",
            textTransform: "uppercase", color: "var(--text-muted)",
            fontFamily: "'Exo 2', sans-serif",
          }}>
            {icon && <span style={{ marginRight: 5 }}>{icon}</span>}
            {title}
          </div>
          {subtitle && <div style={{ fontSize: 10, color: "var(--text-dim)", marginTop: 2 }}>{subtitle}</div>}
        </div>

        {/* % pill */}
        <div style={{
          padding: "3px 10px", borderRadius: 999,
          background: `${color}18`, border: `1px solid ${color}30`,
        }}>
          <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 13, color }}>
            {percent !== null ? `${Math.round(safe)}%` : "N/A"}
          </span>
        </div>
      </div>

      {/* Values */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <span style={{
          fontFamily: "'Share Tech Mono', monospace", fontSize: 30, color,
          textShadow: `0 0 14px ${color}55`,
        }}>
          {used !== null ? used.toFixed(used < 100 ? 1 : 0) : "—"}
        </span>
        <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 13, color: "var(--text-muted)" }}>
          / {total !== null ? total.toFixed(total < 100 ? 1 : 0) : "—"} {unit}
        </span>
      </div>

      {/* Progress bar */}
      <div style={{
        width: "100%", height: 5, background: "var(--border)",
        borderRadius: 999, overflow: "hidden",
      }}>
        <div style={{
          height: "100%", width: `${safe}%`,
          background: `linear-gradient(90deg, ${color}aa, ${color})`,
          borderRadius: 999,
          transition: "width 0.7s cubic-bezier(0.4,0,0.2,1)",
          boxShadow: `0 0 8px ${color}60`,
        }} />
      </div>
    </div>
  );
}
