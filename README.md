# PC Dashboard Monitor

Dashboard de monitoramento de PC em tempo real, acessível via internet. Coleta métricas de hardware do seu PC e exibe em um dashboard web com atualização a cada 5 segundos.

**🌐 Live:** [pc-dashboard-monitor.vercel.app](https://pc-dashboard-monitor.vercel.app/)

---

## Arquitetura

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Seu PC        │     │   Supabase   │     │   Vercel        │
│   (server.py)   │────▶│   (Postgres) │◀────│   (Next.js 16)  │
│   Coleta dados  │     │   sensor_    │     │   Dashboard web │
│   + Push HTTP   │     │   readings   │     │   /api/sensors  │
└─────────────────┘     └──────────────┘     └─────────────────┘
```

1. **Backend** (`server.py`): roda no seu PC, coleta métricas via psutil/LibreHardwareMonitor e faz push para Supabase
2. **API** (`/api/sensors`): rota Next.js que lê do Supabase REST API
3. **Frontend** (Next.js 16): dashboard com gauges, gráficos Chart.js, lista de processos, temperaturas

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| **Coleta** | Python 3.11+, psutil, LibreHardwareMonitor (CSV) |
| **Banco** | Supabase (PostgreSQL) |
| **API** | Next.js 16 API Routes |
| **Frontend** | Next.js 16, React 19, TypeScript, Chart.js, Tabler Icons |
| **Deploy** | Vercel |
| **Build** | PyInstaller (`.exe` do backend) |

---

## Estrutura do Projeto

```
PC-Dashboard-Monitor/
├── server.py                 # Backend coletor (roda no PC)
├── .env                      # Credenciais Supabase (não versionado)
├── .env.example              # Template de variáveis de ambiente
├── dashboard/                # Frontend Next.js
│   ├── app/
│   │   ├── page.tsx          # Página principal do dashboard
│   │   ├── layout.tsx        # Layout com fontes (IBM Plex Mono, DM Sans)
│   │   ├── globals.css       # Estilos + light/dark theme
│   │   └── api/sensors/route.ts  # Proxy Supabase REST API
│   ├── components/
│   │   ├── Topbar.tsx        # Logo SYS.MONITOR + LIVE badge + hostname
│   │   ├── MetricCard.tsx    # Card individual de métrica
│   │   ├── MetricsGrid.tsx   # Grid 4 colunas (CPU, RAM, GPU, Disco)
│   │   ├── MidGrid.tsx       # Gráfico Chart.js + InfoList
│   │   ├── InfoList.tsx      # Lista de info do sistema
│   │   ├── ProcessList.tsx   # Top processos (CPU + MEM)
│   │   ├── TempGrid.tsx      # Grid 2x2 temperaturas
│   │   └── BottomGrid.tsx    # ProcessList + TempGrid
│   ├── package.json
│   ├── next.config.ts
│   ├── vercel.json           # Config de deploy Vercel
│   └── tsconfig.json
├── dist/                     # .exe compilado (PyInstaller)
└── README.md
```

---

## Métricas Coletadas

| Métrica | Campo Supabase | Fonte | Componente |
|---------|---------------|-------|------------|
| CPU Usage | `cpu_usage` | psutil | MetricCard + Chart |
| CPU Temp | `cpu_temp` | LHM CSV | TempGrid |
| CPU Cores | `cpu_cores` | psutil | MetricCard (subtitle) |
| RAM Used | `ram_used` | psutil | MetricCard + Chart |
| RAM Total | `ram_total` | psutil | MetricCard |
| RAM Usage | `ram_usage` | psutil | MetricCard |
| GPU Usage | `gpu_usage` | Get-Counter (WMI) | MetricCard |
| GPU Temp | `gpu_temp` | LHM CSV | TempGrid |
| VRAM Used | `vram_used` | WMI | MetricCard (subtitle) |
| VRAM Total | `vram_total` | WMI | MetricCard (subtitle) |
| Storage | `storage` (JSON) | psutil | MetricCard |
| Uptime | `uptime_sec` | psutil | InfoList |
| Hostname | `hostname` | socket | Topbar |
| DL Speed | `dl_speed` | — | InfoList |
| UL Speed | `ul_speed` | — | InfoList |
| Watts | `watts` | — | InfoList |
| Process Count | `process_count` | — | InfoList |
| Processes | `processes` (JSON) | — | ProcessList |
| SSD Temp | `temp_ssd` | — | TempGrid |
| MB Temp | `temp_mb` | — | TempGrid |

> Campos marcados com "—" ainda não são coletados pelo backend. Aparecem como "—" no dashboard.

---

## Configuração

### 1. Variáveis de Ambiente

Copie `.env.example` para `.env` e preencha:

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-service-role-key
SENSOR_PORT=8080
SENSOR_COOLDOWN=5.0
```

### 2. Supabase

Crie a tabela `sensor_readings`:

```sql
CREATE TABLE sensor_readings (
  id BIGSERIAL PRIMARY KEY,
  recorded_at TIMESTAMPTZ DEFAULT NOW(),
  cpu_usage REAL,
  cpu_temp REAL,
  cpu_cores TEXT,
  gpu_usage REAL,
  gpu_temp REAL,
  vram_used REAL,
  vram_total REAL,
  gpu_fan_rpm REAL,
  gpu_vendor TEXT,
  ram_used REAL,
  ram_total REAL,
  ram_usage REAL,
  storage TEXT,
  uptime_sec INTEGER,
  hostname TEXT
);
```

### 3. LibreHardwareMonitor (obrigatório para temperaturas)

1. Baixe em [LibreHardwareMonitor Releases](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases)
2. Extraia em `C:\Users\Kauezin\Downloads\LibreHardwareMonitor\`
3. Execute `LibreHardwareMonitor.exe` (modo administrador)
4. O LHM salva logs CSV automaticamente — o `server.py` lê o CSV mais recente

### 4. Backend (server.py)

```bash
# Desenvolvimento
python server.py

# Build .exe
pip install pyinstaller
pyinstaller --onefile --console server.py
```

O servidor inicia em `http://localhost:8080` e faz push para Supabase a cada 5s.

### 5. Frontend (dashboard/)

```bash
cd dashboard
npm install
npm run dev      # http://localhost:3000
npm run build    # Build de produção
```

### 6. Deploy Vercel

O deploy é automático via GitHub. Conecte o repositório no [Vercel](https://vercel.com/new) e configure as variáveis de ambiente:

```
NEXT_PUBLIC_SUPABASE_URL=https://seu-projeto.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sua-anon-key
SUPABASE_SERVICE_KEY=sua-service-role-key
```

---

## API

### `GET /api/sensors`

Retorna o último registro de métricas do Supabase.

**Response (200):**
```json
{
  "status": "online",
  "cpu_usage": 12.5,
  "cpu_temp": 45.9,
  "cpu_cores": "[2.1, 1.5, 3.0, ...]",
  "gpu_usage": 6.0,
  "gpu_temp": 55.0,
  "vram_used": 2048,
  "vram_total": 4096,
  "ram_used": 15.7,
  "ram_total": 34.3,
  "ram_usage": 46,
  "storage": "[{\"label\":\"C:\",\"used_gb\":195.6,\"total_gb\":255.4,\"usage_percent\":77}]",
  "uptime_sec": 24061,
  "hostname": "DESKTOP-ABC",
  "gpu_vendor": "amd"
}
```

---

## Tema

O dashboard suporta **light** e **dark** mode automático via `prefers-color-scheme`.

| Cor | Light | Dark | Uso |
|-----|-------|------|-----|
| Green | `#1D9E75` | `#5DCAA5` | CPU, badges |
| Purple | `#534AB7` | `#AFA9EC` | RAM, chart |
| Orange | `#D85A30` | `#F0997B` | GPU, processos |
| Amber | `#BA7517` | `#FAC775` | Disco, warm temp |
| Blue | `#185FA5` | `#85B7EB` | Info badge |

**Temperaturas:** <68°C verde · 68-79°C amber · ≥80°C orange

---

## Responsivo

- **> 700px**: 4 colunas métricas, mid/bottom grid lado a lado
- **≤ 700px**: 2 colunas métricas, grids empilham, hostname oculto
- **≤ 420px**: valores menores, grid 2x2 mantido

---

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Temperaturas null | Verifique se o LibreHardwareMonitor está rodando |
| GPU vendor "UNKNOWN" | Normal para GPUs virtuais (Parsec); GPU real aparece quando ativa |
| Build local falha | Use `npx tsc --noEmit` para debug; o build Vercel funciona independentemente |
| Dados não aparecem | Verifique `.env` e se o `server.py` está rodando + pushando para Supabase |

---

## Licença

MIT
