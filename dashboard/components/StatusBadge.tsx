"use client";

interface StatusBadgeProps {
  ageSeconds: number | null;
  lastUpdate: string | null;
  hostname?: string | null;
}

export default function StatusBadge({ ageSeconds, lastUpdate, hostname }: StatusBadgeProps) {
  if (ageSeconds === null) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          padding: "6px 14px",
          borderRadius: "999px",
          background: "#1a1a1a",
          border: "1px solid #333",
          fontSize: "13px",
          fontFamily: "'Exo 2', sans-serif",
          color: "#888",
        }}
      >
        <span
          style={{
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            background: "#555",
            display: "inline-block",
          }}
        />
        Carregando...
      </div>
    );
  }

  const isOnline = ageSeconds <= 15;
  const color = isOnline ? "#22c55e" : "#ef4444";
  const label = isOnline ? "Ao Vivo" : "PC Offline";
  const emoji = isOnline ? "🟢" : "🔴";

  const formatAge = (s: number) => {
    if (s < 60) return `${Math.round(s)}s atrás`;
    if (s < 3600) return `${Math.round(s / 60)}min atrás`;
    return `${Math.round(s / 3600)}h atrás`;
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "4px" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          padding: "6px 14px",
          borderRadius: "999px",
          background: `${color}18`,
          border: `1px solid ${color}40`,
          fontSize: "13px",
          fontFamily: "'Exo 2', sans-serif",
          fontWeight: 600,
          color: color,
        }}
      >
        <span
          style={{
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            background: color,
            display: "inline-block",
            boxShadow: `0 0 8px ${color}`,
            animation: isOnline ? "pulse-dot 1.5s ease-in-out infinite" : "none",
          }}
          className="animate-pulse-dot"
        />
        {emoji} {label}
      </div>
      {lastUpdate && (
        <span style={{ fontSize: "11px", color: "#555", fontFamily: "'Share Tech Mono', monospace" }}>
          {hostname ? `${hostname} · ` : ""}{formatAge(ageSeconds)}
        </span>
      )}
    </div>
  );
}
