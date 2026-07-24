import React, { useState } from 'react'

export interface CitationItem {
  chunk_id: string
  source_url?: string
  source_type?: string
  source_id?: string
  document_id?: string
  parent_doc_id?: string
  content_excerpt?: string
  content?: string
  relevance_score?: number
  permissions_ref?: string
}

export interface CitationListProps {
  citations?: CitationItem[]
  guardrailFlags?: string[]
  answerText?: string
}

export function formatAnswerWithInlineCitations(text: string): React.ReactNode {
  if (!text) return null

  // Regex to match inline [1], [2] citation markers
  const parts = text.split(/(\[\d+\])/g)

  return parts.map((part, index) => {
    const match = part.match(/^\[(\d+)\]$/)
    if (match) {
      const citeNum = match[1]
      return (
        <sup key={index} className="inline-citation-sup">
          <a
            href={`#citation-${citeNum}`}
            className="inline-citation-link"
            title={`Jump to citation [${citeNum}]`}
          >
            [{citeNum}]
          </a>
        </sup>
      )
    }
    return part
  })
}

export function getGuardrailMessage(flag: string): string {
  switch (flag) {
    case 'pii-redacted':
      return 'PII has been redacted from this response.'
    case 'prompt-injection-blocked':
      return 'Potential prompt injection attempt detected and sanitized.'
    case 'content-filtered':
      return 'Response content was filtered according to security policy.'
    default:
      return `Safety Guardrail Notice: Flagged as [${flag}].`
  }
}

export function getSourceBadge(item: CitationItem): { label: string; color: string; icon: string } {
  const type = (item.source_type || item.source_id || '').toLowerCase()
  if (type.includes('wiki') || type.includes('confluence')) {
    return { label: 'Wiki Source', color: '#10b981', icon: '📖' }
  }
  if (type.includes('db') || type.includes('postgres') || type.includes('sql')) {
    return { label: 'DB Source', color: '#8b5cf6', icon: '🗄️' }
  }
  return { label: 'GitHub Source', color: '#3b82f6', icon: '💻' }
}

export function getFileName(item: CitationItem): string {
  if (item.document_id) return item.document_id
  if (item.parent_doc_id) return item.parent_doc_id
  if (item.source_url) {
    try {
      const url = new URL(item.source_url)
      const parts = url.pathname.split('/').filter(Boolean)
      return parts[parts.length - 1] || item.source_url
    } catch {
      return item.source_url
    }
  }
  return item.chunk_id
}

export default function CitationList({ citations = [], guardrailFlags = [] }: CitationListProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showAll, setShowAll] = useState(false)

  const hasCitations = citations && citations.length > 0
  const initialLimit = 5
  const visibleCitations = showAll ? citations : citations.slice(0, initialLimit)
  const remainingCount = citations.length - initialLimit

  return (
    <div className="citation-list-wrapper mt-16">
      {/* 1. Guardrail Flags Warning Banner */}
      {guardrailFlags && guardrailFlags.length > 0 && (
        <div className="guardrail-banner" role="alert">
          <span className="guardrail-icon">⚠️</span>
          <div className="guardrail-text">
            <strong>Safety Guardrails Warning</strong>
            {guardrailFlags.map((flag, idx) => (
              <div key={idx} className="guardrail-flag-item">
                • {getGuardrailMessage(flag)}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 2. Empty Citations Warning */}
      {!hasCitations ? (
        <div className="empty-citations-banner" role="status">
          <span className="warning-icon">⚠️</span>
          <span>No sources found. This answer may be ungrounded — verify independently.</span>
        </div>
      ) : (
        /* 3. Collapsible Citation Section */
        <div className="citations-container">
          <div className="citations-header" onClick={() => setIsExpanded(!isExpanded)}>
            <div className="citations-title">
              <span className="citations-icon">📚</span>
              <strong>Source Evidence & Citations ({citations.length} {citations.length === 1 ? 'source' : 'sources'})</strong>
            </div>
            <button className="toggle-expand-btn" aria-expanded={isExpanded}>
              {isExpanded ? 'Hide Sources ▲' : 'View Sources ▼'}
            </button>
          </div>

          {(isExpanded || citations.length <= 3) && (
            <div className="citations-grid mt-12 fade-in">
              {visibleCitations.map((item, index) => {
                const citeNum = index + 1
                const badge = getSourceBadge(item)
                const fileName = getFileName(item)
                const excerpt = item.content_excerpt || item.content || ''
                const truncatedExcerpt = excerpt.length > 250 ? excerpt.slice(0, 250) + '…' : excerpt
                const isRestricted = !item.source_url || item.permissions_ref === 'restricted'

                return (
                  <div key={item.chunk_id || index} id={`citation-${citeNum}`} className="citation-card">
                    <div className="citation-card-header">
                      <span className="citation-number">[{citeNum}]</span>
                      <span
                        className="source-badge"
                        style={{ backgroundColor: badge.color }}
                      >
                        {badge.icon} {badge.label}
                      </span>
                      <span className="file-name" title={fileName}>{fileName}</span>
                    </div>

                    <div className="citation-excerpt">
                      {truncatedExcerpt}
                    </div>

                    <div className="citation-card-footer">
                      {isRestricted ? (
                        <span className="restricted-notice" title="Sign in or verify ACL permission to view full source">
                          🔒 Source may be restricted (Sign in to view)
                        </span>
                      ) : (
                        <a
                          href={item.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="citation-link"
                        >
                          View Original Source ↗
                        </a>
                      )}
                      {item.relevance_score !== undefined && (
                        <span className="relevance-score">
                          Score: {(item.relevance_score * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}

              {/* Show N More Toggle for > 5 citations */}
              {remainingCount > 0 && !showAll && (
                <button
                  className="show-more-citations-btn"
                  onClick={() => setShowAll(true)}
                >
                  Show {remainingCount} more {remainingCount === 1 ? 'source' : 'sources'}…
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
