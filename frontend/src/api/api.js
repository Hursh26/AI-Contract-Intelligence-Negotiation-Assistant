import axios from 'axios'

// Dev: Vite proxies /api -> http://localhost:8000 (see vite.config.js), so the
// base is same-origin. Production: VITE_API_URL points at the deployed backend.
const client = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL || ''}/api/v1`,
  timeout: 30000,
})

// Analysis runs the ML pipeline (first call may download models), so give it
// far longer than a normal request.
const ANALYZE_TIMEOUT_MS = 180000

// Upload the file, then run extraction + ML analysis on it.
// Resolves to { document_id } — the contract id used by every other call.
export const uploadDocument = async (file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)
  const uploaded = await client.post('/contracts/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (evt) => {
      if (onProgress && evt.total) {
        onProgress(Math.round((evt.loaded * 100) / evt.total))
      }
    },
  })
  const id = uploaded.data.id
  await client.post(`/contracts/${id}/analyze`, null, { timeout: ANALYZE_TIMEOUT_MS })
  return { document_id: id }
}

// Clauses, risk summary and entities for one analyzed contract.
export const getDocument = async (id) => {
  const res = await client.get(`/contracts/${id}/analysis`)
  return res.data
}

// Analyzed contracts, newest first.
export const getHistory = async () => {
  const res = await client.get('/contracts')
  return res.data
}

// Ask a question about one contract; resolves to { answer, evidence: [...] }.
export const askQuestion = async (documentId, question) => {
  const res = await client.post(`/contracts/${documentId}/ask`, { question }, { timeout: ANALYZE_TIMEOUT_MS })
  return res.data
}

export default client
