import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SourceCard } from '../SourceCard'
import { mockSource } from '@/test/fixtures'

describe('SourceCard', () => {
  it('displays scripture and verse reference', () => {
    render(<SourceCard source={mockSource} onOpen={vi.fn()} />)
    expect(screen.getByText(/Bhagavad Gita 2.47/i)).toBeInTheDocument()
  })

  it('displays translation text', () => {
    render(<SourceCard source={mockSource} onOpen={vi.fn()} />)
    expect(screen.getByText(/prescribed duties/i)).toBeInTheDocument()
  })

  it('displays translator when present', () => {
    render(<SourceCard source={mockSource} onOpen={vi.fn()} />)
    expect(screen.getByText(/Fixture Translator/i)).toBeInTheDocument()
  })

  it('does not display translator when absent', () => {
    render(<SourceCard source={{ ...mockSource, translator: '' }} onOpen={vi.fn()} />)
    expect(screen.queryByText(/Trans:/i)).not.toBeInTheDocument()
  })

  it('calls onOpen when details button clicked', () => {
    const onOpen = vi.fn()
    render(<SourceCard source={mockSource} onOpen={onOpen} />)
    fireEvent.click(screen.getByRole('button', { name: /view details/i }))
    expect(onOpen).toHaveBeenCalled()
  })

  it('has accessible button label', () => {
    render(<SourceCard source={mockSource} onOpen={vi.fn()} />)
    expect(screen.getByRole('button', { name: /view details for Bhagavad Gita 2.47/i })).toBeInTheDocument()
  })

  it('does not display score as percentage', () => {
    render(<SourceCard source={mockSource} onOpen={vi.fn()} />)
    expect(screen.queryByText(/%/)).not.toBeInTheDocument()
  })
})
