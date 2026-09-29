import { useQuery } from '@tanstack/react-query'
import { fetchHealth } from '@/api/healthApi'
import { cn } from '@/lib/cn'
export function HealthIndicator() {
  const { data, isLoading, isError } = useQuery({ queryKey: ['health'], queryFn: ({ signal }) => fetchHealth(signal), staleTime: 30_000, refetchInterval: 60_000, retry: 1 })
  const isOk = !isLoading && !isError && data?.status === 'ok'
  return (
    <div className="hidden sm:flex items-center gap-1.5 text-xs" aria-label={isLoading?'Checking backend':isOk?'Backend connected':'Backend unavailable'}>
      <span className={cn('h-2 w-2 rounded-full', isLoading&&'bg-yellow-400 animate-pulse-slow', isOk&&'bg-green-500', isError&&'bg-red-400')} aria-hidden="true" />
      <span className="text-stone-400 dark:text-stone-500 select-none">{isLoading?'Checking':isOk?'Connected':'Unavailable'}</span>
    </div>
  )
}
