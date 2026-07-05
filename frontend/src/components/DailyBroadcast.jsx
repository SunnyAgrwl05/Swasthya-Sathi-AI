import { useState } from "react";
import { api } from "../api";

export default function DailyBroadcast() {
    const [message, setMessage] = useState(null);
    const [loading, setLoading] = useState(false);

    async function generate() {
        setLoading(true);

        try {
            const res = await api.getDailyBroadcast();
            setMessage(res.message);
        } catch {
            setMessage("Backend se connect nahi ho pa raha.");
        } finally {
            setLoading(false);
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

                    <a
                        href={waLink}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center justify-center w-full sm:w-auto gap-2 mt-4 text-xs px-4 py-2 rounded-xl bg-pulse/10 text-pulse border border-pulse/25 hover:bg-pulse/20 transition-colors"
                    >
                        📲 Share on WhatsApp
                    </a>
                </div>
            )}
        </div>
    );
}