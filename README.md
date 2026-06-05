# PC Dashboard Monitor

[![Live Demo](https://img.shields.io/badge/Live-pc--dashboard--monitor.vercel.app-22d3a5?style=for-the-badge&logo=vercel&logoColor=white)](https://pc-dashboard-monitor.vercel.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-534AB7?style=for-the-badge)](LICENSE)
[![Next.js](https://img.shields.io/badge/Next.js-16-000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![Supabase](https://img.shields.io/badge/Supabase-1D9E75?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)

Dashboard de monitoramento de PC em tempo real, acessível de qualquer lugar. Coleta métricas de hardware do seu PC e exibe em um dashboard web com atualização a cada 5 segundos.

---

## Arquitetura

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Seu PC     │     │   Supabase   │     │   Vercel     │
│  server.py   │────▶│  sensor_     │◀────│  Next.js 16  │
│  coleta +    │     │  readings    │     │  dashboard   │
│  push HTTP   │     │  (Postgres)  │     │  /api/sensors│
└──────────────┘     └──────────────┘     └──────────────┘
```

1. **Backend** (`server.py`) — roda no seu PC, coleta métricas via psutil + LibreHardwareMonitor, push para Supabase
2. **API** (`/api/sensors`) — rota Next.js lê do Supabase REST API
3. **Frontend** (Next.js 16) — dashboard com gauges, gráficos Chart.js, processos, temperaturas

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Coleta | Python 3.11+, psutil, LibreHardwareMonitor (CSV) |
| Banco | Supabase (PostgreSQL) |
| Frontend | Next.js 16, React 19, TypeScript, Chart.js, Tabler Icons |
| Deploy | Vercel |
| Build | PyInstaller (`.exe` do backend) |

---

## Pré-requisitos

- **Python 3.11+** — backend coletor
- **Node.js 18+** — frontend Next.js
- **LibreHardwareMonitor** — leitura de temperaturas ([download](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases))
- **Conta Supabase** — banco de dados ([supabase.com](https://supabase.com))
- **Conta Vercel** — deploy do frontend ([vercel.com](https://vercel.com))

---

## Instalação

### 1. Clone

```bash
git clone https://github.com/ChrisKauet/PC-Dashboard-Monitor.git
cd PC-Dashboard-Monitor
```

### 2. Supabase

Crie a tabela `sensor_readings`:

```sql
CREATE TABLE sensor_readings (
  id BIGSERIAL PRIMARY KEY,
  recorded_at TIMESTAMPTZ DEFAULT NOW(),
  cpu_usage REAL, cpu_temp REAL, cpu_cores TEXT,
  gpu_usage REAL, gpu_temp REAL, vram_used REAL, vram_total REAL,
  gpu_fan_rpm REAL, gpu_vendor TEXT,
  ram_used REAL, ram_total REAL, ram_usage REAL,
  storage TEXT, uptime_sec INTEGER, hostname TEXT
);
```

### 3. Backend

```bash
# Dependências
pip install psutil supabase python-dotenv

# Configure as credenciais
cp .env.example .env
# Edite .env com suas chaves do Supabase

# Execute
python server.py
```

O servidor inicia em `http://localhost:8080` e pusha para Supabase a cada 5s.

**Build .exe (opcional):**

```bash
pip install pyinstaller
pyinstaller --onefile --console server.py
```

### 4. Frontend

```bash
cd dashboard
npm install
npm run dev      # http://localhost:3000
npm run build    # Build de produção
```

### 5. Deploy Vercel

Conecte o repositório no [Vercel](https://vercel.com/new) e configure as variáveis de ambiente:

| Variável | Descrição |
|----------|-----------|
| `NEXT_PUBLIC_SUPABASE_URL` | URL do projeto Supabase |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Chave anônima do Supabase |
| `SUPABASE_SERVICE_KEY` | Chave service-role (bypassa RLS) |

---

## Variáveis de Ambiente

```env
# Supabase (obrigatório)
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-service-role-key

# Backend (opcional, defaults abaixo)
SENSOR_PORT=8080
SENSOR_COOLDOWN=5.0
```

---

## API

### `GET /api/sensors`

Retorna o último registro de métricas.

```json
{
  "status": "online",
  "cpu_usage": 12.5,
  "cpu_temp": 45.9,
  "gpu_usage": 6.0,
  "gpu_temp": 55.0,
  "ram_used": 15.7,
  "ram_total": 34.3,
  "ram_usage": 46,
  "uptime_sec": 24061,
  "hostname": "DESKTOP-ABC",
  "gpu_vendor": "amd"
}
```

---

## Métricas

| Métrica | Campo | Fonte | Componente |
|---------|-------|-------|------------|
| CPU Usage | `cpu_usage` | psutil | MetricCard + Chart |
| CPU Temp | `cpu_temp` | LHM CSV | TempGrid |
| RAM | `ram_used/total/usage` | psutil | MetricCard + Chart |
| GPU Usage | `gpu_usage` | WMI Get-Counter | MetricCard |
| GPU Temp | `gpu_temp` | LHM CSV | TempGrid |
| VRAM | `vram_used/total` | WMI | MetricCard |
| Disco | `storage` (JSON) | psutil | MetricCard |
| Uptime | `uptime_sec` | psutil | InfoList |
| Hostname | `hostname` | socket | Topbar |

> Campos como `dl_speed`, `ul_speed`, `watts`, `process_count`, `processes`, `temp_ssd`, `temp_mb` ainda não são coletados — aparecem como "—".

---

## Tema

Light/dark automático via `prefers-color-scheme`.

| Cor | Light | Dark | Uso |
|-----|-------|------|-----|
| Green | `#1D9E75` | `#5DCAA5` | CPU |
| Purple | `#534AB7` | `#AFA9EC` | RAM |
| Orange | `#D85A30` | `#F0997B` | GPU |
| Amber | `#BA7517` | `#FAC775` | Disco |

Temperaturas: <68°C verde · 68-79°C amber · ≥80°C orange

---

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Temperaturas null | Verifique se o LibreHardwareMonitor está rodando |
| GPU vendor "UNKNOWN" | Normal para GPUs virtuais (Parsec) |
| Dados não aparecem | Verifique `.env` e se o `server.py` está pushando para Supabase |
| Build local falha | Use `npx tsc --noEmit` para debug; o build Vercel funciona independentemente |

---

## Licença

[MIT](LICENSE)
