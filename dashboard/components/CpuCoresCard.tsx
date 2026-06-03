"use client";

interface CpuCoresCardProps {
  cores: number[] | null;
}

export default function CpuCoresCard({ cores }: CpuCoresCardProps) {
  if (!cores || cores.length === 0) return null;

  const getBarColor = (v: number) => {
    if (v >= 90) return "#ef4444";
    if (v >= 70) return "#eab308";
    return "#00e5ff";
  };

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
      {/* Glow */}
      <div
        style={{
          position: "absolute",
          bottom: "-20px",
          left: "-20px",
          width: "100px",
          height: "100px",
          borderRadius: "50%",
          background: "#00e5ff08",
          filter: "blur(25px)",
          pointerEvents: "none",
        }}
      />

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
        🖥️ Núcleos CPU ({cores.length} threads)
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(60px, 1fr))",
          gap: "10px",
        }}
      >
        {cores.map((usage, i) => {
          const color = getBarColor(usage);
          return (
            <div
              key={i}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "6px",
              }}
            >
              {/* Vertical mini bar */}
              <div
                style={{
                  width: "100%",
                  height: "50px",
                  background: "#111",
                  borderRadius: "6px",
                  overflow: "hidden",
                  display: "flex",
                  flexDirection: "column-reverse",
                  border: "1px solid #222",
                }}
              >
                <div
                  style={{
                    width: "100%",
                    height: `${usage}%`,
                    background: `linear-gradient(0deg, ${color}bb, ${color})`,
                    transition: "height 0.5s ease",
                    boxShadow: `0 0 6px ${color}60`,
                  }}
                />
              </div>
              {/* Labels */}
              <span
                style={{
                  fontFamily: "'Share Tech Mono', monospace",
                  fontSize: "10px",
                  color: color,
                  fontWeight: 600,
                }}
              >
                {Math.round(usage)}%
              </span>
              <span style={{ fontSize: "9px", color: "#444", fontFamily: "'Exo 2', sans-serif" }}>
                C{i}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
