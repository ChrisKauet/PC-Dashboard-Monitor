"use client";

interface StatusBadgeProps {
  online: boolean;
  lastUpdate: string | null;
  hostname?: string | null;
}

export default function StatusBadge({ online, lastUpdate, hostname }: StatusBadgeProps) {
  if (online === false && !lastUpdate) {
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

  const color = online ? "#22c55e" : "#ef4444";
  const label = online ? "Ao Vivo" : "Offline";
  const emoji = online ? "🟢" : "🔴";

  const formatTime = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
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
            animation: online ? "pulse-dot 1.5s ease-in-out infinite" : "none",
          }}
          className="animate-pulse-dot"
        />
        {emoji} {label}
      </div>
      {lastUpdate && (
        <span style={{ fontSize: "11px", color: "#555", fontFamily: "'Share Tech Mono', monospace" }}>
          {hostname ? `${hostname} · ` : ""}{formatTime(lastUpdate)}
        </span>
      )}
    </div>
  );
}
