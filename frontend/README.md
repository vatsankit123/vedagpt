# VedaGPT Frontend (Phase 3)

Source-grounded scripture learning interface built with React, TypeScript, and Vite.

## Technology Stack

| Tool | Purpose |
|---|---|
| React 18 | UI framework |
| TypeScript (strict) | Type safety |
| Vite 5 | Dev server and bundler |
| React Router 6 | Client-side routing |
| TanStack Query 5 | Server state and health polling |
| Tailwind CSS 3 | Styling |
| Zod 3 | Runtime API response validation |
| Lucide React | Icons |
| Vitest 2 | Unit and component tests |
| React Testing Library 16 | Component testing |
| MSW 2 | Request mocking for tests |

## Prerequisites

- Node.js >= 18
- npm >= 9
- VedaGPT FastAPI backend running on http://localhost:8000

## Environment Configuration

```powershell
Copy-Item .env.example .env.local
```

Edit `.env.local`:

```
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=VedaGPT
VITE_DEMO_MODE=true
VITE_ENABLE_LOCAL_HISTORY=true
```

IMPORTANT: Never put GEMINI_API_KEY, QDRANT_API_KEY, or any backend secret
in .env.local. VITE_ variables are browser-visible.

## Start the Backend

```powershell
cd ..\backend
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

## Start the Frontend

```powershell
npm run dev
```

Open: http://localhost:5173

## Running Tests

```powershell
npm run test
npm run test:watch
```

## Type Checking

```powershell
npm run typecheck
```

## Lint

```powershell
npm run lint
```

## Production Build

```powershell
npm run build
npm run preview
```

## CORS Configuration

The backend must allow http://localhost:5173.
In backend/.env set:
```
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8000
```

## Demo Mode

When VITE_DEMO_MODE=true (the default), a banner informs users that:
- The corpus is demonstration data only
- Citations should not be treated as authoritative

This warning cannot be hidden while demo data is in use.

## Local Conversation History

When VITE_ENABLE_LOCAL_HISTORY=true, conversations are saved to localStorage.
History stays in the current browser only (never synced to server).
Maximum 50 messages stored. Use the Clear button to remove history.

## API Contract

- GET /health -> { status: string, service: string }
- POST /api/v1/chat body: { question, top_k? } -> { answer, grounded, sources, message }

See src/api/types.ts for TypeScript types.

## Accessibility

- Semantic HTML throughout
- Keyboard navigation for all interactive elements
- Visible focus indicators
- aria-live region for screen reader announcements
- Source drawer with focus management and Escape key
- WCAG-compatible contrast ratios

## Security

- No secrets in VITE_ environment variables
- Gemini and Qdrant are never called from the browser
- Runtime response validation with Zod
- No dangerouslySetInnerHTML usage
- Safe string concatenation (no eval or innerHTML)
- rel=noopener noreferrer on external links

## Known Limitations (Phase 3)

- No user authentication (Phase 4)
- No server-side conversation history (Phase 4)
- Conversation history is browser-local only
- Demo corpus only -- citations are not production-verified scripture
- Voice input not implemented (out of Phase 3 scope)
