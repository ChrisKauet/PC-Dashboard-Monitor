"use client";

import { useEffect, useState, useCallback } from "react";
import StatusBadge from "../components/StatusBadge";
import GaugeCard from "../components/GaugeCard";
import BarCard from "../components/BarCard";
import StorageCard from "../components/StorageCard";
import CpuCoresCard from "../components/CpuCoresCard";

interface Disk {
  label: string;
  used_gb: number;
  total_gb: number;
  usage_percent: number;
}

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
  storage: Disk[] | null;
  uptime_sec: number | null;
  hostname: string | null;
}

function formatUptime(s: number | null): string {
  if (!s) return "—";
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  const parts: string[] = [];
  if (d > 0) parts.push(`${d}d`);
  if (h > 0) parts.push(`${h}h`);
  parts.push(`${m}m`);
  return parts.join(" ");
}

function getGpuLabel(vendor: string | null): string {
  if (vendor === "nvidia") return "GPU NVIDIA";
  if (vendor === "amd") return "GPU AMD";
  if (vendor === "intel") return "GPU Intel";
  return "GPU";
}

// Small inline temperature badge used in the info bar
function TempBadge({ label, value, color }: { label: string; value: number | null; color: string }) {
  const hasValue = value !== null && value !== undefined;
  const textColor = hasValue
    ? value! <= 60 ? "#22d3a5" : value! <= 80 ? "#f59e0b" : "#ef4444"
    : "#334155";

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 11, color: "#475569", letterSpacing: "0.06em" }}>
        {label}
      </span>
      <span
        style={{
          fontFamily: "'Share Tech Mono', monospace",
          fontSize: 13,
          fontWeight: 600,
          color: textColor,
          background: hasValue ? `${textColor}18` : "transparent",
          border: `1px solid ${hasValue ? textColor + "35" : "transparent"}`,
          padding: "1px 8px",
          borderRadius: 999,
        }}
      >
        {hasValue ? `${value}°C` : "—"}
      </span>
    </div>
  );
}

export default function Home() {
  const [data, setData] = useState<SensorData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastFetch, setLastFetch] = useState<Date | null>(null);

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
      setLastFetch(new Date());
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

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", paddingBottom: 48 }}>

      {/* ── Header ── */}
      <header style={{
        position: "sticky", top: 0, zIndex: 20,
        background: "rgba(8,11,16,0.85)",
        backdropFilter: "blur(16px)",
        borderBottom: "1px solid var(--border)",
      }}>
        <div style={{
          maxWidth: 740, margin: "0 auto",
          padding: "12px 20px",
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}>
          {/* Logo */}
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{
              width: 34, height: 34, borderRadius: 10,
              background: "linear-gradient(135deg, #00d4ff22, #a855f722)",
              border: "1px solid #00d4ff25",
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 17,
            }}>📡</div>
            <div>
              <h1 style={{
                fontFamily: "'Exo 2', sans-serif", fontWeight: 700, fontSize: 15,
                color: "var(--text)", letterSpacing: "0.03em", lineHeight: 1,
              }}>
                PC Dashboard
              </h1>
              <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 10, color: "var(--text-dim)", marginTop: 2 }}>
                Monitor de Sensores
              </div>
            </div>
          </div>

          {/* Status badge */}
          <StatusBadge
            online={data?.status === "online"}
            lastUpdate={lastFetch?.toISOString() ?? null}
            hostname={data?.hostname}
          />
        </div>
      </header>

      {/* ── Main ── */}
      <main style={{ maxWidth: 740, margin: "0 auto", padding: "20px 16px", display: "flex", flexDirection: "column", gap: 14 }}>

        {/* Loading */}
        {loading && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }} className="fade-in">
            {[200, 160, 120, 120, 120].map((h, i) => (
              <div key={i} className="skeleton" style={{ height: h }} />
            ))}
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div className="card fade-in" style={{ textAlign: "center", padding: "36px 24px", borderColor: "#ef444435" }}>
            <div style={{ fontSize: 40, marginBottom: 16 }}>⚠️</div>
            <div style={{ fontFamily: "'Exo 2', sans-serif", fontSize: 16, fontWeight: 600, color: "#ef4444", marginBottom: 6 }}>
              Sem conexão com o backend
            </div>
            <div style={{ fontSize: 13, color: "var(--text-muted)" }}>{error}</div>
            <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 8 }}>
              Verifique se o <code style={{ color: "#a855f7" }}>server.py</code> está rodando
            </div>
          </div>
        )}

        {/* Dashboard */}
        {!loading && data && !error && (
          <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: 14 }}>

            {/* ── Info bar: uptime + temps ── */}
            <div className="card" style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "10px 20px",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "12px 18px",
            }}>
              {/* Uptime */}
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 14 }}>⏱️</span>
                <span style={{ fontFamily: "'Exo 2', sans-serif", fontSize: 11, color: "var(--text-muted)", fontWeight: 500, letterSpacing: "0.04em" }}>
                  UPTIME
                </span>
                <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 13, color: "var(--text)" }}>
                  {formatUptime(data.uptime_sec)}
                </span>
              </div>

              {/* Temperatures */}
              <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
                <TempBadge label="CPU" value={data.cpu_temp} color="#00d4ff" />
                <TempBadge label={data.gpu_vendor?.toUpperCase() ?? "GPU"} value={data.gpu_temp} color="#a855f7" />
              </div>

              {/* Last updated */}
              {lastFetch && (
                <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 10, color: "var(--text-dim)" }}>
                  {lastFetch.toLocaleTimeString("pt-BR")}
                </span>
              )}
            </div>

            {/* ── CPU + GPU gauges ── */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
              gap: 14,
            }}>
              <GaugeCard title="CPU" value={data.cpu_usage} color="#00d4ff" unit="%" temp={data.cpu_temp} icon="⚡" />
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

            {/* ── RAM ── */}
            <BarCard
              title="RAM"
              used={data.ram_used}
              total={data.ram_total}
              unit="GB"
              color="#22d3a5"
              percent={data.ram_usage}
              icon="🧠"
            />

            {/* ── VRAM ── */}
            {(data.vram_total !== null) && (
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

            {/* ── CPU Cores ── */}
            {data.cpu_cores && data.cpu_cores.length > 0 && (
              <CpuCoresCard cores={data.cpu_cores} />
            )}

            {/* ── Storage ── */}
            <StorageCard disks={data.storage} />

          </div>
        )}
      </main>

      {/* ── Footer ── */}
      <footer style={{ textAlign: "center", paddingBottom: 20 }}>
        <p style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 10, color: "var(--text-dim)" }}>
          PC Dashboard Monitor · atualiza a cada 5s
        </p>
      </footer>
    </div>
  );
}
