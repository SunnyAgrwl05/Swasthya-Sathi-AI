import { useEffect, useState } from 'react'
import Header from './components/Header'
import StatCards from './components/StatCards'
import AttendanceChart from './components/AttendanceChart'
import WorkerTable from './components/WorkerTable'
import ChatAgent from './components/ChatAgent'
import DailyBroadcast from './components/DailyBroadcast'
import WeeklyInsights from './components/WeeklyInsights'
import { api } from './api'

export default function App() {
  const [workers, setWorkers] = useState([])
  const [summary, setSummary] = useState([])
  const [error, setError] = useState(null)

  async function load() {
    try {
      const [w, s] = await Promise.all([api.getWorkers(), api.getSummary()])
      setWorkers((prev) => (JSON.stringify(prev) === JSON.stringify(w) ? prev : w))
      setSummary((prev) => (JSON.stringify(prev) === JSON.stringify(s) ? prev : s))
      setError(null)
    } catch (e) {
      setError('Backend se connect nahi ho pa raha. Kya uvicorn chal raha hai localhost:8000 par?')
    }
  }

  useEffect(() => {
    load()
    const id = setInterval(load, 60000) // refresh so agent-made changes show up live
    return () => clearInterval(id)
  }, [])

  return (
    <div className="min-h-screen px-4 md:px-8 py-6 max-w-[1400px] mx-auto">
      <Header />

      {error && (
        <div className="glass p-4 mb-6 border-danger/30 text-danger text-sm">{error}</div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_420px] gap-6 items-start">        <div>
        <StatCards workers={workers} summary={summary} />
        <DailyBroadcast />
        <AttendanceChart summary={summary} />
        <WeeklyInsights />
        <WorkerTable workers={workers} summary={summary} />
      </div>
        <div>
          <ChatAgent />
        </div>
      </div>

      <footer className="text-center text-white/25 text-xs mt-10 pb-4">
        AI-powered Rural Health Workforce Management • Swasthya Sathi AI
      </footer>
    </div>
  )
}