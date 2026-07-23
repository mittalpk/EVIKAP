import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { apiClient, KnowledgeResponse } from './api/client'
import './App.css'


const KnowledgeAnimation = () => (
  <svg viewBox="0 0 600 240" className="animated-diagram">
    <defs>
      <linearGradient id="lineGradInfo" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stopColor="#4f8ef7" stopOpacity="0.2"/>
        <stop offset="100%" stopColor="#4f8ef7" stopOpacity="0.8"/>
      </linearGradient>
    </defs>
    <path className="flow-path flow-forward" d="M 120 120 L 250 120" />
    <path className="flow-path flow-split" d="M 330 100 L 420 60" />
    <path className="flow-path flow-split" d="M 330 140 L 420 180" />
    
    <g transform="translate(20, 100)">
      <rect width="100" height="40" rx="6" className="node-rect" />
      <text x="50" y="24" className="node-text">User Query</text>
    </g>
    <g transform="translate(250, 80)">
      <rect width="80" height="80" rx="40" className="node-rect" style={{stroke: '#4f8ef7'}} />
      <text x="40" y="40" className="node-text">Router</text>
      <text x="40" y="55" className="node-sub">Regex</text>
    </g>
    <g transform="translate(420, 40)">
      <rect width="140" height="40" rx="6" className="node-rect" style={{stroke: '#34d399'}} />
      <text x="70" y="24" className="node-text">GitHub Repos</text>
    </g>
    <g transform="translate(420, 160)">
      <rect width="140" height="40" rx="6" className="node-rect" style={{stroke: '#34d399'}} />
      <text x="70" y="24" className="node-text">Azure Blob</text>
    </g>
    <g transform="translate(370, 70)">
      <circle cx="0" cy="0" r="4" fill="#34d399" className="flow-dot" />
    </g>
    <g transform="translate(370, 170)">
      <circle cx="0" cy="0" r="4" fill="#34d399" className="flow-dot" />
    </g>
  </svg>
);

const AgentAnimation = () => (
  <svg viewBox="0 0 700 240" className="animated-diagram">
    <path className="flow-path flow-forward" d="M 120 120 L 180 120" />
    <path className="flow-path flow-forward" d="M 340 120 L 440 120" />
    <path className="flow-path flow-forward" d="M 580 120 L 640 120" />
    <path className="flow-path flow-loop" d="M 260 80 C 260 20, 390 20, 390 80" />
    <path className="flow-path flow-loop-ret" d="M 390 80 C 390 140, 260 140, 260 80" />
    
    <g transform="translate(20, 100)">
      <rect width="100" height="40" rx="6" className="node-rect" />
      <text x="50" y="24" className="node-text">User Task</text>
    </g>
    <g transform="translate(180, 80)">
      <rect width="160" height="80" rx="8" className="node-rect" style={{stroke: '#f59e0b'}} />
      <text x="80" y="30" className="node-text">1. Planner Node</text>
      <text x="80" y="50" className="node-sub">Gemini 2.5 Flash</text>
      <text x="80" y="65" className="node-sub llm-badge">(Low Latency)</text>
    </g>
    <g transform="translate(440, 80)">
      <rect width="140" height="80" rx="8" className="node-rect" style={{stroke: '#7c3aed'}} />
      <text x="70" y="30" className="node-text">2. Synthesizer</text>
      <text x="70" y="50" className="node-sub">Gemini 2.5 Pro</text>
      <text x="70" y="65" className="node-sub llm-badge">(High Reasoning)</text>
    </g>
    <g transform="translate(320, 25)">
      <rect width="140" height="30" rx="15" className="node-rect" style={{stroke: '#34d399'}} />
      <text x="70" y="19" className="node-text">Execute Tools</text>
    </g>
    <g transform="translate(640, 100)">
      <rect width="40" height="40" rx="20" className="node-rect" style={{stroke: '#cbd5e1'}} />
      <text x="20" y="24" className="node-text">End</text>
    </g>
  </svg>
);

export default function App() {
  useEffect(() => {
    console.log('🚀 VigilRAG Production UI loaded correctly. Version: 1.0.1 (Final)');
  }, [])
  const [activeTab, setActiveTab] = useState<'knowledge' | 'agent' | 'documentation'>('knowledge')

  // Knowledge State
  const [query, setQuery] = useState('')
  const [loadingKnowledge, setLoadingKnowledge] = useState(false)
  const [knowData, setKnowData] = useState<KnowledgeResponse | null>(null)

  // Agent State
  const [task, setTask] = useState('')
  const [loadingAgent, setLoadingAgent] = useState(false)
  const [agentData, setAgentData] = useState<{ answer: string; steps: string[] } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showDoc, setShowDoc] = useState(false)

  // Auth State
  const [isLoggedIn, setIsLoggedIn] = useState(apiClient.isLoggedIn())
  const [loginForm, setLoginForm] = useState({ username: '', password: '' })
  const [loadingAuth, setLoadingAuth] = useState(false)

  const clearKnowledge = () => {
    setQuery('')
    setKnowData(null)
    setError(null)
  }

  const clearAgent = () => {
    setTask('')
    setAgentData(null)
    setError(null)
  }

  const runKnowledgeQuery = async () => {
    if (!query.trim()) return
    setLoadingKnowledge(true); setError(null); setKnowData(null)
    try {
      const data = await apiClient.queryKnowledge(query)
      setKnowData(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Knowledge API request failed')
    } finally {
      setLoadingKnowledge(false)
    }
  }

  const runAgentTask = async () => {
    if (!task.trim()) return
    setLoadingAgent(true); setError(null); setAgentData(null)
    try {
      const data = await apiClient.runAgentTask(task)
      setAgentData(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Agent orchestration failed')
    } finally {
      setLoadingAgent(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent, fn: () => void) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) fn()
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoadingAuth(true); setError(null)
    try {
      const { token } = await apiClient.login(loginForm)
      apiClient.setToken(token)
      setIsLoggedIn(true)
    } catch (err: any) {
      setError('Login failed: Invalid credentials.')
    } finally {
      setLoadingAuth(false)
    }
  }

  const handleLogout = () => {
    apiClient.setToken(null)
    setIsLoggedIn(false)
    setLoginForm({ username: '', password: '' })
  }

  if (!isLoggedIn) {
    return (
      <div className="login-page">
        <div className="login-card fade-in">
          <div className="logo mb-24">
            <div className="logo-icon">Ω</div>
            <div className="logo-title">VigilRAG</div>
          </div>
          <h2 className="card-title">Secured Access</h2>
          <p className="card-hint">Please enter your administrative credentials to continue.</p>
          
          <form className="mt-24" onSubmit={handleLogin}>
            <div className="form-group">
              <label>Username</label>
              <input 
                type="text" 
                className="task-input" 
                autoComplete="username"
                value={loginForm.username}
                onChange={e => setLoginForm({...loginForm, username: e.target.value})}
                required 
              />
            </div>
            <div className="form-group mt-16">
              <label>Password</label>
              <input 
                type="password" 
                className="task-input" 
                autoComplete="current-password"
                value={loginForm.password}
                onChange={e => setLoginForm({...loginForm, password: e.target.value})}
                required 
              />
            </div>
            
            {error && <p className="error-text mt-16">{error}</p>}
            
            <button className="btn-primary mt-24 w-full" type="submit" disabled={loadingAuth}>
              {loadingAuth ? 'Verifying...' : 'Login to Console'}
            </button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">
          <div className="logo-icon">Ω</div>
          <div className="logo-title">VigilRAG</div>
        </div>
        <div className="header-status">
          <button className="btn-link logout-btn" onClick={handleLogout}>Logout</button>
          <div className="status-dot" />
          Live · Internal Auth Enabled
        </div>
      </header>

      <main className="app-main">
        <div className="tabs">
          <button
            id="tab-knowledge"
            className={`tab ${activeTab === 'knowledge' ? 'active' : ''}`}
            onClick={() => setActiveTab('knowledge')}
          >
            Knowledge API
          </button>
          <button
            id="tab-agent"
            className={`tab ${activeTab === 'agent' ? 'active' : ''}`}
            onClick={() => setActiveTab('agent')}
          >
            Multi-Agent Orchestrator
          </button>
          <button
            id="tab-documentation"
            className={`tab ${activeTab === 'documentation' ? 'active' : ''}`}
            onClick={() => setActiveTab('documentation')}
          >
            Documentation
          </button>
        </div>

        {activeTab === 'knowledge' && (
          <div className="card fade-in">
            <h2 className="card-title">Knowledge Retrieval API</h2>
            <p className="card-hint">
              Unified semantic retrieval across GitHub repositories, Azure Blob Storage, and SQL databases.
              Returns structured, traceable JSON with stable source IDs — ready for LLM consumption or downstream automation.
            </p>
            <textarea
              id="knowledge-query-input"
              className="task-input"
              rows={3}
              placeholder="e.g., What is our PII policy and how does the auth service handle token validation?"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => handleKeyDown(e, runKnowledgeQuery)}
            />
            <div className="button-group">
              <button
                id="knowledge-submit-btn"
                className="btn-primary"
                onClick={runKnowledgeQuery}
                disabled={loadingKnowledge || !query.trim()}
              >
                {loadingKnowledge ? 'Searching knowledge graph…' : 'Execute Query'}
              </button>
              <button className="btn-secondary" onClick={clearKnowledge} disabled={loadingKnowledge}>
                Clear
              </button>
              <button className="btn-link" onClick={() => setShowDoc(!showDoc)}>
                {showDoc ? 'Hide Details' : 'How it works?'}
              </button>
            </div>

            {showDoc && (
              <div className="doc-panel fade-in">
                <div className="doc-header">
                  <h4>Layer 2 — Knowledge API: Unified Semantic Retrieval</h4>
                  <span className="badge badge-info">System Boundary</span>
                </div>
                
                <div className="doc-content">
                  <div className="svg-diagram-wrapper">
                    <KnowledgeAnimation />
                  </div>
                  
                  <div className="doc-grid-cols">
                    <div className="doc-section">
                      <h5>Architectural Role</h5>
                      <p>The Knowledge API is a <strong>unified semantic retrieval layer</strong> that abstracts enterprise systems into a single predictable interface.</p>
                      <ul>
                        <li><strong>Source Abstraction</strong>: Hides the complexity of GitHub, Azure Blob, and SQL.</li>
                        <li><strong>Trust Boundary</strong>: Enforces safe, read-only data access.</li>
                      </ul>
                    </div>
                    <div className="doc-section">
                      <h5>System Design Properties (Non-LLM)</h5>
                      <ul>
                        <li><strong>Data Contracts</strong>: Normalized JSON schema with stable IDs.</li>
                        <li><strong>Traceability</strong>: All retrieved facts are strictly traceable.</li>
                        <li><strong>LLM Role</strong>: <em>🚫 None.</em> Thorough architectural trace verified this layer operates purely on deterministic regular expressions (`re.findall`) and NLP stop-word tokenization against cloud indices.</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {knowData && (
              <div className="results-container mt-24 fade-in">
                <h4 className="section-heading">Response & Synthesis</h4>
                <p className="synthesis-text">{knowData.answer_synthesis || `Retrieved ${knowData.evidence?.length || 0} evidence records from hybrid semantic search.`}</p>

                {knowData.evidence && knowData.evidence.length > 0 ? (
                  <>
                    <h4 className="section-heading">Source Evidence & Citations (US-010 / US-012)</h4>
                    <div className="facts-grid">
                      {knowData.evidence.map((ev, i) => (
                        <div key={ev.chunk_id || i} className="fact-box">
                          <div className="fact-conf">
                            Score: {(ev.relevance_score * 100).toFixed(1)}% | Ref: {ev.permissions_ref || 'public'}
                          </div>
                          <div style={{ marginTop: '6px' }}>
                            <ReactMarkdown>{ev.content}</ReactMarkdown>
                          </div>

                          <div className="fact-sources" style={{ marginTop: '12px' }}>
                            <span className="code-badge" style={{ backgroundColor: ev.source_id?.includes('wiki') ? '#10b981' : '#3b82f6', color: '#fff' }}>
                              {ev.source_id?.includes('wiki') ? 'Wiki Source' : 'GitHub Source'}
                            </span>
                            &nbsp;
                            <a
                              className="meta-link"
                              href={ev.source_url}
                              target="_blank"
                              rel="noreferrer"
                              style={{ color: '#60a5fa', textDecoration: 'underline' }}
                            >
                              {ev.parent_doc_id || ev.source_url}
                            </a>
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  knowData.facts && (
                    <>
                      <h4 className="section-heading">Extracted Facts</h4>
                      <div className="facts-grid">
                        {knowData.facts.map((f, i) => (
                          <div key={i} className="fact-box">
                            <div className="fact-conf">Confidence: {(f.confidence * 100).toFixed(0)}%</div>
                            <div>{f.fact}</div>
                          </div>
                        ))}
                      </div>
                    </>
                  )
                )}

                <details className="mt-16" style={{ cursor: 'pointer', opacity: 0.85 }}>
                  <summary style={{ fontWeight: 600, color: '#94a3b8' }}>Debug & Execution Trace</summary>

                  <div className="meta-grid mt-12" style={{ padding: '12px', background: '#0f172a', borderRadius: '6px' }}>
                    {knowData.trace_id && (
                      <div className="meta-row">
                        <span className="source-tag">Trace ID</span>
                        <code style={{ color: '#38bdf8' }}>{knowData.trace_id}</code>
                      </div>
                    )}

                    <div className="meta-row">
                      <span className="source-tag">Execution Time</span>
                      <span>{knowData.execution_time_ms} ms</span>
                    </div>

                  </div>

                </details>

              </div>
            )}
          </div>
        )}


        {activeTab === 'agent' && (
          <div className="card fade-in">
            <h2 className="card-title">Multi-Agent Reasoning Engine</h2>
            <p className="card-hint">
              Powered by LangGraph. Decomposes complex, multi-source queries into a
              stateful plan → execute → respond workflow. Uses the Knowledge API as a
              controlled tool — grounded synthesis only, no hallucination.
            </p>
            <textarea
              id="agent-task-input"
              className="task-input"
              rows={3}
              placeholder="e.g., Trace the auth implementation and verify it matches the API Authentication Policy."
              value={task}
              onChange={e => setTask(e.target.value)}
              onKeyDown={e => handleKeyDown(e, runAgentTask)}
            />
            <div className="button-group">
              <button
                id="agent-submit-btn"
                className="btn-primary"
                onClick={runAgentTask}
                disabled={loadingAgent || !task.trim()}
              >
                {loadingAgent ? 'Orchestrating agent…' : 'Delegate to Agent'}
              </button>
              <button className="btn-secondary" onClick={clearAgent} disabled={loadingAgent}>
                Clear
              </button>
              <button className="btn-link" onClick={() => setShowDoc(!showDoc)}>
                {showDoc ? 'Hide Details' : 'How it works?'}
              </button>
            </div>

            {showDoc && (
              <div className="doc-panel fade-in">
                <div className="doc-header">
                  <h4>Layer 3 — Agent Orchestration: Decision & Reasoning Engine</h4>
                  <span className="badge badge-success">LangGraph Stateful</span>
                </div>

                <div className="doc-content">
                  <div className="svg-diagram-wrapper">
                    <AgentAnimation />
                  </div>

                  <div className="doc-grid-cols">
                    <div className="doc-section">
                      <h5>Architectural Role</h5>
                      <p>The multi-agent system is a <strong>stateful orchestration layer</strong> that delegates knowledge retrieval and synthesizes answers.</p>
                      <ul>
                        <li><strong>State Management</strong>: LangGraph maintains graph context continuously.</li>
                        <li><strong>Workflow Control</strong>: Decides tool calls through loops.</li>
                      </ul>
                    </div>
                    <div className="doc-section">
                      <h5>Dual-LLM Node Architecture</h5>
                      <ul>
                        <li><strong>1. Planner Node</strong>: 🤖 <em>Gemini 2.5 Flash</em> — Decomposes tasks with ultra-low latency. Decides parallel tools needed. Iterates until finished.</li>
                        <li><strong>2. Tool Execution</strong>: Triggers parallel `asyncio.gather` tool runs.</li>
                        <li><strong>3. Synthesizer</strong>: 🤖 <em>Gemini 2.5 Pro</em> — Dedicated heavy-lift reasoning node to formulate final answers from facts.</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {loadingAgent && (
              <div className="agent-loader mt-24 fade-in">
                <div className="pulse-ring"></div>
                <div className="loader-text">
                  <strong>Agent orchestrating...</strong>
                  <span>Decomposing query, searching knowledge base, and synthesizing...</span>
                </div>
              </div>
            )}

            {agentData && !loadingAgent && (
              <div className="results-container mt-24 fade-in">
                <div className="agent-meta">
                  <span className="badge badge-info">✓ LangGraph Complete</span>
                  <span className="badge badge-success">{agentData.steps.length} tools executed</span>
                </div>

                <div className="agent-steps fade-in">
                  <h4 className="section-heading">Execution Trace</h4>
                  <ul className="step-timeline">
                    {agentData.steps.map((step, i) => (
                      <li key={i} className="timeline-item">
                        <div className="timeline-dot"></div>
                        <div className="timeline-content">
                          {step}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>

                <h4 className="section-heading">Agent Conclusion</h4>
                <div className="agent-answer">{agentData.answer}</div>
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="card error-card fade-in mt-16">
            <span className="badge badge-error">Error</span>
            <p style={{ marginTop: 8, color: '#f87171', fontSize: '0.9rem' }}>{error}</p>
          </div>
        )}

        {activeTab === 'documentation' && (
          <div className="card fade-in">
            <h2 className="card-title">System Architecture & FAQ</h2>
            <p className="card-hint">
              Detailed knowledgebase covering how VigilRAG operates, its current retrieval mechanisms, and future scalability.
            </p>

            <div className="faq-container mt-16">
              
              {/* Beginner / Non-Tech */}
              <div className="faq-item">
                <div className="faq-badge badge-success">Beginner</div>
                <h3 className="faq-question">How does the agent know the answers? Does it make things up?</h3>
                <p className="faq-answer">
                  The Multi-Agent Orchestrator acts like a very fast researcher. Before it answers your question, it creates a "plan" and reaches out to the Knowledge API. The Knowledge API reads your exact, live company files (from GitHub code and Azure Wiki documents). The agent then summarizes <strong>only</strong> the facts it physically retrieved from those documents. This strictly prevents the AI from "hallucinating" or inventing made-up answers.
                </p>
              </div>

              {/* Technical / Developer */}
              <div className="faq-item">
                <div className="faq-badge badge-info">Technical</div>
                <h3 className="faq-question">Are we using a Vector Database for Semantic Search?</h3>
                <p className="faq-answer">
                  Currently, <strong>no</strong>. While the system performs the overarching workflow of Retrieval-Augmented Generation (RAG), the retrieval layer itself is powered by a high-speed Deterministic Search Engine, not dense vector embeddings. 
                  <br/><br/>
                  When you submit a query, the system strips out stop-words via NLP heuristics (`re.findall`) and searches the resulting tight keywords directly against the official GitHub Search API and via in-memory Regex matching against Azure Blob `.md` streams. There is currently no Pinecone, pgvector, or Milvus database integrated.
                </p>
              </div>

              {/* Expert / Architect */}
              <div className="faq-item">
                <div className="faq-badge badge-accent" style={{background: 'rgba(124, 58, 237, 0.1)', color: '#a78bfa', border: '1px solid rgba(124,58,237,0.3)'}}>Expert / Architect</div>
                <h3 className="faq-question">How can we scale and enhance the retrieval system in the future?</h3>
                <p className="faq-answer">
                  The current regex/keyword-based retrieval limits the system's ability to understand the <em>meaning</em> of concepts (e.g., retrieving a document about "money" when the user asked about "currency"). 
                  <br/><br/>
                  <strong>Future Enhancement Path:</strong> Let's upgrade Layer 2 (The Knowledge API) to true dense vector retrieval. 
                  <br/>1. <strong>Ingestion Pipeline:</strong> Implement a chron job that chunks Azure Wiki documents and GitHub repos into semantic blocks.
                  <br/>2. <strong>Embedding Model:</strong> Use an embedding model (like `text-embedding-3-small` or `text-embedding-004`) to convert those chunks into dense vector coordinates.
                  <br/>3. <strong>Vector Stores:</strong> Store these vectors in Azure AI Search or a dedicated vector DB like Qdrant/Milvus.
                  <br/>4. <strong>Hybrid Search:</strong> Upgrade the router to perform Cosine Similarity searches against the vector DB, augmented with the existing exact-keyword match (BM25) to create a state-of-the-art Hybrid System.
                </p>
              </div>

            </div>
          </div>
        )}
      </main>
    </div>
  )
}
