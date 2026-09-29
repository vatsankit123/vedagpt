function normalizeBaseUrl(url: string): string {
  return url.replace(/\/+$/, '')
}
const rawBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
export const env = {
  apiBaseUrl: normalizeBaseUrl(String(rawBaseUrl)),
  appName: String(import.meta.env.VITE_APP_NAME ?? 'VedaGPT'),
  isDemoMode: import.meta.env.VITE_DEMO_MODE !== 'false',
  enableLocalHistory: import.meta.env.VITE_ENABLE_LOCAL_HISTORY !== 'false',
  isDev: import.meta.env.DEV === true,
  isProd: import.meta.env.PROD === true,
} as const
export type Env = typeof env
