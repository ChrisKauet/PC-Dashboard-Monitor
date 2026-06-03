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