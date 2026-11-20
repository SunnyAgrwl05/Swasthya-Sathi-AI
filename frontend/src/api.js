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
    const payload = { message }
    if (context !== null && context !== undefined) {
      payload.context = context
    }
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
  getWorkerAttendanceHistory: (workerId, days = 30) =>
    req(`/api/workers/${workerId}/attendance-history?days=${days}`),
  applyLeave: (payload) =>
    req('/api/leaves', { method: 'POST', body: JSON.stringify(payload) }),
  getLeaves: (workerId = null) =>
    req(`/api/leaves${workerId ? `?worker_id=${workerId}` : ''}`),
  updateLeaveStatus: (leaveId, status, approvedBy = "Supervisor") =>
    req(`/api/leaves/${leaveId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, approved_by: approvedBy }),
    }),
  getSMSQueue: (status = null) =>
    req(`/api/notifications/queue${status ? `?status=${status}` : ""}`),
  processSMSQueue: () =>
    req("/api/notifications/queue/process", { method: "POST" }),
  dispatchSMSAlerts: (payload = {}) =>
    req('/api/notifications/dispatch-sms', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getNotificationLogs: (limit = 20) =>
    req(`/api/notifications/logs?limit=${limit}`),
  importWorkersCsv: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${BASE}/api/workers/import-csv`, {
      method: 'POST',
      body: formData,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `API error ${res.status}`)
    }
    return res.json()
  },
  exportAttendanceCsvUrl: (month, center) => {
    const params = new URLSearchParams()
    if (month) params.append('month', month)
    if (center && center !== 'All') params.append('center', center)
    return `${BASE}/api/attendance/export-csv?${params.toString()}`
  },
  sampleWorkersCsvUrl: `${BASE}/api/workers/sample-csv`,
}


