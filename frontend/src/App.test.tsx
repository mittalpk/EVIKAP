import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import App from './App'
import { apiClient } from './api/client'

vi.mock('./api/client', () => ({
  apiClient: {
    isLoggedIn: vi.fn().mockReturnValue(true),
    setToken: vi.fn(),
    login: vi.fn(),
    checkHealth: vi.fn(),
    queryKnowledge: vi.fn(),
    runAgentTask: vi.fn(),
  },
}))

describe('App Knowledge Submission UI (US-010)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(apiClient.isLoggedIn as any).mockReturnValue(true)
  })

  it('renders title, query input, and submit button', () => {
    render(<App />)
    expect(screen.getByText('VigilRAG')).toBeDefined()
    expect(screen.getByPlaceholderText(/What is our PII policy/i)).toBeDefined()
    expect(screen.getByRole('button', { name: /Execute Query/i })).toBeDefined()
  })

  it('disables submit button when query input is empty', () => {
    render(<App />)
    const submitBtn = screen.getByRole('button', { name: /Execute Query/i }) as HTMLButtonElement
    expect(submitBtn.disabled).toBe(true)
  })

  it('enables submit button when input is non-empty and triggers query', async () => {
    ;(apiClient.queryKnowledge as any).mockResolvedValue({
      answer_synthesis: 'JWT authentication uses HS256 algorithm.',
      evidence: [
        {
          chunk_id: 'chk-1',
          content: 'JWT tokens are verified using HS256 algorithm.',
          source_url: 'https://github.com/org/repo/blob/main/auth.py',
          relevance_score: 0.95,
          source_id: 'github-repo',
          permissions_ref: 'public',
        },
      ],
      trace_id: 'trc-test-123',
      execution_time_ms: 45,
    })

    render(<App />)
    const textarea = screen.getByPlaceholderText(/What is our PII policy/i)
    fireEvent.change(textarea, { target: { value: 'How is JWT validated?' } })

    const submitBtn = screen.getByRole('button', { name: /Execute Query/i }) as HTMLButtonElement
    expect(submitBtn.disabled).toBe(false)

    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(apiClient.queryKnowledge).toHaveBeenCalledWith('How is JWT validated?')
      expect(screen.getByText(/JWT authentication uses HS256 algorithm/i)).toBeDefined()
      expect(screen.getByText(/GitHub Source/i)).toBeDefined()
    })
  })

  it('displays warning when evidence list is empty', async () => {
    ;(apiClient.queryKnowledge as any).mockResolvedValue({
      answer_synthesis: 'No relevant data found.',
      evidence: [],
      trace_id: 'trc-empty-000',
      execution_time_ms: 10,
    })

    render(<App />)
    const textarea = screen.getByPlaceholderText(/What is our PII policy/i)
    fireEvent.change(textarea, { target: { value: 'Nonexistent query' } })

    const submitBtn = screen.getByRole('button', { name: /Execute Query/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText(/No sources found. This answer may be ungrounded/i)).toBeDefined()
    })

  })
})
