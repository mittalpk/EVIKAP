import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import CitationList, { formatAnswerWithInlineCitations } from './CitationList'

describe('CitationList Component (US-012)', () => {
  it('renders citation list with source badges and clickable links', () => {
    const citations = [
      {
        chunk_id: 'chk-001',
        source_url: 'https://github.com/org/repo/blob/main/auth.py',
        source_type: 'github_repo',
        document_id: 'auth.py',
        content_excerpt: 'def authenticate_user(): pass',
        relevance_score: 0.95,
      },
      {
        chunk_id: 'chk-002',
        source_url: 'https://wiki.example.com/pages/security',
        source_type: 'confluence_wiki',
        document_id: 'Security Policy',
        content_excerpt: 'All requests must be encrypted.',
        relevance_score: 0.88,
      },
    ]

    render(<CitationList citations={citations} />)

    expect(screen.getByText(/Source Evidence & Citations \(2 sources\)/i)).toBeDefined()
    expect(screen.getByText(/GitHub Source/i)).toBeDefined()
    expect(screen.getByText(/Wiki Source/i)).toBeDefined()
    expect(screen.getByText(/auth.py/i)).toBeDefined()
    expect(screen.getByText(/Security Policy/i)).toBeDefined()
    expect(screen.getByText(/def authenticate_user\(\)/i)).toBeDefined()
  })

  it('renders empty citations warning banner when citations list is empty', () => {
    render(<CitationList citations={[]} />)

    expect(screen.getByText(/No sources found. This answer may be ungrounded — verify independently/i)).toBeDefined()
  })

  it('renders guardrail flags warning banner when guardrailFlags is non-empty', () => {
    render(<CitationList citations={[]} guardrailFlags={['pii-redacted', 'prompt-injection-blocked']} />)

    expect(screen.getByText(/Safety Guardrails Warning/i)).toBeDefined()
    expect(screen.getByText(/PII has been redacted from this response/i)).toBeDefined()
    expect(screen.getByText(/Potential prompt injection attempt detected and sanitized/i)).toBeDefined()
  })

  it('handles restricted/broken source URLs gracefully', () => {
    const citations = [
      {
        chunk_id: 'chk-restricted',
        source_url: '',
        permissions_ref: 'restricted',
        document_id: 'secret_config.json',
        content_excerpt: 'TOP SECRET KEYS',
      },
    ]

    render(<CitationList citations={citations} />)

    expect(screen.getByText(/Source may be restricted \(Sign in to view\)/i)).toBeDefined()
  })

  it('toggles collapsible show more for > 5 citations', () => {
    const citations = Array.from({ length: 7 }, (_, i) => ({
      chunk_id: `chk-${i + 1}`,
      source_url: `https://github.com/org/repo/file${i + 1}.py`,
      source_type: 'github_repo',
      document_id: `file${i + 1}.py`,
      content_excerpt: `Excerpt for file ${i + 1}`,
    }))

    render(<CitationList citations={citations} />)

    // Expand citation list
    const expandBtn = screen.getByText(/View Sources ▼/i)
    fireEvent.click(expandBtn)

    expect(screen.getByText(/Show 2 more sources…/i)).toBeDefined()
    expect(screen.queryByText(/file7.py/i)).toBeNull()

    const showMoreBtn = screen.getByText(/Show 2 more sources…/i)
    fireEvent.click(showMoreBtn)

    expect(screen.getByText(/file7.py/i)).toBeDefined()

  })

  it('formats inline citation superscript markers [1], [2] correctly', () => {
    const { container } = render(<>{formatAnswerWithInlineCitations('This claim is verified [1] and [2].')}</>)

    expect(container.querySelector('sup')).not.toBeNull()
    expect(container.querySelectorAll('sup').length).toBe(2)
  })
})
