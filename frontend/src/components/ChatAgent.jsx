import { useState, useRef, useEffect } from 'react'
import { api } from '../api'
import { generateAttendancePDF } from '../utils/pdfExport'

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";


const SUGGESTIONS = [
  'Sunny Kumar ko aaj present mark karo',
  'Kajal Kumari ka attendance summary dikhao',
  'Is month sabse kam attendance kiski hai?',
  'Aaj kisne attendance nahi mark ki?',
]

export default function ChatAgent() {
  const [messages, setMessages] = useState([])
  const [showWelcome, setShowWelcome] = useState(true)
  const [expandedSafetyIndex, setExpandedSafetyIndex] = useState(null)

  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [listening, setListening] = useState(false)

  const bottomRef = useRef(null)
  const recognitionRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: 'auto',
      block: 'end',
    })
  }, [messages])

  const speechSupported =
    typeof window !== 'undefined' &&
    (window.SpeechRecognition || window.webkitSpeechRecognition)

  function toggleVoice() {
    if (!speechSupported) return

    if (listening) {
      recognitionRef.current?.stop()
      return
    }

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition

    const recognition = new SpeechRecognition()

    recognition.lang = 'hi-IN'
    recognition.interimResults = false
    recognition.maxAlternatives = 1

    recognition.onstart = () => setListening(true)
    recognition.onend = () => setListening(false)
    recognition.onerror = () => setListening(false)

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      setInput(transcript)
      send(transcript)
    }

    recognitionRef.current = recognition
    recognition.start()
  }

  function downloadPDF(text, language = "hi") {
    generateAttendancePDF(text, language)
  }


  async function send(text) {
    const msg = (text ?? input).trim()

    if (!msg || loading) return

    setMessages((m) => [...m, { role: 'user', text: msg }])
    setShowWelcome(false)

    setInput('')
    setLoading(true)

    try {
      const res = await api.sendChat(msg)

      setMessages((m) => [
        ...m,
        {
          role: 'agent',
          text: res.reply,
          actions: res.actions_taken || [],
          language: res.language || "hi",
          safety: res.hallucination_check || null,
        },
      ])
    } catch {
      setMessages((m) => [
        ...m,
        {
          role: 'agent',
          text: '❌ AI Agent is temporarily unavailable. Please try again.',
          actions: [],
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="glass flex flex-col h-full min-h-[520px] lg:sticky lg:top-6">
      <div className="p-4 border-b border-line flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-pulse animate-pulse" />
        <h2 className="font-display font-semibold text-sm">🤖 AI Operations Agent</h2>
        <span className="text-[10px] text-white/35 ml-auto">
          AI Multi-Agent Runtime
        </span>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-3">
        {showWelcome && (
          <div className="flex justify-start">
            <div className="max-w-[90%] sm:max-w-[85%] rounded-2xl rounded-bl-sm bg-white/5 border border-line shadow-lg px-3.5 py-2.5 text-sm leading-relaxed whitespace-pre-wrap">
              {`👋 Welcome to Swasthya Sathi AI

AI Operations Agent
Bihar Health Department

I monitor and manage attendance across the Bihar PHC Network.

Capabilities

✅ Mark attendance
📊 Attendance summaries
⚠ Detect low attendance
📈 Weekly analytics
📢 Daily operational reports

Ask me:

• Mark Sunny Kumar present today
• Show Kajal Kumari attendance summary
• Who has the lowest attendance this month?
• Who has not marked attendance today?`}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={`${m.role}-${i}-${m.text.slice(0, 20)}`}
            className={`flex ${m.role === 'user'
              ? 'justify-end'
              : 'justify-start'
              }`}
          >
            <div
              className={`max-w-[90%] sm:max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${m.role === 'user'
                ? 'bg-gradient-to-br from-pulse2 to-pulse2/70 text-white rounded-br-sm'
                : 'bg-white/5 border border-line rounded-bl-sm shadow-lg'
                }`}
            >
              {m.role === "agent" ? (
                <div>
                  {/* Verification Status Chip & Clinical Safety Audit */}
                  <div className="mb-2.5">
                    {m.safety ? (
                      <div className="inline-block">
                        <button
                          type="button"
                          onClick={() => setExpandedSafetyIndex(expandedSafetyIndex === i ? null : i)}
                          aria-expanded={expandedSafetyIndex === i}
                          className={`inline-flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-1 rounded-full border transition-all cursor-pointer ${
                            m.safety.risk_level === 'HIGH'
                              ? 'bg-red-500/15 border-red-500/35 text-red-200 hover:bg-red-500/25'
                              : m.safety.risk_level === 'MEDIUM'
                              ? 'bg-amber-500/15 border-amber-500/35 text-amber-200 hover:bg-amber-500/25'
                              : 'bg-emerald-500/15 border-emerald-500/35 text-emerald-200 hover:bg-emerald-500/25'
                          }`}
                          title="Click to view clinical safety audit"
                        >
                          <span>
                            {m.safety.risk_level === 'HIGH'
                              ? '🚨 High Clinical Risk'
                              : m.safety.risk_level === 'MEDIUM'
                              ? '⚠️ Clinical Caution'
                              : '🛡️ MoHFW Verified'}
                          </span>
                          <span className="opacity-80">
                            • {Math.round((m.safety.confidence_score || 0) * 100)}%
                          </span>
                          <span className="text-[9px] opacity-60 ml-0.5">
                            {expandedSafetyIndex === i ? '▲' : '▼'}
                          </span>
                        </button>

                        {expandedSafetyIndex === i && (
                          <div className="mt-2 p-3 rounded-xl bg-slate-900/95 border border-white/10 text-xs shadow-xl space-y-2 text-slate-200">
                            <div className="flex items-center justify-between border-b border-white/10 pb-1.5 font-semibold text-[11px]">
                              <span className="text-white">Clinical Safety & Hallucination Audit</span>
                              <span className="text-pulse2">
                                Confidence: {Math.round((m.safety.confidence_score || 0) * 100)}%
                              </span>
                            </div>
                            <div>
                              <span className="font-medium text-slate-400 block text-[10px] uppercase tracking-wider">Cited Protocol</span>
                              <span className="text-[11px] text-slate-200">
                                MoHFW / National Health Mission (NHM) Bihar Standard Clinical Guidelines
                              </span>
                            </div>
                            {m.safety.flagged_reasons?.length > 0 ? (
                              <div>
                                <span className="font-medium text-amber-300 block text-[10px] uppercase tracking-wider">Caveats & Findings</span>
                                <ul className="list-disc pl-4 space-y-0.5 text-[11px] text-amber-100">
                                  {m.safety.flagged_reasons.map((reason, rIdx) => (
                                    <li key={rIdx}>{reason}</li>
                                  ))}
                                </ul>
                              </div>
                            ) : (
                              <div>
                                <span className="font-medium text-emerald-300 block text-[10px] uppercase tracking-wider">Caveats & Findings</span>
                                <p className="text-[11px] text-emerald-100">No clinical hallucinations or protocol contradictions detected.</p>
                              </div>
                            )}
                            {m.safety.warning_message && (
                              <div>
                                <span className="font-medium text-red-300 block text-[10px] uppercase tracking-wider">Clinical Warning</span>
                                <p className="text-[11px] text-red-100 leading-relaxed">{m.safety.warning_message}</p>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 text-[11px] px-2.5 py-0.5 rounded-full bg-slate-500/15 text-slate-300 border border-slate-500/20">
                        📋 Operational Query
                      </span>
                    )}
                  </div>

                  {/* Mandatory Medical Disclaimer for High Clinical Risk Queries */}
                  {m.safety?.risk_level === 'HIGH' && (
                    <div className="mb-3 p-3 rounded-xl border bg-red-500/15 border-red-500/30 text-red-200 text-xs">
                      <div className="font-semibold flex items-center gap-1.5 mb-1 text-red-100">
                        <span>🚨 Mandatory Medical Disclaimer</span>
                      </div>
                      <p className="text-[11px] leading-relaxed">
                        This response involves high-risk clinical advice. Generated for operational guidance only and cannot replace clinical judgment by a licensed Medical Officer. Verify with PHC Medical Officer before clinical administration.
                      </p>
                    </div>
                  )}

                  <div className="prose prose-invert max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {m.text}
                    </ReactMarkdown>
                  </div>
                </div>
              ) : (
                <div className="whitespace-pre-wrap">
                  {m.text}
                </div>
              )}

              {m.actions?.length > 0 && (
                <div className="mt-2 pt-2 border-t border-white/10 flex flex-wrap gap-1.5">
                  {m.actions.map((a, j) => (
                    <span
                      key={j}
                      className="text-[10px] px-2 py-0.5 rounded-full bg-pulse/15 text-pulse border border-pulse/25"
                    >
                      ✓ {a}
                    </span>
                  ))}
                </div>
              )}

              {m.role === "agent" && i > 0 && (
                <div className="mt-3 flex gap-2">
                  <button
                    onClick={() => downloadPDF(m.text,m.language)}
                    className="text-xs px-3 py-2 rounded-lg bg-green-600 hover:bg-green-700 transition-colors text-white"
                  >
                    📄 Download PDF
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white/5 border border-line rounded-2xl rounded-bl-sm px-4 py-3 text-sm text-white/70">
              🧠 Processing...
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="p-3 flex flex-wrap gap-1.5 border-t border-line">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => send(s)}
            className="text-[11px] px-3 py-1 rounded-full border border-line text-white/50 hover:text-pulse hover:border-pulse/40"
          >
            {s}
          </button>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          send()
        }}
        className="p-3 border-t border-line flex items-center gap-2"
      >
        <input
          autoFocus
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            listening
              ? 'Sun raha hoon…'
              : 'Type in Hindi, English or Hinglish…'
          }
          className="flex-1 bg-white/5 border border-line rounded-xl px-4 py-2.5 text-sm outline-none focus:border-pulse/50 placeholder:text-white/30 transition-colors"
        />

        {speechSupported && (
          <button
            type="button"
            onClick={toggleVoice}
            className={`w-11 h-11 flex items-center justify-center rounded-xl border ${listening
              ? 'bg-danger/20 border-danger/40 text-danger animate-pulse'
              : 'bg-white/5 border-line text-white/50 hover:text-pulse hover:border-pulse/40'
              }`}
          >
            🎤
          </button>
        )}

        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-br from-pulse to-pulse2 text-[#080B10] font-semibold hover:scale-105 transition-transform disabled:opacity-50 disabled:hover:scale-100"
        >
          Send
        </button>
      </form>
    </div>
  )
}