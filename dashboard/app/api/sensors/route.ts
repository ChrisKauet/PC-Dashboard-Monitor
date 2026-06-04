import { NextResponse } from "next/server"

/**
 * Proxy route: forwards to the local sensor collector.
 * In production (Vercel), the frontend fetches directly from NEXT_PUBLIC_API_URL.
 * This route is kept for local dev convenience.
 */
export const dynamic = "force-dynamic"

export async function GET() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"

  try {
    const res = await fetch(`${apiUrl}/api/sensors`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    })

    if (!res.ok) {
      return NextResponse.json(
        { error: `Backend returned ${res.status}` },
        { status: 502 }
      )
    }

    const data = await res.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: "Sensor backend unreachable. Is server.py running?" },
      { status: 503 }
    )
  }
}
