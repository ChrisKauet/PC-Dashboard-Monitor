import { NextResponse } from "next/server"

export const dynamic = "force-dynamic"

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
      }
    )

    if (!res.ok) {
      return NextResponse.json(
        { error: `Supabase returned ${res.status}` },
        { status: 502 }
      )
    }

    const data = await res.json()

    if (!data || data.length === 0) {
      return NextResponse.json(
        { error: "No sensor data available" },
        { status: 404 }
      )
    }

    const row = data[0]

    // Map Supabase row to frontend format
    return NextResponse.json({
      cpu_usage: row.cpu_usage,
      cpu_temp: row.cpu_temp,
      cpu_cores: typeof row.cpu_cores === "string" ? JSON.parse(row.cpu_cores) : row.cpu_cores,
      ram_used: row.ram_used,
      ram_total: row.ram_total,
      ram_usage: row.ram_usage,
      storage: typeof row.storage === "string" ? JSON.parse(row.storage) : row.storage,
      uptime_sec: row.uptime_sec,
      hostname: row.hostname,
      gpu_usage: row.gpu_usage,
      gpu_temp: row.gpu_temp,
      vram_used: row.vram_used,
      vram_total: row.vram_total,
      gpu_fan_rpm: row.gpu_fan_rpm,
      gpu_vendor: row.gpu_vendor,
      status: "online",
    })
  } catch (error) {
    return NextResponse.json(
      { error: "Supabase unreachable" },
      { status: 503 }
    )
  }
}
