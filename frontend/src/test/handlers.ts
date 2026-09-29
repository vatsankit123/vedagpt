import { http, HttpResponse } from 'msw'
import { mockGroundedResponse, mockHealthOk, mockUngroundedResponse } from './fixtures'
export const handlers = [
  http.get('http://localhost:8000/health', () => HttpResponse.json(mockHealthOk)),
  http.post('http://localhost:8000/api/v1/chat', async ({ request }) => {
    const body = await request.json() as { question: string }
    const q = (body.question ?? '').toLowerCase()
    if (q.includes('quantum') || q.includes('unrelated')) return HttpResponse.json(mockUngroundedResponse)
    return HttpResponse.json(mockGroundedResponse)
  }),
]
