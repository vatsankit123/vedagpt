import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SourceDetailsDrawer } from '../SourceDetailsDrawer'
import { mockSource } from '@/test/fixtures'

describe('SourceDetailsDrawer', () => {
  it('does not render when source is null', () => {
    render(<SourceDetailsDrawer source={null} onClose={vi.fn()} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('renders when source provided', () => {
    render(<SourceDetailsDrawer source={mockSource} onClose={vi.fn()} />)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('has accessible dialog label', () => {
    render(<SourceDetailsDrawer source={mockSource} onClose={vi.fn()} />)
    expect(screen.getByRole('dialog', { name: /Source details: Bhagavad Gita 2.47/i })).toBeInTheDocument()
  })

  it('displays translation', () => {
    render(<SourceDetailsDrawer source={mockSource} onClose={vi.fn()} />)
    expect(screen.getByText(/prescribed duties/i)).toBeInTheDocument()
  })

  it('does not display missing translator', () => {
    render(<SourceDetailsDrawer source={{ ...mockSource, translator: '' }} onClose={vi.fn()} />)
    expect(screen.queryByText(/Fixture Translator/)).not.toBeInTheDocument()
  })

  it('calls onClose on close button click', () => {
    const onClose = vi.fn()
    render(<SourceDetailsDrawer source={mockSource} onClose={onClose} />)
    fireEvent.click(screen.getByRole('button', { name: /close source details/i }))
    expect(onClose).toHaveBeenCalled()
  })

  it('calls onClose on Escape', () => {
    const onClose = vi.fn()
    render(<SourceDetailsDrawer source={mockSource} onClose={onClose} />)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalled()
  })

  it('has aria-modal attribute', () => {
    render(<SourceDetailsDrawer source={mockSource} onClose={vi.fn()} />)
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true')
  })
})
