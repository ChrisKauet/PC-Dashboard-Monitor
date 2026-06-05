"use client";

interface Process {
  name: string;
  cpu_percent: number;
  mem_mb: number;
}

interface ProcessListProps {
  processes: Process[];
}

const DOT_COLORS = ["#1D9E75", "#534AB7", "#D85A30", "#BA7517", "#185FA5"];

export default function ProcessList({ processes }: ProcessListProps) {
  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Top processos</span>
        <span className="badge badge-orange">CPU · MEM</span>
      </div>
      <div className="proc-header">
        <span>Processo</span>
        <span style={{ display: "flex", gap: 16 }}>
          <span style={{ width: 38, textAlign: "right" }}>CPU</span>
          <span style={{ width: 50, textAlign: "right" }}>MEM</span>
        </span>
      </div>
      <div className="proc-list">
        {processes.slice(0, 5).map((proc, i) => (
          <div key={i} className="proc-item">
            <div
              className="proc-dot"
              style={{ backgroundColor: DOT_COLORS[i % DOT_COLORS.length] }}
            />
            <span className="proc-name" title={proc.name}>{proc.name}</span>
            <span className="proc-cpu">{proc.cpu_percent.toFixed(1)}%</span>
            <span className="proc-mem">{proc.mem_mb} MB</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export type { Process };
