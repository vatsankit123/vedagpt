import { describe, it, expect } from 'vitest'
import { sendChatMessage } from '../chatApi'
import { ApiError } from '../errors'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/server'

describe('sendChatMessage', () => {
  it('returns a grounded response', async () => {
    const r = await sendChatMessage({ question: 'What is karma?' })
    expect(r.grounded).toBe(true)
    expect(r.sources.length).toBeGreaterThan(0)
    expect(r.answer).toBeTruthy()
  })

  it('returns an ungrounded response for off-topic questions', async () => {
    const r = await sendChatMessage({ question: 'quantum computing' })
    expect(r.grounded).toBe(false)
    expect(r.sources).toHaveLength(0)
  })

  it('throws ApiError kind=validation_error on HTTP 422', async () => {
    server.use(http.post('http://localhost:8000/api/v1/chat', () => HttpResponse.json({ detail: 'err' }, { status: 422 })))
    await expect(sendChatMessage({ question: 'test' })).rejects.toMatchObject({ kind: 'validation_error' })
  })

  it('throws ApiError kind=server_error on HTTP 500', async () => {
    server.use(http.post('http://localhost:8000/api/v1/chat', () => HttpResponse.json({}, { status: 500 })))
    await expect(sendChatMessage({ question: 'test' })).rejects.toMatchObject({ kind: 'server_error' })
  })

  it('throws ApiError kind=backend_unavailable on HTTP 503', async () => {
    server.use(http.post('http://localhost:8000/api/v1/chat', () => HttpResponse.json({}, { status: 503 })))
    await expect(sendChatMessage({ question: 'test' })).rejects.toMatchObject({ kind: 'backend_unavailable' })
  })

  it('throws ApiError on network failure', async () => {
    server.use(http.post('http://localhost:8000/api/v1/chat', () => HttpResponse.error()))
    await expect(sendChatMessage({ question: 'test' })).rejects.toMatchObject({ kind: 'network' })
  })

  it('throws ApiError on malformed response', async () => {
    server.use(http.post('http://localhost:8000/api/v1/chat', () => HttpResponse.json({ unexpected: true })))
    await expect(sendChatMessage({ question: 'test' })).rejects.toMatchObject({ kind: 'malformed_response' })
  })

  it('throws ApiError kind=cancelled when signal already aborted', async () => {
    // Pre-abort the controller so the check fires before fetch is called
    const ctrl = new AbortController()
    ctrl.abort()
    await expect(sendChatMessage({ question: 'test' }, ctrl.signal)).rejects.toMatchObject({ kind: 'cancelled' })
  })

  it('does not leak API keys in error messages', async () => {
    server.use(http.post('http://localhost:8000/api/v1/chat', () => HttpResponse.json({ detail: 'GEMINI_API_KEY invalid' }, { status: 500 })))
    try { await sendChatMessage({ question: 'test' }) } catch (err) {
      if (err instanceof ApiError) {
        expect(err.userMessage).not.toContain('GEMINI')
        expect(err.userMessage).not.toContain('API_KEY')
      }
    }
  })
})
