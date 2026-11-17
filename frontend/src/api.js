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
    const payload = context ? { message, context } : { message };
    return req('/api/chat', { method: 'POST', body: JSON.stringify(payload) });
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
  getWorkerAttendanceHistory: (workerId, days = 30) =>
    req(`/api/workers/${workerId}/attendance-history?days=${days}`),
  applyLeave: (payload) =>
    req('/api/leaves', { method: 'POST', body: JSON.stringify(payload) }),
  getLeaves: (workerId = null) =>
    req(`/api/leaves${workerId ? `?worker_id=${workerId}` : ''}`),
}


