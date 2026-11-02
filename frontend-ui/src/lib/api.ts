// Thin client over the FastAPI backend (backend/app/api/v1/endpoints/contracts.py).
// Only endpoints that exist today live here; ML-backed features go through lib/analysis.ts.

export type Contract = {
  id: string
  filename: string
  status: string
  extracted_text: string | null
  clauses: unknown
  created_at: string
  updated_at: string
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

const BASE = import.meta.env.VITE_API_URL ?? '/api/v1'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(BASE + path, init)
  } catch {
    console.warn(`Fineprint: could not reach the API at ${BASE}. Is the backend running?`)
    throw new ApiError(0, 'We cannot connect right now. Please check your internet connection and try again in a moment.')
  }
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      /* keep statusText */
    }
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<T>
}

export function uploadContract(file: File): Promise<Contract> {
  const form = new FormData()
  form.append('file', file)
  return request<Contract>('/contracts/upload', { method: 'POST', body: form })
}

export const extractContract = (id: string) =>
  request<Contract>(`/contracts/${id}/extract`, { method: 'POST' })

export const getContract = (id: string) => request<Contract>(`/contracts/${id}`)

// ── analysis endpoints (backend `develop`: ML pipeline). Older backends answer 404; callers fall back. ──
export type ClauseView = {
  category: string
  text: string
  risk_label: string // HIGH | MEDIUM | LOW
  risk_score: number // 0-100
  reasons: string[]
  page: number | null
}

export type RiskSummary = { overall_score: number; level: string; high: number; medium: number; low: number }

export type AnalysisOut = {
  id: string
  filename: string
  uploaded_at: string
  num_pages: number | null
  clauses: ClauseView[]
  risk_summary: RiskSummary
  entities: {
    parties?: Record<string, { name: string }>
    rent?: { value: string } | null
    deposit?: { value: string } | null
    money_mentions?: { value: string }[]
    dates?: { value: string }[]
    notice_periods?: { value: string }[]
  }
}

export type AskOut = { answer: string; evidence: { text: string; page: number | null; similarity: number }[] }

/** Runs the ML pipeline and stores the clauses on the contract. Can take a while on first use. */
export const analyzeContract = (id: string) => request<Contract>(`/contracts/${id}/analyze`, { method: 'POST' })

export const getAnalysis = (id: string) => request<AnalysisOut>(`/contracts/${id}/analysis`)

export const askContract = (id: string, question: string) =>
  request<AskOut>(`/contracts/${id}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })

/** Turn backend error text into something a non-lawyer can act on. */
export function friendlyError(e: unknown): string {
  if (!(e instanceof ApiError)) return 'Something went wrong. Please try again.'
  if (e.status === 0) return e.message
  if (e.status === 404) return 'We could not find that contract. It may have been removed.'
  if (e.status === 409) return 'That contract has not been analysed yet.'
  if (e.status === 502) return 'Our analysis tool is not responding right now. Please try again in a moment.'
  if (e.status === 503) return 'Our analysis tool is busy. Please try again in a few seconds.'
  if (e.status === 422) return 'We could not find any readable text in this file. Photos or scans of paper cannot be read yet. Please try a PDF, Word document or text file made on a computer.'
  if (e.status === 400) {
    const m = e.message.toLowerCase()
    if (m.includes('empty')) return 'That file is empty.'
    if (m.includes('exceeds')) return 'That file is too large. The limit is 10 MB.'
    if (m.includes('unsupported')) return 'That type of file is not supported. Please use a PDF, Word document or text file.'
    if (m.includes('does not match')) return 'That file does not look like a real PDF or Word document. It may be damaged. Try saving it again, or upload a different version.'
    return 'We could not use that file. Please try a different one.'
  }
  return 'Something went wrong on our side. Please try again.'
}
