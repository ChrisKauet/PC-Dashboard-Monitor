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

function getTempColor(temp: number | null): string {
  if (temp === null) return "#888";
  if (temp <= 60) return "#22c55e";
  if (temp <= 80) return "#eab308";
  return "#ef4444";
}

export default function GaugeCard({
  title,
  value,
  color,
  unit = "%",
  temp,
  subtitle,
  icon,
}: GaugeCardProps) {
  const safeValue = value ?? 0;
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const strokeDash = (safeValue / 100) * circumference;
  const tempColor = getTempColor(temp ?? null);

  return (
    <div
      className="card"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "12px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Glow bg */}
      <div
        style={{
          position: "absolute",
          top: "-30px",
          right: "-30px",
          width: "120px",
          height: "120px",
          borderRadius: "50%",
          background: `${color}10`,
          filter: "blur(30px)",
          pointerEvents: "none",
        }}
      />

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
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
        {temp !== undefined && temp !== null && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "4px",
              padding: "4px 10px",
              borderRadius: "999px",
              background: `${tempColor}18`,
              border: `1px solid ${tempColor}40`,
            }}
          >
            <span style={{ fontSize: "13px" }}>🌡️</span>
            <span
              style={{
                fontFamily: "'Share Tech Mono', monospace",
                fontSize: "13px",
                fontWeight: 600,
                color: tempColor,
              }}
            >
              {temp}°C
            </span>
          </div>
        )}
      </div>

      {/* Gauge SVG */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ position: "relative", width: "130px", height: "130px" }}>
          <svg width="130" height="130" viewBox="0 0 130 130">
            {/* Track */}
            <circle
              cx="65"
              cy="65"
              r={radius}
              fill="none"
              stroke="#2a2a2a"
              strokeWidth="10"
              strokeLinecap="round"
            />
            {/* Progress */}
            <circle
              cx="65"
              cy="65"
              r={radius}
              fill="none"
              stroke={color}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={`${strokeDash} ${circumference}`}
              strokeDashoffset={circumference * 0.25}
              style={{
                transition: "stroke-dasharray 0.6s cubic-bezier(0.4,0,0.2,1)",
                filter: `drop-shadow(0 0 6px ${color}80)`,
              }}
              transform="rotate(-90 65 65)"
            />
            {/* Glow dot at end */}
            {value !== null && value > 0 && (
              <circle
                cx="65"
                cy="65"
                r={radius}
                fill="none"
                stroke={color}
                strokeWidth="3"
                strokeLinecap="round"
                strokeDasharray={`0 ${circumference}`}
                strokeDashoffset={circumference * 0.25}
                style={{ filter: `drop-shadow(0 0 10px ${color})` }}
                transform="rotate(-90 65 65)"
              />
            )}
          </svg>
          {/* Center value */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {value === null ? (
              <span style={{ fontSize: "13px", color: "#555" }}>N/A</span>
            ) : (
              <>
                <span
                  style={{
                    fontFamily: "'Share Tech Mono', monospace",
                    fontSize: "26px",
                    fontWeight: 400,
                    color: color,
                    lineHeight: 1,
                    textShadow: `0 0 20px ${color}60`,
                  }}
                >
                  {Math.round(safeValue)}
                </span>
                <span
                  style={{
                    fontFamily: "'Share Tech Mono', monospace",
                    fontSize: "12px",
                    color: "#666",
                    marginTop: "2px",
                  }}
                >
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
