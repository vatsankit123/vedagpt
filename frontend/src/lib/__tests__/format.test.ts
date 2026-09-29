import { describe, it, expect } from 'vitest'
import { formatVerseRef, truncate } from '../format'
describe('formatVerseRef', () => {
  it('formats chapter and verse', () => { expect(formatVerseRef(2, 47)).toBe('2.47') })
  it('formats single-digit chapter', () => { expect(formatVerseRef(1, 1)).toBe('1.1') })
})
describe('truncate', () => {
  it('returns text unchanged when within limit', () => { expect(truncate('hello', 10)).toBe('hello') })
  it('truncates with ellipsis', () => { expect(truncate('hello world test', 10)).toHaveLength(10) })
  it('handles exact length', () => { expect(truncate('12345', 5)).toBe('12345') })
})
