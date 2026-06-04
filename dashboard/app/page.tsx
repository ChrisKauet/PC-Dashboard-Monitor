"use client";

import { useEffect, useState, useCallback } from "react";
import StatusBadge from "../components/StatusBadge";
import GaugeCard from "../components/GaugeCard";
import BarCard from "../components/BarCard";
import StorageCard from "../components/StorageCard";
import CpuCoresCard from "../components/CpuCoresCard";
import TempCard from "../components/TempCard";

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
}

function formatUptime(seconds: number | null): string {
  if (!seconds) return "—";
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const parts: string[] = [];
  if (d > 0) parts.push(`${d}d`);
  if (h > 0) parts.push(`${h}h`);
  parts.push(`${m}m`);
  return parts.join(" ");
}

function getGpuLabel(vendor: string | null): string {
  if (!vendor) return "GPU";
  if (vendor === "nvidia") return "GPU NVIDIA";
  if (vendor === "amd") return "GPU AMD";
  if (vendor === "intel") return "GPU Intel";
  return "GPU";
}

export default function Home() {
  const [data, setData] = useState<SensorData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastFetch, setLastFetch] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    try {
      // In production (Vercel), fetch directly from the tunneled API URL
      // In dev, use the local proxy route
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      const url = apiUrl ? `${apiUrl}/api/sensors` : "/api/sensors";

      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setError(body.error || `Erro ${res.status}`);
        return;
      }
      const json: SensorData = await res.json();
      setData(json);
      setLastFetch(new Date());
      setError(null);
    } catch (e) {
      setError("Falha ao conectar com a API");
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0d0d0d",
        padding: "0 0 48px 0",
      }}
    >
      {/* Header */}
      <header
        style={{
          borderBottom: "1px solid #1e1e1e",
          background: "#111111",
          padding: "16px 20px",
          position: "sticky",
          top: 0,
          zIndex: 10,
          backdropFilter: "blur(12px)",
        }}
      >
        <div
          style={{
            maxWidth: "680px",
            margin: "0 auto",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "32px",
                height: "32px",
                borderRadius: "8px",
                background: "linear-gradient(135deg, #00e5ff30, #a855f730)",
                border: "1px solid #00e5ff30",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "16px",
              }}
            >
              📡
            </div>
            <div>
              <h1
                style={{
                  fontFamily: "'Exo 2', sans-serif",
                  fontSize: "15px",
                  fontWeight: 700,
                  color: "#e8e8e8",
                  letterSpacing: "0.02em",
                  lineHeight: 1,
                }}
              >
                PC Dashboard
              </h1>
              <div
                style={{
                  fontFamily: "'Share Tech Mono', monospace",
                  fontSize: "10px",
                  color: "#444",
                  marginTop: "2px",
                }}
              >
                Monitor de Sensores
              </div>
            </div>
          </div>

          <StatusBadge
            online={data?.status === "online"}
            lastUpdate={lastFetch?.toISOString() ?? null}
            hostname={data?.hostname}
          />
        </div>
      </header>

      {/* Main content */}
      <main
        style={{
          maxWidth: "680px",
          margin: "0 auto",
          padding: "24px 16px",
          display: "flex",
          flexDirection: "column",
          gap: "16px",
        }}
      >
        {/* Loading skeleton */}
        {loading && (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="skeleton"
                style={{ height: i === 1 ? "180px" : "120px", borderRadius: "16px" }}
              />
            ))}
          </div>
        )}

        {/* Error state */}
        {!loading && error && (
          <div
            style={{
              padding: "24px",
              borderRadius: "16px",
              background: "#1a0a0a",
              border: "1px solid #ef444440",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "32px", marginBottom: "12px" }}>⚠️</div>
            <div
              style={{
                fontFamily: "'Exo 2', sans-serif",
                fontSize: "15px",
                fontWeight: 600,
                color: "#ef4444",
                marginBottom: "6px",
              }}
            >
              Erro ao carregar dados
            </div>
            <div style={{ fontSize: "13px", color: "#666" }}>{error}</div>
            <div style={{ fontSize: "12px", color: "#444", marginTop: "8px" }}>
              Verifique se o backend está rodando e o túnel ativo
            </div>
          </div>
        )}

        {/* Dashboard */}
        {!loading && data && !error && (
          <>
            {/* Uptime info bar */}
            <div
              style={{
                padding: "10px 16px",
                borderRadius: "10px",
                background: "#111",
                border: "1px solid #1e1e1e",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontSize: "14px" }}>⏱️</span>
                <span
                  style={{
                    fontFamily: "'Exo 2', sans-serif",
                    fontSize: "12px",
                    color: "#666",
                    fontWeight: 500,
                  }}
                >
                  Uptime
                </span>
                <span
                  style={{
                    fontFamily: "'Share Tech Mono', monospace",
                    fontSize: "13px",
                    color: "#aaa",
                  }}
                >
                  {formatUptime(data.uptime_sec)}
                </span>
              </div>
              {lastFetch && (
                <span
                  style={{
                    fontFamily: "'Share Tech Mono', monospace",
                    fontSize: "11px",
                    color: "#444",
                  }}
                >
                  atualizado {lastFetch.toLocaleTimeString("pt-BR")}
                </span>
              )}
            </div>

            {/* CPU + GPU Gauges */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: "16px",
              }}
            >
              <GaugeCard
                title="CPU"
                value={data.cpu_usage}
                color="#00e5ff"
                unit="%"
                temp={data.cpu_temp}
                icon="⚡"
              />
              <GaugeCard
                title={getGpuLabel(data.gpu_vendor)}
                value={data.gpu_usage}
                color="#a855f7"
                unit="%"
                temp={data.gpu_temp}
                icon="🎮"
                subtitle={data.gpu_vendor ? `(${data.gpu_vendor.toUpperCase()})` : undefined}
              />
            </div>

            {/* Temperature Card — CPU & GPU side by side */}
            <TempCard
              cpuTemp={data.cpu_temp}
              gpuTemp={data.gpu_temp}
              cpuLabel="CPU"
              gpuLabel={data.gpu_vendor ? data.gpu_vendor.toUpperCase() : "GPU"}
            />

            {/* RAM */}
            <BarCard
              title="RAM"
              used={data.ram_used}
              total={data.ram_total}
              unit="GB"
              color="#22c55e"
              percent={data.ram_usage}
              icon="🧠"
            />

            {/* VRAM */}
            {(data.vram_used !== null || data.vram_total !== null) && (
              <BarCard
                title="VRAM"
                used={data.vram_used}
                total={data.vram_total}
                unit="MB"
                color="#a855f7"
                percent={
                  data.vram_used !== null && data.vram_total !== null && data.vram_total > 0
                    ? (data.vram_used / data.vram_total) * 100
                    : null
                }
                icon="🖼️"
                subtitle={data.gpu_vendor ? `Memória ${data.gpu_vendor.toUpperCase()}` : undefined}
              />
            )}

            {/* CPU Cores */}
            {data.cpu_cores && data.cpu_cores.length > 0 && (
              <CpuCoresCard cores={data.cpu_cores} />
            )}

            {/* Storage */}
            <StorageCard disks={data.storage} />

            {/* GPU Fan RPM (if available) */}
            {data.gpu_fan_rpm !== null && data.gpu_fan_rpm !== undefined && (
              <div
                className="card"
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{ fontSize: "20px" }}>🌀</span>
                  <div>
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
                      Fan GPU
                    </div>
                    <div
                      style={{
                        fontFamily: "'Share Tech Mono', monospace",
                        fontSize: "22px",
                        color: "#a855f7",
                      }}
                    >
                      {data.gpu_fan_rpm} RPM
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer
        style={{
          textAlign: "center",
          paddingTop: "8px",
          paddingBottom: "16px",
        }}
      >
        <p
          style={{
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: "11px",
            color: "#333",
          }}
        >
          PC Dashboard Monitor · Atualiza a cada 5s
        </p>
      </footer>
    </div>
  );
}
