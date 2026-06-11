import { NextResponse } from "next/server"

export const dynamic = "force-dynamic"

const SUPABASE_TIMEOUT_MS = 5000

export async function GET() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseKey = process.env.SUPABASE_SERVICE_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  if (!supabaseUrl || !supabaseKey) {
    return NextResponse.json(
      { error: "Supabase not configured" },
      { status: 503 }
    )
  }

  try {
    const res = await fetch(
      `${supabaseUrl}/rest/v1/sensor_readings?select=*&order=recorded_at.desc&limit=1`,
      {
        headers: {
          apikey: supabaseKey,
          Authorization: `Bearer ${supabaseKey}`,
        },
        cache: "no-store",
        signal: AbortSignal.timeout(SUPABASE_TIMEOUT_MS),
      }
    )

    if (!res.ok) {
      const status = res.status === 429 ? 429 : 502
      return NextResponse.json(
        { error: `Supabase returned ${res.status}` },
        { status }
      )
    }

    const data = await res.json()

    // No rows yet — return empty status instead of 404 so the frontend
    // doesn't fall back to mock data when the DB is simply empty.
    if (!data || data.length === 0) {
      return NextResponse.json({ status: "no_data" })
    }

    const row = data[0]

    // Safe JSON parse helpers
    function parseJson<T>(val: unknown, fallback: T): T {
      if (val == null) return fallback
      if (typeof val !== "string") return val as T
      try { return JSON.parse(val) } catch { return fallback }
    }

    return NextResponse.json({
      status: "online",
      cpu_usage: row.cpu_usage ?? null,
      cpu_temp: row.cpu_temp ?? null,
      cpu_cores: parseJson(row.cpu_cores, null),
      ram_used: row.ram_used ?? null,
      ram_total: row.ram_total ?? null,
      ram_usage: row.ram_usage ?? null,
      storage: parseJson(row.storage, null),
      uptime_sec: row.uptime_sec ?? null,
      hostname: row.hostname ?? null,
      gpu_usage: row.gpu_usage ?? null,
      gpu_temp: row.gpu_temp ?? null,
      vram_used: row.vram_used ?? null,
      vram_total: row.vram_total ?? null,
      gpu_fan_rpm: row.gpu_fan_rpm ?? null,
      gpu_vendor: row.gpu_vendor ?? null,
      // Optional fields — present only if the Supabase schema includes them
      dl_speed: row.dl_speed ?? null,
      ul_speed: row.ul_speed ?? null,
      process_count: row.process_count ?? null,
      temp_ssd: row.temp_ssd ?? null,
      temp_mb: row.temp_mb ?? null,
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    const isTimeout = message.includes("TimeoutError") || message.includes("AbortError")
    console.error("[/api/sensors]", isTimeout ? "Supabase timeout" : message)
    return NextResponse.json(
      { error: isTimeout ? "Supabase timeout" : "Supabase unreachable" },
      { status: 503 }
    )
  }
}
