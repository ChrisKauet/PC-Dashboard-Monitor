"use client";

interface TopbarProps {
  hostname: string | null;
  online: boolean;
}

export default function Topbar({ hostname, online }: TopbarProps) {
  return (
    <div style={{
      borderBottom: "0.5px solid var(--border)",
      padding: "14px 0",
      marginBottom: 20,
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      flexWrap: "wrap",
      gap: 12,
    }}>
      <div style={{
        fontFamily: "var(--font-mono)",
        fontSize: 15,
        fontWeight: 600,
        color: "var(--text-primary)",
        letterSpacing: 2,
      }}>
        SYS<span style={{ color: "var(--c-green)" }}>.</span>MONITOR
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
        <span className="hostname" style={{
          fontFamily: "var(--font-mono)",
          fontSize: 11,
          color: "var(--text-muted)",
        }}>
          {hostname ?? "—"}
        </span>
        {online && (
          <div className="badge badge-green">
            <div className="live-dot" />
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, fontWeight: 600 }}>
              LIVE
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
