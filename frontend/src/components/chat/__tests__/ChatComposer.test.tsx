import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatComposer } from '../ChatComposer'

function setup(overrides = {}) {
  const onSend = vi.fn(); const onCancel = vi.fn()
  const props = { onSend, onCancel, isLoading: false, ...overrides }
  const utils = render(<ChatComposer {...props} />)
  return { onSend, onCancel, ...utils }
}

describe('ChatComposer', () => {
  it('has accessible label on textarea', () => {
    setup()
    expect(screen.getByLabelText(/ask a question/i)).toBeInTheDocument()
  })

  it('send button disabled for blank input', () => {
    setup()
    expect(screen.getByRole('button', { name: /send/i })).toBeDisabled()
  })

  it('send button disabled for whitespace-only input', async () => {
    const user = userEvent.setup(); setup()
    await user.type(screen.getByRole('textbox'), '   ')
    expect(screen.getByRole('button', { name: /send/i })).toBeDisabled()
  })

  it('send button enabled for valid input', async () => {
    const user = userEvent.setup(); setup()
    await user.type(screen.getByRole('textbox'), 'What is karma?')
    expect(screen.getByRole('button', { name: /send/i })).not.toBeDisabled()
  })

  it('Enter submits', async () => {
    const user = userEvent.setup(); const { onSend } = setup()
    await user.type(screen.getByRole('textbox'), 'What is dharma?')
    await user.keyboard('{Enter}')
    expect(onSend).toHaveBeenCalledWith('What is dharma?')
  })

  it('Shift+Enter does not submit', async () => {
    const user = userEvent.setup(); const { onSend } = setup()
    await user.type(screen.getByRole('textbox'), 'Line 1')
    await user.keyboard('{Shift>}{Enter}{/Shift}')
    expect(onSend).not.toHaveBeenCalled()
  })

  it('clears input after submission', async () => {
    const user = userEvent.setup(); setup()
    const ta = screen.getByRole('textbox') as HTMLTextAreaElement
    await user.type(ta, 'What is yoga?')
    await user.keyboard('{Enter}')
    expect(ta.value).toBe('')
  })

  it('shows cancel button when loading', () => {
    const { onCancel } = setup({ isLoading: true })
    const btn = screen.getByRole('button', { name: /cancel/i })
    expect(btn).toBeInTheDocument()
    fireEvent.click(btn)
    expect(onCancel).toHaveBeenCalled()
  })

  it('textarea disabled while loading', () => {
    setup({ isLoading: true })
    expect(screen.getByRole('textbox')).toBeDisabled()
  })
})
