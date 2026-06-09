"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  IconCpu, IconDatabase, IconDeviceDesktop, IconServer,
  IconClock, IconArrowDown, IconArrowUp, IconBolt, IconApps,
  IconTemperature,
} from "@tabler/icons-react";
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  Filler, Legend, Tooltip, LineController,
} from "chart.js";

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  Filler, Legend, Tooltip, LineController
);

// ── Types ──
interface Disk { label: string; used_gb: number; total_gb: number; usage_percent: number }
interface Proc { name: string; cpu_percent: number; mem_mb: number }
interface SensorData {
  status: string; error?: string;
  cpu_usage: number | null; cpu_temp: number | null; cpu_cores: number[] | null;
  gpu_usage: number | null; gpu_temp: number | null;
  vram_used: number | null; vram_total: number | null; gpu_vendor: string | null;
  ram_used: number | null; ram_total: number | null; ram_usage: number | null;
  storage: Disk[] | null;
  uptime_sec: number | null; hostname: string | null;
  dl_speed?: number | null; ul_speed?: number | null;
  watts?: number | null; process_count?: number | null;
  processes?: Proc[] | null;
  temp_ssd?: number | null; temp_mb?: number | null;
}

const DISK_COLORS = ["#a855f7", "#7c3aed", "#6d28d9", "#5b21b6"];

// ── Helpers ──
function fmtVal(v: number | null, d = 1) { return v == null ? "—" : v.toFixed(d); }
function fmtTemp(t: number | null) { return t == null ? "—" : `${t}°C`; }
function tempCls(t: number | null) {
  if (t == null) return "ok";
  if (t >= 80) return "hot";
  if (t >= 68) return "warm";
  return "ok";
}
function fmtUptime(s: number | null) {
  if (!s) return "—";
  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
}

function parseData(d: SensorData): SensorData {
  if (typeof d.cpu_cores === "string") { try { d.cpu_cores = JSON.parse(d.cpu_cores); } catch { /* ignore */ } }
  if (typeof d.storage === "string") { try { d.storage = JSON.parse(d.storage); } catch { /* ignore */ } }
  return d;
}

// ── Components ──

function TempBadge({ temp, id }: { temp: number | null; id?: string }) {
  const cls = tempCls(temp);
  return (
    <div id={id} className={`mtemp mtemp-${cls}`}>
      <IconTemperature size={13} />
      <span>{fmtTemp(temp)}</span>
    </div>
  );
}

function MetricCard({ label, icon, value, unit, sub, percent, children }: {
  label: string; icon: React.ReactNode;
  value: number | null; unit: string; sub: string; percent: number | null;
  children?: React.ReactNode;
}) {
  return (
    <div className="metric-card">
      <div className="metric-label">{icon} {label}</div>
      {children}
      <div className="metric-value-row">
        <span className="metric-value">{value != null ? value.toFixed(0) : "—"}</span>
        <span className="metric-unit">{unit}</span>
      </div>
      <div className="metric-sub">{sub || "—"}</div>
      <div className="bar-track">
        <div className="bar-fill" style={{ width: `${percent ?? 0}%` }} />
      </div>
    </div>
  );
}

function DiskCard({ disks }: { disks: Disk[] | null }) {
  const list = disks || [];
  return (
    <div className="metric-card">
      <div className="metric-label"><IconServer size={16} /> Discos</div>
      <div className="disk-list">
        {list.length === 0 && <div className="info-item"><span className="info-label">Nenhum disco detectado</span></div>}
        {list.map((d, i) => (
          <div key={d.label} className="disk-item">
            <IconServer size={18} className="disk-icon" />
            <div className="disk-info">
              <div className="disk-name">{d.label} {d.usage_percent >= 85 ? "⚠️" : ""}</div>
              <div className="disk-bar">
                <div className="disk-bar-fill" style={{ width: `${d.usage_percent}%`, background: `linear-gradient(90deg, var(--p4), ${DISK_COLORS[i % DISK_COLORS.length]})` }} />
              </div>
            </div>
            <span className="disk-pct">{d.usage_percent}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function InfoList({ uptime, dl, ul, watts, procs }: {
  uptime: string; dl: number | null; ul: number | null;
  watts: number | null; procs: number | null;
}) {
  const items = [
    { icon: <IconClock size={16} />, label: "Uptime", val: uptime },
    { icon: <IconArrowDown size={16} />, label: "Download", val: dl != null ? `${dl} MB/s` : "—" },
    { icon: <IconArrowUp size={16} />, label: "Upload", val: ul != null ? `${ul} MB/s` : "—" },
    { icon: <IconBolt size={16} />, label: "Energia", val: watts != null ? `${watts}W` : "—" },
    { icon: <IconApps size={16} />, label: "Processos", val: procs != null ? `${procs}` : "—" },
  ];
  return (
    <div className="card">
      <div className="info-header"><span className="title">Sistema</span><span className="badge badge-purple">Info</span></div>
      <div className="info-list">
        {items.map(it => (
          <div key={it.label} className="info-item">
            <div className="info-label">{it.icon} {it.label}</div>
            <span className="info-val">{it.val}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function MidGrid({ cpuH, ramH, uptime, dl, ul, watts, procs }: {
  cpuH: (number | null)[]; ramH: (number | null)[];
  uptime: string; dl: number | null; ul: number | null;
  watts: number | null; procs: number | null;
}) {
  const ref = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<ChartJS | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const ctx = ref.current.getContext("2d");
    if (!ctx) return;

    const g1 = ctx.createLinearGradient(0, 0, 0, 200);
    g1.addColorStop(0, "rgba(168,85,247,.3)"); g1.addColorStop(1, "rgba(168,85,247,0)");
    const g2 = ctx.createLinearGradient(0, 0, 0, 200);
    g2.addColorStop(0, "rgba(109,40,217,.25)"); g2.addColorStop(1, "rgba(109,40,217,0)");

    if (chartRef.current) chartRef.current.destroy();

    chartRef.current = new ChartJS(ctx, {
      type: "line",
      data: {
        labels: cpuH.map((_, i) => `${i}s`),
        datasets: [
          { label: "CPU", data: cpuH, borderColor: "#a855f7", backgroundColor: g1, fill: true, tension: 0.4, pointRadius: 0, pointHoverRadius: 4, borderWidth: 2 },
          { label: "RAM", data: ramH, borderColor: "#6d28d9", backgroundColor: g2, fill: true, tension: 0.4, pointRadius: 0, pointHoverRadius: 4, borderWidth: 2 },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false, animation: { duration: 0 },
        plugins: { legend: { display: false }, tooltip: { mode: "index", intersect: false, backgroundColor: "#1a1a2e", titleColor: "#e8e8f0", bodyColor: "#6b6b80", borderColor: "rgba(139,92,247,.15)", borderWidth: 1, padding: 10, usePointStyle: true } },
        scales: {
          x: { display: false },
          y: { min: 0, max: 100, grid: { color: "rgba(139,92,247,.06)" }, ticks: { color: "#4a4a5e", font: { family: "'IBM Plex Mono', monospace", size: 10 }, stepSize: 25, callback: (v: number | string) => `${v}%` } },
        },
        interaction: { mode: "nearest", axis: "x", intersect: false },
      },
    });

    return () => { if (chartRef.current) { chartRef.current.destroy(); chartRef.current = null; } };
  }, [cpuH, ramH]);

  return (
    <div className="mid-grid">
      <div className="card">
        <div className="chart-header">
          <span className="title">Histórico — CPU & RAM</span>
          <span className="badge badge-purple">Tempo real</span>
        </div>
        <div className="chart-legend">
          <div className="legend-item"><div className="legend-dot" style={{ background: "var(--p1)" }} /><span>CPU</span></div>
          <div className="legend-item"><div className="legend-dot" style={{ background: "var(--p3)" }} /><span>RAM</span></div>
        </div>
        <div className="chart-wrap"><canvas ref={ref} /></div>
      </div>
      <InfoList uptime={uptime} dl={dl} ul={ul} watts={watts} procs={procs} />
    </div>
  );
}

function ProcessList({ processes }: { processes: Proc[] }) {
  const colors = ["#a855f7", "#7c3aed", "#6d28d9", "#5b21b6", "#4c1d95"];
  return (
    <div className="card">
      <div className="sec-header">
        <span className="title">Top processos</span>
        <span className="badge badge-purple">CPU · MEM</span>
      </div>
      <div className="proc-hdr">
        <span>Processo</span>
        <div className="right"><span>CPU</span><span>MEM</span></div>
      </div>
      <div className="proc-list">
        {processes.slice(0, 5).map((p, i) => (
          <div key={i} className="proc-item">
            <span className="proc-rank">{i + 1}</span>
            <div className="proc-dot" style={{ background: colors[i % 5] }} />
            <span className="proc-name" title={p.name}>{p.name}</span>
            <span className="proc-cpu">{p.cpu_percent.toFixed(1)}%</span>
            <span className="proc-mem">{p.mem_mb} MB</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TempGrid({ cpuT, gpuT, ssdT, mbT }: {
  cpuT: number | null; gpuT: number | null; ssdT: number | null; mbT: number | null;
}) {
  const temps = [
    { id: "tCpu", label: "CPU Package", val: cpuT },
    { id: "tGpu", label: "GPU Core", val: gpuT },
    { id: "tSsd", label: "Disco SSD", val: ssdT },
    { id: "tMb", label: "Placa-mãe", val: mbT },
  ];
  return (
    <div className="card">
      <div className="sec-header">
        <span className="title">Temperaturas</span>
        <span className="badge badge-purple">Monitorando</span>
      </div>
      <div className="temp-grid">
        {temps.map(t => (
          <div key={t.id} className="temp-item">
            <div id={t.id} className={`temp-val t-${tempCls(t.val)}`}>{fmtTemp(t.val)}</div>
            <div className="temp-lbl">{t.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Mock ──
const MOCK: SensorData = {
  status: "online", hostname: "DESKTOP-ABC", uptime_sec: 24061,
  cpu_usage: 12.5, cpu_temp: 45.9, cpu_cores: [2.1,1.5,3.0,0.8,1.2,2.5,1.8,0.5,1.1,2.0,0.9,1.3],
  gpu_usage: 6.0, gpu_temp: 55.0, vram_used: 2048, vram_total: 4096, gpu_vendor: "amd",
  ram_usage: 46, ram_used: 15.7, ram_total: 34.3,
  storage: [
    { label: "C:", used_gb: 195.6, total_gb: 255.4, usage_percent: 77 },
    { label: "E:", used_gb: 883.4, total_gb: 1000.2, usage_percent: 88 },
    { label: "F:", used_gb: 714.4, total_gb: 1000.2, usage_percent: 71 },
  ],
  dl_speed: null, ul_speed: null, watts: null, process_count: 142,
  processes: [
    { name: "chrome.exe", cpu_percent: 3.2, mem_mb: 450 },
    { name: "explorer.exe", cpu_percent: 1.8, mem_mb: 120 },
    { name: "node.exe", cpu_percent: 1.2, mem_mb: 280 },
    { name: "python.exe", cpu_percent: 0.8, mem_mb: 95 },
    { name: "vscode.exe", cpu_percent: 0.5, mem_mb: 340 },
  ],
  temp_ssd: 38, temp_mb: 42,
};

const HLEN = 30;

// ── Main ──
export default function Home() {
  const [data, setData] = useState<SensorData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState<"live" | "mock" | "err">("mock");
  const cpuRef = useRef<(number | null)[]>([]);
  const ramRef = useRef<(number | null)[]>([]);

  const sourceRef = useRef<"live" | "mock" | "err">("mock");
  const dataRef = useRef<SensorData | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch("/api/sensors", { cache: "no-store", signal: AbortSignal.timeout(8000) });
      if (!res.ok) throw new Error();
      const json = parseData(await res.json());
      setData(json);
      dataRef.current = json;
      cpuRef.current = [...cpuRef.current.slice(-(HLEN - 1)), json.cpu_usage];
      ramRef.current = [...ramRef.current.slice(-(HLEN - 1)), json.ram_usage];
      sourceRef.current = "live";
      setSource("live"); setError(null);
    } catch {
      if (sourceRef.current !== "live" && sourceRef.current !== "mock") {
        sourceRef.current = "mock";
        setSource("mock"); setData(MOCK);
        cpuRef.current = [...cpuRef.current.slice(-(HLEN - 1)), MOCK.cpu_usage];
        ramRef.current = [...ramRef.current.slice(-(HLEN - 1)), MOCK.ram_usage];
      } else if (sourceRef.current === "live") {
        setError("Timeout — último dado real mantido");
        const last = dataRef.current;
        cpuRef.current = [...cpuRef.current.slice(-(HLEN - 1)), last?.cpu_usage ?? null];
        ramRef.current = [...ramRef.current.slice(-(HLEN - 1)), last?.ram_usage ?? null];
      }
    } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    // Pre-fill history
    for (let i = 0; i < HLEN; i++) {
      cpuRef.current.push(8 + Math.random() * 18);
      ramRef.current.push(38 + Math.random() * 15);
    }
    fetchData();
    const id = setInterval(fetchData, 2000);
    return () => clearInterval(id);
  }, [fetchData]);

  const d = data || MOCK;
  const cores = d.cpu_cores
    ? (Array.isArray(d.cpu_cores) ? d.cpu_cores.length : String(d.cpu_cores).split(",").length)
    : null;
  const procs = (d.processes && d.processes.length ? d.processes : MOCK.processes) as Proc[];

  return (
    <div className="app">

      {/* Topbar */}
      <div className="topbar">
        <div className="logo">
          <span>SY</span><span className="logo-dot" /><span>MONITOR</span>
        </div>
        <div className="topbar-right">
          <span className="hostname">{d.hostname || "—"}</span>
          <div className="live-badge">
            <div className="dot" />
            <span className="txt">LIVE</span>
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="status-bar">
        <div className="status-source">
          <div className={`sdot sdot-${source}`} />
          <span>{source === "live" ? "Dados ao vivo · API" : source === "mock" ? "Modo demonstração (mock)" : "Erro de conexão"}</span>
        </div>
        <span>{new Date().toLocaleTimeString("pt-BR")}</span>
      </div>

      {/* Error */}
      {!loading && error && (
        <div className="card" style={{ textAlign: "center", padding: 28, borderColor: "rgba(239,68,68,.25)", background: "rgba(239,68,68,.04)", marginBottom: 16 }}>
          <div style={{ fontSize: 28, marginBottom: 10 }}>⚠️</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#ef4444", marginBottom: 4 }}>Erro ao carregar dados</div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Verifique se o backend está rodando</div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="skeleton" style={{ height: 100 }} />
          <div className="skeleton" style={{ height: 200 }} />
          <div className="skeleton" style={{ height: 160 }} />
        </div>
      )}

      {/* Dashboard */}
      {!loading && !error && d && (
        <>
          {/* Metrics Grid */}
          <div className="metrics-grid">
            <MetricCard
              label="CPU" icon={<IconCpu size={16} />}
              value={d.cpu_usage} unit="%"
              sub={cores ? `${cores} núcleos` : ""}
              percent={d.cpu_usage}
            >
              <TempBadge temp={d.cpu_temp} />
            </MetricCard>

            <MetricCard
              label="RAM" icon={<IconDatabase size={16} />}
              value={d.ram_usage} unit="%"
              sub={d.ram_total != null ? `${fmtVal(d.ram_used)} / ${fmtVal(d.ram_total)} GB` : ""}
              percent={d.ram_usage}
            />

            <MetricCard
              label="GPU" icon={<IconDeviceDesktop size={16} />}
              value={d.gpu_usage} unit="%"
              sub={d.vram_total != null ? `${fmtVal(d.vram_used)} / ${fmtVal(d.vram_total)} MB${d.gpu_vendor ? ` · ${d.gpu_vendor.toUpperCase()}` : ""}` : ""}
              percent={d.gpu_usage}
            >
              <TempBadge temp={d.gpu_temp} />
            </MetricCard>

            <DiskCard disks={d.storage} />
          </div>

          {/* Mid Grid */}
          <MidGrid
            cpuH={cpuRef.current} ramH={ramRef.current}
            uptime={fmtUptime(d.uptime_sec)}
            dl={d.dl_speed ?? null} ul={d.ul_speed ?? null}
            watts={d.watts ?? null} procs={d.process_count ?? null}
          />

          {/* Bottom Grid */}
          <div className="bot-grid">
            <ProcessList processes={procs} />
            <TempGrid cpuT={d.cpu_temp} gpuT={d.gpu_temp} ssdT={d.temp_ssd ?? null} mbT={d.temp_mb ?? null} />
          </div>
        </>
      )}

      {/* Footer */}
      <div className="footer"><p>SYS.MONITOR · atualiza a cada 5s</p></div>
    </div>
  );
}
