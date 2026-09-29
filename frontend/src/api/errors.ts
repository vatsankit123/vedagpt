export type ApiErrorKind = 'network'|'timeout'|'cancelled'|'backend_unavailable'|'validation_error'|'server_error'|'malformed_response'|'unknown'
export class ApiError extends Error {
  constructor(public readonly kind: ApiErrorKind, public readonly userMessage: string, public readonly status?: number) {
    super(userMessage); this.name = 'ApiError'
  }
}
export function userFacingMessage(error: unknown): string {
  if (error instanceof ApiError) return error.userMessage
  if (error instanceof Error && error.name === 'AbortError') return 'The request was cancelled.'
  return 'An unexpected error occurred. Please try again.'
}
