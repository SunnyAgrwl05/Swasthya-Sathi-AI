import { useState } from "react";
import { api } from "../api";

export default function DailyBroadcast() {
    const [message, setMessage] = useState(null);
    const [loading, setLoading] = useState(false);
    const [smsLoading, setSmsLoading] = useState(false);
    const [smsResult, setSmsResult] = useState(null);

    async function generate() {
        setLoading(true);
        setSmsResult(null);

        try {
            const res = await api.getDailyBroadcast();
            setMessage(res.message);
        } catch {
            setMessage("Backend se connect nahi ho pa raha.");
        } finally {
            setLoading(false);
        }
    }

    async function handleDispatchSMS() {
        if (!message) return;
        setSmsLoading(true);
        try {
            const res = await api.dispatchSMSAlerts({
                message,
                target: "all",
            });
            setSmsResult(res);
        } catch {
            setSmsResult({
                status: "failed",
                total_recipients: 0,
                sent: 0,
                failed: 1,
                errors: ["Failed to connect to SMS dispatch service"],
            });
        } finally {
            setSmsLoading(false);
        }
    }

    const waLink = message
        ? "https://wa.me/?text=" +
        encodeURIComponent(message.replace(/\*/g, ""))
        : "#";

    const lines = message ? message.split("\n") : [];

    return (
        <div className="glass p-4 sm:p-5 mb-6 fade-up">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
                <div>
                    <h2 className="font-display font-semibold text-sm text-white/90">
                        📢 Daily Broadcast
                    </h2>

                    <p className="text-xs text-white/50 mt-1">
                        AI-generated daily operational update
                    </p>
                </div>

                <button
                    onClick={generate}
                    disabled={loading}
                    className="w-full sm:w-auto text-xs px-4 py-2 rounded-xl bg-white/5 border border-line hover:border-pulse/40 hover:text-pulse transition-colors disabled:opacity-50"
                >
                    {loading
                        ? "Generating..."
                        : message
                            ? "🔄 Regenerate"
                            : "✨ Generate Today's Update"}
                </button>
            </div>

            {message && (
                <div className="fade-up">
                    <div className="bg-[#0b1a12] border border-pulse/20 rounded-2xl rounded-tl-sm px-4 py-4 text-sm whitespace-pre-wrap leading-relaxed overflow-x-auto">
                        {lines.map((line, i) => (
                            <div
                                key={i}
                                className={
                                    i === 0
                                        ? "font-semibold text-pulse mb-2"
                                        : "text-white/80"
                                }
                            >
                                {line.replace(/\*/g, "")}
                            </div>
                        ))}
                    </div>

                    <div className="flex flex-wrap items-center gap-3 mt-4">
                        <a
                            href={waLink}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center justify-center w-full sm:w-auto gap-2 text-xs px-4 py-2 rounded-xl bg-pulse/10 text-pulse border border-pulse/25 hover:bg-pulse/20 transition-colors"
                        >
                            📲 Share on WhatsApp
                        </a>

                        <button
                            type="button"
                            onClick={handleDispatchSMS}
                            disabled={smsLoading}
                            className="inline-flex items-center justify-center w-full sm:w-auto gap-2 text-xs px-4 py-2 rounded-xl bg-blue-500/15 text-blue-300 border border-blue-500/30 hover:bg-blue-500/25 transition-colors disabled:opacity-50 cursor-pointer"
                        >
                            {smsLoading ? "📡 Transmitting SMS..." : "📨 Dispatch SMS Alerts"}
                        </button>
                    </div>

                    {smsResult && (
                        <div
                            className={`mt-3 p-3 rounded-xl border text-xs leading-relaxed ${
                                smsResult.failed === 0
                                    ? "bg-emerald-500/10 border-emerald-500/25 text-emerald-300"
                                    : "bg-amber-500/10 border-amber-500/25 text-amber-300"
                            }`}
                        >
                            <span className="font-semibold">
                                {smsResult.failed === 0 ? "✓ SMS Broadcast Dispatched:" : "⚠️ Dispatch Notice:"}
                            </span>{" "}
                            {smsResult.sent} messages delivered to offline field workers ({smsResult.failed} failed).
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}