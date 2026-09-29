import { BookOpen, Sparkles } from 'lucide-react'
const QUESTIONS = [
  'What does the indexed text say about performing duty without attachment?',
  'What does the indexed text say about controlling the mind?',
  'Explain Bhagavad Gita chapter 2, verse 47.',
  'Which indexed passages discuss karma yoga?',
]
interface Props { onSelectQuestion: (q: string) => void }
export function ChatEmptyState({ onSelectQuestion }: Props) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] py-12 text-center gap-6 animate-fade-in">
      <div className="h-16 w-16 rounded-full bg-saffron-100 dark:bg-saffron-950 flex items-center justify-center">
        <BookOpen className="h-8 w-8 text-saffron-500" aria-hidden="true" />
      </div>
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-stone-900 dark:text-stone-50">Welcome to VedaGPT</h1>
        <p className="text-sm text-stone-500 dark:text-stone-400 max-w-sm">Ask questions about indexed scripture passages and receive answers grounded in retrieved sources. Citations are programmatic -- never invented by the AI.</p>
      </div>
      <div className="w-full max-w-lg">
        <p className="text-xs text-stone-400 dark:text-stone-500 mb-3 flex items-center justify-center gap-1">
          <Sparkles className="h-3 w-3" aria-hidden="true" />
          Example questions (demonstration corpus only)
        </p>
        <ul className="space-y-2" role="list">
          {QUESTIONS.map((q) => (
            <li key={q}>
              <button type="button" onClick={() => onSelectQuestion(q)} className="w-full text-left card px-4 py-3 text-sm text-stone-700 dark:text-stone-300 hover:border-saffron-300 dark:hover:border-saffron-700 hover:bg-saffron-50 dark:hover:bg-saffron-950/50 transition-colors focus-ring rounded-xl">{q}</button>
            </li>
          ))}
        </ul>
      </div>
      <p className="text-xs text-stone-400 dark:text-stone-500 max-w-xs">Answers include structured citations. Verify results against cited editions and qualified scholarly sources.</p>
    </div>
  )
}
