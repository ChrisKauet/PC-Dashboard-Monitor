# Prompt: PC Sensor Dashboard — Acesso Remoto Completo

## Visão Geral da Arquitetura

```
[PC com Windows]                    [Nuvem]                    [Celular / qualquer browser]
  server.py                                                     
  - lê sensores           →  Supabase (PostgreSQL)  ←        Next.js no Vercel
  - envia dados a cada       tabela: sensor_readings            - busca último registro
    5 segundos via           (histórico ilimitado)              - exibe dashboard ao vivo
    Supabase client                                             - atualiza a cada 5s
```

**Por que não WebSocket direto?** O PC fica atrás de NAT/roteador doméstico — não tem IP público fixo. A solução correta é o PC **empurrar** dados para o Supabase (saída), e o Vercel **ler** do Supabase (entrada). Nenhuma porta precisa ser aberta no roteador.

---

## Estrutura de Arquivos a Gerar

```
C:\SensorDash\
├── server.py               # Coletor local — roda no PC 24/7
├── .env                    # Credenciais Supabase (NÃO commitar)
├── requirements.txt        # Dependências Python
│
├── dashboard/              # Projeto Next.js → deploy no Vercel
│   ├── .env.local          # Credenciais Supabase (NÃO commitar)
│   ├── package.json
│   ├── next.config.js
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx        # Dashboard principal
│   │   └── api/
│   │       └── sensors/
│   │           └── route.ts  # API Route que lê do Supabase
│   └── components/
│       ├── GaugeCard.tsx
│       ├── BarCard.tsx
│       ├── StorageCard.tsx
│       └── StatusBadge.tsx
│
└── .gitignore
```

---

## PARTE 1 — Banco de Dados (Supabase)

### Configuração inicial (fazer manualmente antes de gerar código)

1. Criar projeto em https://supabase.com
2. Ir em **SQL Editor** e executar:

```sql
-- Tabela principal de leituras
CREATE TABLE sensor_readings (
  id          BIGSERIAL PRIMARY KEY,
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  cpu_usage   FLOAT,
  cpu_temp    FLOAT,
  cpu_cores   JSONB,        -- array de floats ex: [12.0, 45.0, ...]
  gpu_usage   FLOAT,
  gpu_temp    FLOAT,
  vram_used   FLOAT,        -- MB
  vram_total  FLOAT,        -- MB
  gpu_fan_rpm INT,
  ram_used    FLOAT,        -- GB
  ram_total   FLOAT,        -- GB
  ram_usage   FLOAT,        -- percent
  storage     JSONB,        -- array de objetos de disco
  uptime_sec  INT,
  hostname    TEXT
);

-- Index para buscar o registro mais recente rapidamente
CREATE INDEX idx_sensor_readings_recorded_at ON sensor_readings (recorded_at DESC);

-- Limpeza automática: manter só as últimas 24h (evitar crescimento infinito)
CREATE OR REPLACE FUNCTION delete_old_sensor_readings()
RETURNS TRIGGER AS $$
BEGIN
  DELETE FROM sensor_readings
  WHERE recorded_at < NOW() - INTERVAL '24 hours';
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_cleanup_sensors
AFTER INSERT ON sensor_readings
EXECUTE FUNCTION delete_old_sensor_readings();
```

3. Ir em **Project Settings → API** e anotar:
   - `Project URL` → ex: `https://xxxx.supabase.co`
   - `anon public key` → chave pública (usada no Next.js)
   - `service_role key` → chave privada (usada APENAS no server.py — nunca expor)

---

## PARTE 2 — Coletor Local (`server.py`)

### `C:\SensorDash\requirements.txt`

```
psutil
pyamdgpuinfo
supabase
python-dotenv
```

### `C:\SensorDash\.env`

```env
SUPABASE_URL=https://SEU_PROJETO.supabase.co
SUPABASE_SERVICE_KEY=sua_service_role_key_aqui
PUSH_INTERVAL_SECONDS=5
```

### `C:\SensorDash\server.py`

Gere o arquivo completo com a seguinte lógica:

```python
# Imports
import time, socket, os
from dotenv import load_dotenv
import psutil
from supabase import create_client

load_dotenv()

# Inicializar cliente Supabase com service_role key
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
INTERVAL = int(os.getenv("PUSH_INTERVAL_SECONDS", 5))

# Tentar importar pyamdgpuinfo — AMD RX 7600
AMD_AVAILABLE = False
try:
    import pyamdgpuinfo
    AMD_AVAILABLE = True
except Exception:
    print("[AVISO] pyamdgpuinfo não disponível — dados de GPU serão null")

def read_gpu():
    if not AMD_AVAILABLE:
        return dict(gpu_usage=None, gpu_temp=None, vram_used=None, vram_total=None, gpu_fan_rpm=None)
    try:
        gpu = pyamdgpuinfo.get_gpu(0)
        return {
            "gpu_usage":   round(gpu.query_load() * 100, 1),
            "gpu_temp":    round(gpu.query_temperature(), 1),
            "vram_used":   round(gpu.query_vram_usage() / 1e6, 1),
            "vram_total":  round(gpu.memory_info["vram_size"] / 1e6, 1),
            "gpu_fan_rpm": None,
        }
    except Exception as e:
        print(f"[GPU erro] {e}")
        return dict(gpu_usage=None, gpu_temp=None, vram_used=None, vram_total=None, gpu_fan_rpm=None)

def read_cpu_temp():
    # psutil.sensors_temperatures() não funciona no Windows nativamente.
    # Tentar chaves: 'coretemp', 'k10temp', 'cpu_thermal'
    # Se nenhuma disponível, retornar None.
    try:
        temps = psutil.sensors_temperatures()
        for key in ("coretemp", "k10temp", "cpu_thermal"):
            if key in temps and temps[key]:
                return round(temps[key][0].current, 1)
    except Exception:
        pass
    return None

def read_storage():
    discos = []
    for part in psutil.disk_partitions():
        if "cdrom" in part.opts or not part.fstype:
            continue
        try:
            u = psutil.disk_usage(part.mountpoint)
            discos.append({
                "label":   part.device.replace("\\", ""),
                "used_gb": round(u.used / 1e9, 1),
                "total_gb": round(u.total / 1e9, 1),
                "usage_percent": u.percent,
            })
        except PermissionError:
            pass
    return discos

def collect():
    vm = psutil.virtual_memory()
    cores = psutil.cpu_percent(interval=0.3, percpu=True)
    gpu = read_gpu()

    return {
        "cpu_usage":  round(psutil.cpu_percent(interval=0.3), 1),
        "cpu_temp":   read_cpu_temp(),
        "cpu_cores":  cores,
        "ram_used":   round(vm.used / 1e9, 2),
        "ram_total":  round(vm.total / 1e9, 2),
        "ram_usage":  vm.percent,
        "storage":    read_storage(),
        "uptime_sec": int(time.time() - psutil.boot_time()),
        "hostname":   socket.gethostname(),
        **gpu,
    }

def main():
    print(f"[SensorDash] Iniciando. Enviando para Supabase a cada {INTERVAL}s...")
    while True:
        try:
            data = collect()
            supabase.table("sensor_readings").insert(data).execute()
            print(f"[OK] {data['hostname']} | CPU {data['cpu_usage']}% | GPU {data['gpu_usage']}%")
        except Exception as e:
            print(f"[ERRO ao enviar] {e}")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
```

### Instalação e execução

```bat
cd C:\SensorDash
pip install -r requirements.txt
python server.py
```

Para rodar em segundo plano no Windows sem janela aberta:

```bat
pythonw server.py
```

Ou criar um serviço Windows com NSSM (opcional — instruir o modelo a perguntar ao usuário se deseja isso).

---

## PARTE 3 — Frontend Next.js (`dashboard/`)

### Tecnologias

- **Next.js 14** com App Router e TypeScript
- **Tailwind CSS** para estilo
- **@supabase/supabase-js** no lado do servidor (API Route)
- Polling client-side a cada **5 segundos** via `useEffect` + `setInterval`
- Deploy no **Vercel** (zero config para Next.js)

### Inicialização do projeto

```bash
cd C:\SensorDash
npx create-next-app@latest dashboard --typescript --tailwind --app --no-src-dir
cd dashboard
npm install @supabase/supabase-js
```

### `dashboard/.env.local`

```env
NEXT_PUBLIC_SUPABASE_URL=https://SEU_PROJETO.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sua_anon_key_aqui
```

> Usar a **anon key** aqui (pública). A service_role key NUNCA vai para o frontend.

### `dashboard/app/api/sensors/route.ts`

API Route server-side que busca o registro mais recente:

```typescript
import { createClient } from '@supabase/supabase-js'
import { NextResponse } from 'next/server'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export async function GET() {
  const { data, error } = await supabase
    .from('sensor_readings')
    .select('*')
    .order('recorded_at', { ascending: false })
    .limit(1)
    .single()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  // Calcular idade do dado para indicar se o PC está online
  const ageSeconds = (Date.now() - new Date(data.recorded_at).getTime()) / 1000

  return NextResponse.json({ ...data, age_seconds: ageSeconds })
}
```

### `dashboard/app/page.tsx`

Página principal do dashboard. Implementar com a seguinte lógica:

- `useSensors()` hook: faz fetch para `/api/sensors` a cada 5s via `setInterval`
- Status do PC: se `age_seconds > 15` → "PC Offline" (vermelho); senão → "Ao Vivo" (verde)
- Renderizar os componentes: `GaugeCard`, `BarCard`, `StorageCard`, `StatusBadge`
- Layout mobile-first: `max-w-lg mx-auto px-4`, coluna única

### Componentes a implementar

#### `GaugeCard.tsx`
- Props: `title`, `value` (0–100), `color` (hex), `unit` (ex: "%"), `temp?`, `subtitle?`
- Gauge circular SVG (stroke-dasharray trick)
- Temperatura com cor dinâmica: ≤60 verde, 61–80 amarelo, >80 vermelho

#### `BarCard.tsx`
- Props: `title`, `used`, `total`, `unit`, `color`, `percent`
- Barra de progresso com `transition-all duration-500`
- Valores absolutos + percentual

#### `StorageCard.tsx`
- Props: `disks: Array<{label, used_gb, total_gb, usage_percent}>`
- Sub-card por disco
- Borda vermelha + ícone ⚠️ quando `usage_percent > 85`

#### `StatusBadge.tsx`
- Props: `ageSeconds: number`, `lastUpdate: string`
- "Ao Vivo 🟢" / "PC Offline 🔴" / "Carregando..."

### Tema visual

- **Dark theme** — `bg-[#0d0d0d]`, cards `bg-[#1a1a1a]`
- Acento **ciano** para CPU, **violeta** para GPU, **verde** para RAM, **laranja** para storage
- Font: `'Share Tech Mono'` (Google Fonts) para números, `'Exo 2'` para labels
- `rounded-2xl`, `shadow-lg` nos cards

### `dashboard/next.config.js`

```js
/** @type {import('next').NextConfig} */
const nextConfig = {}
module.exports = nextConfig
```

---

## PARTE 4 — GitHub e Vercel

### `C:\SensorDash\.gitignore`

Gerar com o seguinte conteúdo:

```gitignore
# Credenciais — NUNCA commitar
.env
.env.local
*.env

# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/

# Node
dashboard/node_modules/
dashboard/.next/

# OS
.DS_Store
Thumbs.db
```

### Publicar no GitHub

Executar na pasta `C:\SensorDash\`:

```bash
git init
git add .
git commit -m "feat: pc sensor dashboard inicial"
gh repo create sensor-dashboard --public --push --source=.
```

> Requer [GitHub CLI](https://cli.github.com) instalado. Se não estiver disponível, instruir a criar o repo manualmente em github.com e rodar `git remote add origin URL && git push -u origin main`.

### Deploy no Vercel

```bash
cd dashboard
npx vercel --prod
```

Durante o wizard do Vercel:
1. Detecta Next.js automaticamente — confirmar
2. **Adicionar variáveis de ambiente** quando solicitado:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`

Após o deploy, o Vercel fornece uma URL pública (ex: `sensor-dashboard.vercel.app`). Essa URL funciona de qualquer browser, em qualquer rede.

---

## Fluxo de dados resumido

```
server.py (PC)
  └── a cada 5s: INSERT em sensor_readings no Supabase

Browser (celular/qualquer lugar)
  └── a cada 5s: GET /api/sensors (Next.js no Vercel)
        └── SELECT * FROM sensor_readings ORDER BY recorded_at DESC LIMIT 1
              └── retorna dado + age_seconds
                    └── se age_seconds > 15 → PC aparece como Offline
```

---

## Checklist de entrega

### Supabase
- [ ] Tabela `sensor_readings` criada com trigger de limpeza
- [ ] Credenciais anotadas (URL, anon key, service key)

### Coletor local (server.py)
- [ ] `requirements.txt` gerado
- [ ] `.env` gerado (sem commitar)
- [ ] `server.py` gerado e rodando
- [ ] Dados aparecendo na tabela do Supabase (verificar em Table Editor)

### Frontend (Next.js)
- [ ] Projeto criado com `create-next-app`
- [ ] `.env.local` configurado
- [ ] API Route `/api/sensors` retornando JSON com `age_seconds`
- [ ] Dashboard renderizando todos os cards
- [ ] Status "Ao Vivo" / "PC Offline" funcionando
- [ ] Layout sem scroll horizontal em 375px

### GitHub
- [ ] `.gitignore` correto — arquivos `.env` não aparecem no `git status`
- [ ] Repositório criado e código publicado

### Vercel
- [ ] Deploy bem-sucedido
- [ ] Variáveis de ambiente configuradas no painel
- [ ] URL pública acessível do celular fora da rede local
