import { useState } from "react";
import { api } from "../api";

export default function WeeklyInsights() {
    const [report, setReport] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [language, setLanguage] = useState("hi");

    async function runAnalysis(langOverride) {
        const lang = langOverride || language;
        setLoading(true);
        setError("");

        try {
            const res = await api.getWeeklyInsights(lang);

            // Backend string ya object dono handle karega
            if (typeof res === "string") {
                setReport(res);
            } else {
                setReport(res.report || "");
            }
        } catch (err) {
            console.error(err);
            setError("Unable to generate weekly attendance insights. Please try again.");
        } finally {
            setLoading(false);
        }
    }

    function switchLanguage(lang) {
        setLanguage(lang);
        if (report) {
            runAnalysis(lang);
        }
    }

    return (
        <div className="glass p-4 sm:p-5 fade-up mb-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
                <div>
                    <h2 className="font-display font-semibold text-white text-base">
                        📊 AI Insights Agent
                    </h2>

                    <p className="text-xs text-white/50 mt-1">
                        Weekly Attendance Intelligence
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1 rounded-xl border border-line bg-white/5 p-1">
                        <button
                            disabled={loading}
                            onClick={() => switchLanguage("hi")}
                            className={`px-3 py-1.5 rounded-lg text-sm transition ${language === "hi"
                                    ? "bg-cyan-500/20 text-cyan-300"
                                    : "text-white/50 hover:text-white/80"
                                }`}
                        >
                            हिंदी
                        </button>

                        <button
                            disabled={loading}
                            onClick={() => switchLanguage("en")}
                            className={`px-3 py-1.5 rounded-lg text-sm transition ${language === "en"
                                    ? "bg-cyan-500/20 text-cyan-300"
                                    : "text-white/50 hover:text-white/80"
                                }`}
                        >
                            English
                        </button>
                    </div>

                    <button
                        onClick={() => runAnalysis()}
                        disabled={loading}
                        className="px-4 py-2 rounded-xl border border-line bg-white/5 hover:bg-white/10 transition text-sm disabled:cursor-not-allowed disabled:opacity-60"
                    >
                        {loading ? "Generating..." : "Run weekly analysis"}
                    </button>
                </div>
            </div>

            {loading ? (
                <div
                    className="rounded-xl border border-line bg-white/5 p-4 space-y-3"
                    role="status"
                    aria-live="polite"
                    aria-label="Generating weekly attendance insights"
                >
                    <div className="h-3 w-2/3 animate-pulse rounded-full bg-white/15" />
                    <div className="h-3 w-full animate-pulse rounded-full bg-white/10" />
                    <div className="h-3 w-5/6 animate-pulse rounded-full bg-white/10" />
                    <div className="h-3 w-1/2 animate-pulse rounded-full bg-white/10" />
                </div>
            ) : error ? (
                <div
                    className="rounded-xl border border-danger/30 bg-danger/10 p-4 text-sm text-danger"
                    role="alert"
                >
                    {error}
                </div>
            ) : report ? (
                <div className="rounded-xl border border-line bg-white/5 p-4 text-sm leading-7 whitespace-pre-wrap text-white/90">
                    {report}
                </div>
            ) : (
                <div className="rounded-xl border border-dashed border-line p-6 text-center text-white/40 text-sm">
                    Click <span className="text-cyan-300">Run weekly analysis</span> to
                    generate AI-powered attendance insights.
                </div>
            )}
        </div>
    );
}
