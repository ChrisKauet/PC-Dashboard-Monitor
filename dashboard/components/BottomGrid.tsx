"use client";

import ProcessList from "./ProcessList";
import TempGrid from "./TempGrid";

interface BottomGridProps {
  processes: { name: string; cpu_percent: number; mem_mb: number }[];
  cpuTemp: number | null;
  gpuTemp: number | null;
  ssdTemp: number | null;
  mbTemp: number | null;
}

export default function BottomGrid({ processes, cpuTemp, gpuTemp, ssdTemp, mbTemp }: BottomGridProps) {
  return (
    <div className="bot-grid">
      <ProcessList processes={processes} />
      <TempGrid cpuTemp={cpuTemp} gpuTemp={gpuTemp} ssdTemp={ssdTemp} mbTemp={mbTemp} />
    </div>
  );
}
