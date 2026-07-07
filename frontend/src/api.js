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
  sendChat: (message) => req('/api/chat', { method: 'POST', body: JSON.stringify({ message }) }),
  getDailyBroadcast: () => req('/api/broadcast/daily'),
  getWeeklyInsights: (language = "hi") =>
    req("/api/insights/weekly", {
        method: "POST",
        body: JSON.stringify({
            language,
        }),
    }),
}


