"use client";

import { useEffect, useRef } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Legend,
  Tooltip,
  LineController,
} from "chart.js";
import InfoList from "./InfoList";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Legend,
  Tooltip,
  LineController
);

interface MidGridProps {
  cpuHistory: (number | null)[];
  ramHistory: (number | null)[];
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

export default function MidGrid({
  cpuHistory, ramHistory,
  uptime: uptimeSec, dlSpeed, ulSpeed, watts, processCount,
}: MidGridProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<ChartJS | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    const labels = cpuHistory.map((_, i) => `${i}s`);
    const cpuColor = "#1D9E75";
    const ramColor = "#534AB7";

    if (chartRef.current) {
      chartRef.current.destroy();
    }

    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return;

    chartRef.current = new ChartJS(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "CPU",
            data: cpuHistory,
            borderColor: cpuColor,
            backgroundColor: `${cpuColor}20`,
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 4,
            borderWidth: 2,
          },
          {
            label: "RAM",
            data: ramHistory,
            borderColor: ramColor,
            backgroundColor: `${ramColor}20`,
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 4,
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 0 },
        plugins: {
          legend: { display: false },
          tooltip: {
            mode: "index",
            intersect: false,
          },
        },
        scales: {
          x: { display: false },
          y: {
            min: 0,
            max: 100,
            grid: {
              color: "rgba(128,128,128,0.1)",
            },
            ticks: {
              color: "#8B8B99",
              font: { family: "'IBM Plex Mono', monospace", size: 10 },
              stepSize: 25,
              callback: (v: number | string) => `${v}%`,
            },
          },
        },
        interaction: {
          mode: "nearest",
          axis: "x",
          intersect: false,
        },
      },
    });

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [cpuHistory, ramHistory]);

  return (
    <div className="mid-grid">
      <div className="card">
        <div className="card-header">
          <span className="card-title">Histórico — CPU & RAM</span>
          <span className="badge badge-green">Tempo real</span>
        </div>
        <div className="chart-legend">
          <div className="legend-item">
            <div className="legend-dot" style={{ backgroundColor: "#1D9E75" }} />
            <span>CPU</span>
          </div>
          <div className="legend-item">
            <div className="legend-dot" style={{ backgroundColor: "#534AB7" }} />
            <span>RAM</span>
          </div>
        </div>
        <div className="chart-wrap">
          <canvas ref={canvasRef} />
        </div>
      </div>
      <InfoList
        uptime={formatUptime(uptimeSec)}
        dlSpeed={dlSpeed}
        ulSpeed={ulSpeed}
        watts={watts}
        processCount={processCount}
      />
    </div>
  );
}
