import { CheckCircle2, HelpCircle } from 'lucide-react'
import { cn } from '@/lib/cn'
interface Props { grounded: boolean }
export function GroundingBadge({ grounded }: Props) {
  return (
    <div
      className={cn('inline-flex items-center gap-1.5 text-xs rounded-full px-2.5 py-1 font-medium',
        grounded ? 'bg-green-50 dark:bg-green-950 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800'
                 : 'bg-stone-100 dark:bg-stone-800 text-stone-500 dark:text-stone-400 border border-stone-200 dark:border-stone-700')}
      role="status"
      aria-label={grounded ? 'Answer grounded in indexed sources' : 'Answer not grounded -- insufficient indexed sources'}>
      {grounded ? <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" /> : <HelpCircle className="h-3.5 w-3.5" aria-hidden="true" />}
      {grounded ? 'Grounded in indexed sources' : 'Insufficient indexed sources'}
    </div>
  )
}
