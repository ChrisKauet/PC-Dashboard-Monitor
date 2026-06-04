"use client";

interface Disk {
  label: string;
  used_gb: number;
  total_gb: number;
  usage_percent: number;
}

interface StorageCardProps {
  disks: Disk[] | null;
}

function getDiskColor(percent: number): string {
  if (percent > 85) return "#ef4444";
  if (percent > 70) return "#eab308";
  return "#f97316";
}

export default function StorageCard({ disks }: StorageCardProps) {
  if (!disks || disks.length === 0) {
    return (
      <div className="card">
        <div
          style={{
            fontSize: "11px",
            fontWeight: 600,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "#666",
            fontFamily: "'Exo 2', sans-serif",
            marginBottom: "12px",
          }}
        >
          💾 Armazenamento
        </div>
        <div style={{ color: "#555", fontSize: "13px" }}>Sem dados de disco</div>
      </div>
    );
  }

  return (
    <div
      className="card"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "16px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Glow bg */}
      <div
        style={{
          position: "absolute",
          top: "-20px",
          right: "-20px",
          width: "100px",
          height: "100px",
          borderRadius: "50%",
          background: "#f9731608",
          filter: "blur(25px)",
          pointerEvents: "none",
        }}
      />

      {/* Header */}
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
        💾 Armazenamento
      </div>

      {/* Disk list */}
      <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        {disks.map((disk, i) => {
          const color = getDiskColor(disk.usage_percent);
          const isCritical = disk.usage_percent > 85;

          return (
            <div
              key={i}
              style={{
                padding: "12px",
                borderRadius: "10px",
                background: "var(--bg)",
                border: `1px solid ${isCritical ? "#ef444440" : "var(--border)"}`,
                boxShadow: isCritical ? "0 0 12px rgba(239,68,68,0.1)" : "none",
              }}
            >
              {/* Disk label row */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "10px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  {isCritical && <span style={{ fontSize: "14px" }}>⚠️</span>}
                  <span
                    style={{
                      fontFamily: "'Share Tech Mono', monospace",
                      fontSize: "14px",
                      color: "#ccc",
                      fontWeight: 600,
                    }}
                  >
                    {disk.label}
                  </span>
                </div>
                <span
                  style={{
                    fontFamily: "'Share Tech Mono', monospace",
                    fontSize: "13px",
                    color: color,
                    padding: "2px 8px",
                    borderRadius: "999px",
                    background: `${color}18`,
                    border: `1px solid ${color}30`,
                  }}
                >
                  {Math.round(disk.usage_percent)}%
                </span>
              </div>

              {/* Usage numbers */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: "8px",
                }}
              >
                <span
                  style={{
                    fontFamily: "'Share Tech Mono', monospace",
                    fontSize: "20px",
                    color: color,
                    textShadow: `0 0 12px ${color}50`,
                  }}
                >
                  {disk.used_gb.toFixed(1)}
                </span>
                <span
                  style={{
                    fontFamily: "'Share Tech Mono', monospace",
                    fontSize: "13px",
                    color: "var(--text-muted)",
                  }}
                >
                  / {disk.total_gb.toFixed(1)} GB
                </span>
              </div>

              {/* Progress bar */}
              <div
                style={{
                  width: "100%",
                  height: "5px",
                  background: "var(--border)",
                  borderRadius: "999px",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    height: "100%",
                    width: `${disk.usage_percent}%`,
                    background: `linear-gradient(90deg, ${color}bb, ${color})`,
                    borderRadius: "999px",
                    transition: "width 0.6s cubic-bezier(0.4,0,0.2,1)",
                    boxShadow: `0 0 6px ${color}60`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
