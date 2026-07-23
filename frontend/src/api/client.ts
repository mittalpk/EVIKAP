/**
 * VigilRAG API Client — typed wrappers for backend and agent services.
 */
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? '/api'
const AGENT_URL   = import.meta.env.VITE_AGENT_URL   ?? BACKEND_URL

let authToken: string | null = localStorage.getItem('vigilrag_token')

async function request<T>(url: string, options: RequestInit = {}, timeoutMs = 10000): Promise<T> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  const headers = new Headers(options.headers || {})
  headers.set('Content-Type', 'application/json')
  
  if (authToken) {
    headers.set('Authorization', `Bearer ${authToken}`)
  }

  try {
    const res = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
      credentials: 'include',  // Include cookies and credentials for CORS
    })
    clearTimeout(timeoutId)

    if (res.status === 401) {
      localStorage.removeItem('vigilrag_token')
      window.location.reload()
    }

    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
    return res.json() as Promise<T>
  } catch (err: any) {
    clearTimeout(timeoutId)
    if (err.name === 'AbortError') {
      throw new Error(`Request timed out after ${timeoutMs / 1000}s. Please check backend connectivity.`)
    }
    throw err
  }
}


export interface UnifiedFact {
  fact: string;
  confidence: number;
  derived_from_stable_ids: string[];
}

export interface SourceMetadata {
  source_system: string;
  stable_id: string;
  timestamp: string;
  url: string;
}

export interface EvidenceItem {
  chunk_id: string;
  content: string;
  source_url: string;
  relevance_score: number;
  source_id: string;
  parent_doc_id?: string;
  references?: string[];
  permissions_ref?: string;
}


export interface HybridRetrievalResponse {
  evidence: EvidenceItem[];
  trace_id: string;
  execution_time_ms: number;
  query: string;
  total_retrieved: number;
}

export interface KnowledgeResponse {
  answer_synthesis: string;
  facts: UnifiedFact[];
  metadata: SourceMetadata[];
  execution_time_ms: number;
  evidence?: EvidenceItem[];
  trace_id?: string;
}

export const apiClient = {
  setToken: (token: string | null) => {
    authToken = token
    if (token) localStorage.setItem('vigilrag_token', token)
    else localStorage.removeItem('vigilrag_token')
  },

  isLoggedIn: () => !!authToken,

  login: (credentials: { username: string; password: string }) =>
    request<{ token: string }>(`${BACKEND_URL}/api/v1/auth/login`, {
      method: 'POST',
      body: JSON.stringify(credentials)
    }),

  checkHealth: () =>
    request<{ status: string; service: string }>(`${BACKEND_URL}/health`),

  queryKnowledge: (query: string, target_systems: string[] = ["confluence", "code_repos", "databases"], top_k: number = 5) =>
    request<HybridRetrievalResponse & KnowledgeResponse>(
      `${BACKEND_URL}/api/v1/knowledge/query`,
      { method: 'POST', body: JSON.stringify({ query, target_systems, top_k }) }
    ),

  runAgentTask: (task: string, max_iterations = 10) =>
    request<{ task: string; answer: string; steps: string[] }>(
      `${AGENT_URL}/api/v1/agent/run`,
      { method: 'POST', body: JSON.stringify({ task, max_iterations }) }
    ),
}

