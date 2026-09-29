import { apiFetch } from './client'
import { healthResponseSchema } from './schemas'
import type { HealthResponse } from './types'
export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const raw = await apiFetch<unknown>('/health', { signal })
  const parsed = healthResponseSchema.safeParse(raw)
  if (!parsed.success) return { status: 'unknown', service: 'vedagpt-api' }
  return parsed.data
}
