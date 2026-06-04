"use client";

interface GaugeCardProps {
  title: string;
  value: number | null;
  color: string;
  unit?: string;
  temp?: number | null;
  subtitle?: string;
  icon?: string;
}

function getTempColor(t: number | null): string {
  if (t === null) return "var(--text-dim)";
  if (t <= 60) return "#22d3a5";
  if (t <= 80) return "#f59e0b";
  return "#ef4444";
}

export default function GaugeCard({ title, value, color, unit = "%", temp, subtitle, icon }: GaugeCardProps) {
  const safe = value ?? 0;
  const radius = 50;
  const circ = 2 * Math.PI * radius;
  const dash = (safe / 100) * circ;
  const tempColor = getTempColor(temp ?? null);

  return (
    <div
      className="card"
      style={{ display: "flex", flexDirection: "column", gap: 14, position: "relative", overflow: "hidden" }}
    >
      {/* Ambient glow */}
      <div style={{
        position: "absolute", top: -40, right: -40,
        width: 140, height: 140, borderRadius: "50%",
        background: `${color}12`, filter: "blur(35px)", pointerEvents: "none",
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
          {subtitle && (
            <div style={{ fontSize: 10, color: "var(--text-dim)", marginTop: 2 }}>{subtitle}</div>
          )}
        </div>

        {/* Temp badge */}
        {temp !== undefined && temp !== null && (
          <div style={{
            display: "flex", alignItems: "center", gap: 4,
            padding: "3px 10px", borderRadius: 999,
            background: `${tempColor}18`, border: `1px solid ${tempColor}35`,
          }}>
            <span style={{ fontSize: 12 }}>🌡️</span>
            <span style={{
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: 12, fontWeight: 600, color: tempColor,
            }}>
              {temp}°C
            </span>
          </div>
        )}
      </div>

      {/* SVG Gauge */}
      <div style={{ display: "flex", justifyContent: "center" }}>
        <div style={{ position: "relative", width: 124, height: 124 }}>
          <svg width="124" height="124" viewBox="0 0 124 124">
            {/* Track */}
            <circle cx="62" cy="62" r={radius} fill="none" stroke="#1a1f2e" strokeWidth="9" />
            {/* Progress */}
            <circle
              cx="62" cy="62" r={radius}
              fill="none"
              stroke={color}
              strokeWidth="9"
              strokeLinecap="round"
              strokeDasharray={`${dash} ${circ}`}
              transform="rotate(-90 62 62)"
              style={{
                transition: "stroke-dasharray 0.7s cubic-bezier(0.4,0,0.2,1)",
                filter: `drop-shadow(0 0 7px ${color}90)`,
              }}
            />
          </svg>

          {/* Center label */}
          <div style={{
            position: "absolute", inset: 0,
            display: "flex", flexDirection: "column",
            alignItems: "center", justifyContent: "center",
          }}>
            {value === null ? (
              <span style={{ fontSize: 12, color: "var(--text-dim)" }}>N/A</span>
            ) : (
              <>
                <span style={{
                  fontFamily: "'Share Tech Mono', monospace",
                  fontSize: 28, fontWeight: 400, color, lineHeight: 1,
                  textShadow: `0 0 18px ${color}70`,
                }}>
                  {Math.round(safe)}
                </span>
                <span style={{
                  fontFamily: "'Share Tech Mono', monospace",
                  fontSize: 11, color: "var(--text-dim)", marginTop: 2,
                }}>
                  {unit}
                </span>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
