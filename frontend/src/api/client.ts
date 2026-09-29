import { env } from '@/config/env'
import { ApiError } from './errors'
import type { ApiErrorKind } from './errors'

const REQUEST_TIMEOUT_MS = 30_000

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { signal?: AbortSignal } = {},
): Promise<T> {
  const url = env.apiBaseUrl + path

  // Check if already aborted before making any network call
  if (options.signal?.aborted) {
    throw new ApiError('cancelled', 'The request was cancelled.')
  }

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort('timeout'), REQUEST_TIMEOUT_MS)

  // Forward the caller's signal: if it aborts, also abort ours
  options.signal?.addEventListener('abort', () => controller.abort('cancelled'), { once: true })

  let response: Response
  try {
    response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...options.headers,
      },
    })
  } catch (err) {
    clearTimeout(timer)
    // Distinguish caller-cancellation from internal timeout
    if (options.signal?.aborted || (err instanceof Error && err.name === 'AbortError')) {
      throw new ApiError('cancelled', 'The request was cancelled.')
    }
    throw new ApiError(
      'network',
      'VedaGPT could not reach the backend. Please check that the local API is running.',
    )
  } finally {
    clearTimeout(timer)
  }

  if (!response.ok) {
    let kind: ApiErrorKind = 'server_error'
    let msg = 'An internal error occurred. Please try again later.'
    if (response.status === 503) {
      kind = 'backend_unavailable'
      msg = 'The VedaGPT service is temporarily unavailable.'
    } else if (response.status === 422 || response.status === 400) {
      kind = 'validation_error'
      msg = 'The question could not be processed. Please rephrase and try again.'
    }
    throw new ApiError(kind, msg, response.status)
  }

  let data: unknown
  try {
    data = await response.json()
  } catch {
    throw new ApiError('malformed_response', 'The server returned an unexpected response.')
  }
  return data as T
}
