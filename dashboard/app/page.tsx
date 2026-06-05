"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Topbar from "../components/Topbar";
import MetricsGrid from "../components/MetricsGrid";
import MidGrid from "../components/MidGrid";
import BottomGrid from "../components/BottomGrid";

interface SensorData {
  status: string;
  error?: string;
  cpu_usage: number | null;
  cpu_temp: number | null;
  cpu_cores: number[] | null;
  gpu_usage: number | null;
  gpu_temp: number | null;
  vram_used: number | null;
  vram_total: number | null;
  gpu_fan_rpm: number | null;
  gpu_vendor: string | null;
  ram_used: number | null;
  ram_total: number | null;
  ram_usage: number | null;
  storage: { label: string; used_gb: number; total_gb: number; usage_percent: number }[] | null;
  uptime_sec: number | null;
  hostname: string | null;
  // New fields (may not exist yet in backend)
  dl_speed?: number | null;
  ul_speed?: number | null;
  watts?: number | null;
  process_count?: number | null;
  processes?: { name: string; cpu_percent: number; mem_mb: number }[] | null;
  temp_ssd?: number | null;
  temp_mb?: number | null;
}

const HISTORY_LENGTH = 30;

function formatUptime(seconds: number | null): string {
  if (!seconds) return "—";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${m}m`;
}

function getCpuModel(cores: number[] | null): string | null {
  if (!cores) return null;
  return `${cores.length} núcleos`;
}

export default function Home() {
  const [data, setData] = useState<SensorData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const cpuHistoryRef = useRef<(number | null)[]>([]);
  const ramHistoryRef = useRef<(number | null)[]>([]);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch("/api/sensors", { cache: "no-store" });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setError(body.error || `Erro ${res.status}`);
        return;
      }
      const json: SensorData = await res.json();
      setData(json);

      // Update rolling history
      cpuHistoryRef.current = [
        ...cpuHistoryRef.current.slice(-(HISTORY_LENGTH - 1)),
        json.cpu_usage,
      ];
      ramHistoryRef.current = [
        ...ramHistoryRef.current.slice(-(HISTORY_LENGTH - 1)),
        json.ram_usage,
      ];

      setError(null);
    } catch {
      setError("Falha ao conectar com a API");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const id = setInterval(fetchData, 5000);
    return () => clearInterval(id);
  }, [fetchData]);

  // Build process list from data or show placeholder
  const processes = data?.processes ?? [];

  // Get primary disk (first one)
  const primaryDisk = data?.storage?.[0] ?? null;

  return (
    <div className="app">
      <Topbar
        hostname={data?.hostname ?? null}
        online={data?.status === "online"}
      />

      {/* Loading skeleton */}
      {loading && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="skeleton" style={{ height: 100 }} />
          <div className="skeleton" style={{ height: 200 }} />
          <div className="skeleton" style={{ height: 160 }} />
        </div>
      )}

      {/* Error state */}
      {!loading && error && (
        <div className="card" style={{
          textAlign: "center",
          padding: 32,
          borderColor: "rgba(239,68,68,0.3)",
          background: "rgba(239,68,68,0.05)",
        }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>⚠️</div>
          <div style={{
            fontFamily: "var(--font-sans)",
            fontSize: 15,
            fontWeight: 600,
            color: "#ef4444",
            marginBottom: 6,
          }}>
            Erro ao carregar dados
          </div>
          <div style={{ fontSize: 13, color: "var(--text-muted)" }}>{error}</div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 8 }}>
            Verifique se o backend está rodando e o túnel ativo
          </div>
        </div>
      )}

      {/* Dashboard */}
      {!loading && data && !error && (
        <>
          <MetricsGrid
            cpuUsage={data.cpu_usage}
            cpuCores={data.cpu_cores?.length ?? null}
            cpuModel={getCpuModel(data.cpu_cores)}
            ramUsed={data.ram_used}
            ramTotal={data.ram_total}
            ramUsage={data.ram_usage}
            gpuUsage={data.gpu_usage}
            vramUsed={data.vram_used}
            vramTotal={data.vram_total}
            gpuVendor={data.gpu_vendor}
            diskUsed={primaryDisk?.used_gb ?? null}
            diskTotal={primaryDisk?.total_gb ?? null}
            diskPercent={primaryDisk?.usage_percent ?? null}
          />

          <MidGrid
            cpuHistory={cpuHistoryRef.current}
            ramHistory={ramHistoryRef.current}
            uptime={formatUptime(data.uptime_sec)}
            dlSpeed={data.dl_speed ?? null}
            ulSpeed={data.ul_speed ?? null}
            watts={data.watts ?? null}
            processCount={data.process_count ?? null}
          />

          <BottomGrid
            processes={processes}
            cpuTemp={data.cpu_temp}
            gpuTemp={data.gpu_temp}
            ssdTemp={data.temp_ssd ?? null}
            mbTemp={data.temp_mb ?? null}
          />
        </>
      )}

      {/* Footer */}
      <footer style={{ textAlign: "center", paddingTop: 24, paddingBottom: 16 }}>
        <p style={{
          fontFamily: "var(--font-mono)",
          fontSize: 10,
          color: "var(--text-muted)",
        }}>
          PC Dashboard Monitor · atualiza a cada 5s
        </p>
      </footer>
    </div>
  );
}
