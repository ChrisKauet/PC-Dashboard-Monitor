interface TempCardProps {
  cpuTemp: number | null;
  gpuTemp: number | null;
  cpuLabel?: string;
  gpuLabel?: string;
}

export default function TempCard({ cpuTemp, gpuTemp, cpuLabel = "CPU", gpuLabel = "GPU" }: TempCardProps) {
  return (
    <div style={{
      background: "#111",
      border: "1px solid #1e1e1e",
      borderRadius: 16,
      padding: 20,
      display: "flex",
      gap: 16,
    }}>
      <div style={{ flex: 1, textAlign: "center" }}>
        <div style={{ fontSize: 11, color: "#666", marginBottom: 4, fontFamily: "Share Tech Mono, monospace" }}>
          🌡️ {cpuLabel}
        </div>
        <div style={{ fontSize: 28, fontWeight: 700, color: cpuTemp ? "#e8e8e8" : "#444", fontFamily: "Share Tech Mono, monospace" }}>
          {cpuTemp !== null ? `${cpuTemp}°C` : "—"}
        </div>
      </div>
      <div style={{ width: 1, background: "#1e1e1e" }} />
      <div style={{ flex: 1, textAlign: "center" }}>
        <div style={{ fontSize: 11, color: "#666", marginBottom: 4, fontFamily: "Share Tech Mono, monospace" }}>
          🌡️ {gpuLabel}
        </div>
        <div style={{ fontSize: 28, fontWeight: 700, color: gpuTemp ? "#e8e8e8" : "#444", fontFamily: "Share Tech Mono, monospace" }}>
          {gpuTemp !== null ? `${gpuTemp}°C` : "—"}
        </div>
      </div>
    </div>
  );
}
