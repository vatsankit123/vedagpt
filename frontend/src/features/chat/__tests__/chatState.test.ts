import { describe, it, expect, beforeEach } from 'vitest'
import { loadHistory, saveHistory, clearHistory } from '../chatState'
import type { ChatMessage } from '../chatTypes'

const msg: ChatMessage = { id: 'x', role: 'user', content: 'hi', createdAt: new Date(), status: 'success' }

describe('chatState', () => {
  beforeEach(() => localStorage.clear())

  it('returns empty array when nothing stored', () => {
    expect(loadHistory()).toEqual([])
  })

  it('saves and loads messages', () => {
    saveHistory([msg])
    const loaded = loadHistory()
    expect(loaded.length).toBe(1)
    expect(loaded[0].content).toBe('hi')
  })

  it('clears history', () => {
    saveHistory([msg]); clearHistory()
    expect(loadHistory()).toEqual([])
  })

  it('handles malformed stored data safely', () => {
    localStorage.setItem('vedagpt-chat-v1', 'not json')
    expect(() => loadHistory()).not.toThrow()
    expect(loadHistory()).toEqual([])
  })
})
