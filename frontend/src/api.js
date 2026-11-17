const BASE = import.meta.env.VITE_API_URL || ''

async function req(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`API error ${res.status}`)
  return res.json()
}

export const api = {
  getWorkers: () => req('/api/workers'),
  getSummary: (days = 30) => req(`/api/analytics/summary?days=${days}`),
  sendChat: (message, context = null) => {
    const payload = context ? { message, context } : { message }
    return req('/api/chat', { method: 'POST', body: JSON.stringify(payload) })
  },
  checkHallucination: (query, response, context = null, retrieval_score = null) =>
    req('/api/safety/check-hallucination', {
      method: 'POST',
      body: JSON.stringify({ query, response, context, retrieval_score }),
    }),
  getDailyBroadcast: () => req('/api/broadcast/daily'),
  getWeeklyInsights: (language = "hi") =>
    req("/api/insights/weekly", {
        method: "POST",
        body: JSON.stringify({
            language,
        }),
    }),
  getWorker: (id) => req(`/api/workers/${id}`),
  updateWorker: (id, data) =>
    req(`/api/workers/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  exportAttendanceCSVUrl: (filters = {}) => {
    const params = new URLSearchParams()
    if (filters.worker_id) params.append('worker_id', filters.worker_id)
    if (filters.status && filters.status !== 'All') params.append('status', filters.status.toLowerCase())
    if (filters.center && filters.center !== 'All') params.append('center', filters.center)
    const qs = params.toString()
    return `${BASE}/api/attendance/export-csv${qs ? `?${qs}` : ''}`
  },
  exportWorkersCSVUrl: (filters = {}) => {
    const params = new URLSearchParams()
    if (filters.center && filters.center !== 'All') params.append('center', filters.center)
    if (filters.role && filters.role !== 'All') params.append('role', filters.role)
    const qs = params.toString()
    return `${BASE}/api/workers/export-csv${qs ? `?${qs}` : ''}`
  },
  importWorkersCSV: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${BASE}/api/workers/import-csv`, {
      method: 'POST',
      body: formData,
    })
    if (!res.ok) throw new Error(`API error ${res.status}`)
    return res.json()
  },
  importAttendanceCSV: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${BASE}/api/attendance/import-csv`, {
      method: 'POST',
      body: formData,
    })
    if (!res.ok) throw new Error(`API error ${res.status}`)
    return res.json()
  },
}


