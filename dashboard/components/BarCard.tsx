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

export default function BarCard({
  title,
  used,
  total,
  unit,
  color,
  percent,
  icon,
  subtitle,
}: BarCardProps) {
  const safePercent = percent ?? 0;

  return (
    <div
      className="card"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "14px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Glow bg */}
      <div
        style={{
          position: "absolute",
          bottom: "-20px",
          left: "-20px",
          width: "100px",
          height: "100px",
          borderRadius: "50%",
          background: `${color}0c`,
          filter: "blur(25px)",
          pointerEvents: "none",
        }}
      />

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div
            style={{
              fontSize: "11px",
              fontWeight: 600,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "#666",
              fontFamily: "'Exo 2', sans-serif",
            }}
          >
            {icon && <span style={{ marginRight: "6px" }}>{icon}</span>}
            {title}
          </div>
          {subtitle && (
            <div style={{ fontSize: "11px", color: "#555", marginTop: "2px" }}>{subtitle}</div>
          )}
        </div>
        {/* Percentage badge */}
        <div
          style={{
            padding: "4px 10px",
            borderRadius: "999px",
            background: `${color}18`,
            border: `1px solid ${color}30`,
          }}
        >
          <span
            style={{
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: "14px",
              fontWeight: 400,
              color: color,
            }}
          >
            {percent !== null ? `${Math.round(safePercent)}%` : "N/A"}
          </span>
        </div>
      </div>

      {/* Values */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <span
          style={{
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: "28px",
            color: color,
            textShadow: `0 0 16px ${color}50`,
          }}
        >
          {used !== null ? used.toFixed(used < 100 ? 1 : 0) : "—"}
        </span>
        <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "13px", color: "#555" }}>
          / {total !== null ? total.toFixed(total < 100 ? 1 : 0) : "—"} {unit}
        </span>
      </div>

      {/* Progress bar */}
      <div
        style={{
          width: "100%",
          height: "6px",
          background: "#2a2a2a",
          borderRadius: "999px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${safePercent}%`,
            background: `linear-gradient(90deg, ${color}bb, ${color})`,
            borderRadius: "999px",
            transition: "width 0.6s cubic-bezier(0.4,0,0.2,1)",
            boxShadow: `0 0 8px ${color}60`,
          }}
        />
      </div>
    </div>
  );
}
