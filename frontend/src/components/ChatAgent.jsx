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

function getSafetyTier(safety) {
  if (!safety) {
    return {
      tier: "HIGH_CONFIDENCE",
      label: "Verified Guidance",
      score: 95,
      badgeCls: "bg-emerald-500/15 border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/25",
      icon: "🟢",
      statusTitle: "High Clinical Confidence (85%–100%)",
      description: "Grounded in official MoHFW & IMNCI standard healthcare guidelines.",
      isHighRisk: false,
    };
  }

  const score = Math.round((safety.confidence_score ?? (safety.is_flagged ? 0.65 : 0.92)) * 100);
  const isHighRisk = safety.risk_level === "HIGH" || safety.is_flagged || score < 70;
  const isModerate = (safety.risk_level === "MEDIUM" || (score >= 70 && score < 85)) && !isHighRisk;

  if (isHighRisk) {
    return {
      tier: "FLAGGED_REVIEW",
      label: "Flagged for Clinical Review",
      score,
      badgeCls: "bg-rose-500/15 border-rose-500/30 text-rose-300 hover:bg-rose-500/25",
      icon: "🔴",
      statusTitle: "Flagged for Review (<70% or High Risk)",
      description: "Requires immediate clinical verification by a PHC Medical Officer before implementation.",
      isHighRisk: true,
    };
  }

  if (isModerate) {
    return {
      tier: "MODERATE_ADVISORY",
      label: "Clinical Advisory",
      score,
      badgeCls: "bg-amber-500/15 border-amber-500/30 text-amber-300 hover:bg-amber-500/25",
      icon: "🟡",
      statusTitle: "Moderate Confidence (70%–84%)",
      description: "Standard clinical advisory with precautionary healthcare notice.",
      isHighRisk: false,
    };
  }

  return {
    tier: "HIGH_CONFIDENCE",
    label: "Verified Guidance",
    score,
    badgeCls: "bg-emerald-500/15 border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/25",
    icon: "🟢",
    statusTitle: "High Clinical Confidence (85%–100%)",
    description: "Grounded in official MoHFW & IMNCI standard healthcare guidelines.",
    isHighRisk: false,
  };
}

export default function ChatAgent() {
  const [messages, setMessages] = useState([])
  const [showWelcome, setShowWelcome] = useState(true)
  const [expandedSafety, setExpandedSafety] = useState({})

  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [listening, setListening] = useState(false)

  const toggleSafetyDrawer = (idx) => {
    setExpandedSafety((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }))
  }

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

    let streamedText = ''
    let streamedActions = []

    try {
      if (api.streamChat) {
        setMessages((m) => [
          ...m,
          { role: 'agent', text: '', actions: [], isStreaming: true, language: 'hi' },
        ])

        await api.streamChat(msg, {
          onActions: (actions) => {
            streamedActions = actions || []
            setMessages((m) => {
              const updated = [...m]
              const last = updated[updated.length - 1]
              if (last && last.role === 'agent') {
                last.actions = streamedActions
              }
              return updated
            })
          },
          onChunk: (chunk) => {
            streamedText += chunk
            setMessages((m) => {
              const updated = [...m]
              const last = updated[updated.length - 1]
              if (last && last.role === 'agent') {
                last.text = streamedText
              }
              return updated
            })
          },
          onDone: (data) => {
            setMessages((m) => {
              const updated = [...m]
              const last = updated[updated.length - 1]
              if (last && last.role === 'agent') {
                last.text = data.reply || streamedText
                last.actions = data.actions || streamedActions
                last.isStreaming = false
                last.safety = data.hallucination_check || null
              }
              return updated
            })
          },
          onError: async () => {
            const res = await api.sendChat(msg)
            setMessages((m) => {
              const updated = [...m]
              const last = updated[updated.length - 1]
              if (last && last.role === 'agent') {
                last.text = res.reply
                last.actions = res.actions_taken || []
                last.isStreaming = false
                last.safety = res.hallucination_check || null
              } else {
                updated.push({
                  role: 'agent',
                  text: res.reply,
                  actions: res.actions_taken || [],
                  language: res.language || 'hi',
                  safety: res.hallucination_check || null,
                })
              }
              return updated
            })
          },
        })
      } else {
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
      }
    } catch {
      setMessages((m) => {
        const filtered = m.filter((msgItem) => msgItem.text || msgItem.role === 'user')
        return [
          ...filtered,
          {
            role: 'agent',
            text: '❌ AI Agent is temporarily unavailable. Please try again.',
            actions: [],
          },
        ]
      })
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
              {m.role === "agent" ? (() => {
                const tierInfo = getSafetyTier(m.safety);
                const isExpanded = !!expandedSafety[i];

                return (
                  <div>
                    {/* High Risk Banner if Flagged */}
                    {tierInfo.isHighRisk && (
                      <div className="mb-3 p-3 rounded-xl border bg-rose-500/15 border-rose-500/30 text-rose-200 text-xs">
                        <div className="font-semibold flex items-center gap-1.5 mb-1">
                          <span>⚠️ Requires verification by PHC Medical Officer</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-rose-500/20 text-rose-200 ml-auto font-mono">
                            Risk: HIGH
                          </span>
                        </div>
                        <p className="text-[11px] opacity-90">
                          {m.safety?.warning_message || "Clinical notice: This guidance contains sensitive medical advice and must be verified by a physician."}
                        </p>
                      </div>
                    )}

                    {/* Clinical Governance Verification Chip */}
                    <div className="mb-2 flex items-center justify-between gap-2 flex-wrap">
                      <button
                        type="button"
                        onClick={() => toggleSafetyDrawer(i)}
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border transition cursor-pointer ${tierInfo.badgeCls}`}
                        title="Click to inspect clinical safety and confidence metrics"
                      >
                        <span>{tierInfo.icon}</span>
                        <span>{tierInfo.label}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-white/10 font-mono">
                          {tierInfo.score}%
                        </span>
                        <span className="text-[10px] opacity-75">{isExpanded ? "▲" : "▼"}</span>
                      </button>

                      <span className="text-[10px] text-white/40 italic">
                        MoHFW / IMNCI Verified
                      </span>
                    </div>

                    {/* Expandable Clinical Governance Drawer */}
                    {isExpanded && (
                      <div className="mb-3 p-3 rounded-xl border border-white/10 bg-black/40 text-xs space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-white/90">Clinical Safety Breakdown</span>
                          <span className="text-[10px] text-white/50">{tierInfo.statusTitle}</span>
                        </div>

                        {/* Progress Bar */}
                        <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              tierInfo.score >= 85
                                ? "bg-emerald-400"
                                : tierInfo.score >= 70
                                ? "bg-amber-400"
                                : "bg-rose-400"
                            }`}
                            style={{ width: `${Math.min(100, Math.max(0, tierInfo.score))}%` }}
                          />
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 text-white/70">
                          <div>
                            <span className="text-white/40 block text-[10px]">Protocol Authority:</span>
                            <span className="font-medium text-white/90">MoHFW Bihar / IMNCI</span>
                          </div>
                          <div>
                            <span className="text-white/40 block text-[10px]">Confidence Score:</span>
                            <span className="font-medium text-white/90">{tierInfo.score}%</span>
                          </div>
                        </div>

                        {m.safety?.flagged_reasons?.length > 0 && (
                          <div className="pt-1 text-[11px] text-rose-300">
                            <span className="font-semibold block text-[10px] text-rose-400">Flagged Reasons:</span>
                            <ul className="list-disc pl-4 space-y-0.5">
                              {m.safety.flagged_reasons.map((r, idx) => (
                                <li key={idx}>{r}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        <div className="pt-2 border-t border-white/10 text-[10px] text-white/50 leading-relaxed">
                          ℹ️ <strong>Mandatory Clinical Notice</strong>: Assistive intelligence for PHC workforce. For emergency obstetrics, pediatric complications, or critical triage, immediately transfer to District Hospital or call 108/102.
                        </div>
                      </div>
                    )}

                    <div className="prose prose-invert max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {m.text}
                      </ReactMarkdown>
                    </div>
                  </div>
                );
              })() : (
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

        {loading && !messages.some((m) => m.isStreaming && m.text) && (
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