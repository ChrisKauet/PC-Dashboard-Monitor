"use client";

import { IconClock, IconArrowDown, IconArrowUp, IconBolt, IconTemperature } from "@tabler/icons-react";

interface InfoListProps {
  uptime: string;
  dlSpeed: number | null;
  ulSpeed: number | null;
  watts: number | null;
  processCount: number | null;
}

function formatUptime(seconds: number | null): string {
  if (!seconds) return "—";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${m}m`;
}

export default function InfoList({ uptime, dlSpeed, ulSpeed, watts, processCount }: InfoListProps) {
  const items = [
    { icon: <IconClock size={14} />, label: "Uptime", value: uptime },
    { icon: <IconArrowDown size={14} />, label: "Download", value: dlSpeed !== null ? `${dlSpeed} MB/s` : "—" },
    { icon: <IconArrowUp size={14} />, label: "Upload", value: ulSpeed !== null ? `${ulSpeed} MB/s` : "—" },
    { icon: <IconBolt size={14} />, label: "Energia", value: watts !== null ? `${watts}W` : "—" },
    { icon: <IconTemperature size={14} />, label: "Processos", value: processCount !== null ? `${processCount}` : "—" },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Sistema</span>
        <span className="badge badge-blue">Info</span>
      </div>
      <div className="info-list">
        {items.map((item) => (
          <div key={item.label} className="info-item">
            <div className="info-label">
              {item.icon}
              {item.label}
            </div>
            <span className="info-val">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
