"use client";

import { IconCpu, IconDatabase, IconDeviceDesktop, IconServer } from "@tabler/icons-react";
import MetricCard from "./MetricCard";

interface MetricsGridProps {
  cpuUsage: number | null;
  cpuCores: number | null;
  cpuModel: string | null;
  ramUsed: number | null;
  ramTotal: number | null;
  ramUsage: number | null;
  gpuUsage: number | null;
  vramUsed: number | null;
  vramTotal: number | null;
  gpuVendor: string | null;
  diskUsed: number | null;
  diskTotal: number | null;
  diskPercent: number | null;
}

export default function MetricsGrid({
  cpuUsage, cpuCores, cpuModel,
  ramUsed, ramTotal, ramUsage,
  gpuUsage, vramUsed, vramTotal, gpuVendor,
  diskUsed, diskTotal, diskPercent,
}: MetricsGridProps) {
  const cpuSubtitle = cpuModel
    ? `${cpuModel} · ${cpuCores ?? "?"} núcleos`
    : cpuCores ? `${cpuCores} núcleos` : "";

  const ramSubtitle = ramTotal ? `de ${ramTotal} GB` : "";
  const gpuSubtitle = vramTotal ? `${vramUsed ?? "?"} / ${vramTotal} MB${gpuVendor ? ` · ${gpuVendor.toUpperCase()}` : ""}` : "";
  const diskSubtitle = diskTotal ? `de ${diskTotal} GB` : "";

  return (
    <div className="metrics-grid">
      <MetricCard
        label="CPU"
        icon={<IconCpu size={13} />}
        value={cpuUsage}
        unit="%"
        subtitle={cpuSubtitle}
        percent={cpuUsage}
        colorClass="cpu"
      />
      <MetricCard
        label="RAM"
        icon={<IconDatabase size={13} />}
        value={ramUsed}
        unit="GB"
        subtitle={ramSubtitle}
        percent={ramUsage}
        colorClass="ram"
      />
      <MetricCard
        label="GPU"
        icon={<IconDeviceDesktop size={13} />}
        value={gpuUsage}
        unit="%"
        subtitle={gpuSubtitle}
        percent={gpuUsage}
        colorClass="gpu"
      />
      <MetricCard
        label="Disco"
        icon={<IconServer size={13} />}
        value={diskUsed}
        unit="GB"
        subtitle={diskSubtitle}
        percent={diskPercent}
        colorClass="disk"
      />
    </div>
  );
}
