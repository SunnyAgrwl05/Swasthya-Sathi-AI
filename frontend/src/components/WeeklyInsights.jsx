import { useState } from "react";
import { api } from "../api";

export default function WeeklyInsights() {
    const [report, setReport] = useState("");
    const [loading, setLoading] = useState(false);

    async function runAnalysis() {
        setLoading(true);

        try {
            const res = await api.getWeeklyInsights();

            // Backend string ya object dono handle karega
            if (typeof res === "string") {
                setReport(res);
            } else {
                setReport(res.report || "");
            }
        } catch (err) {
            console.error(err);
            setReport("Unable to generate weekly attendance insights.");
        }

        setLoading(false);
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

                <button
                    onClick={runAnalysis}
                    disabled={loading}
                    className="px-4 py-2 rounded-xl border border-line bg-white/5 hover:bg-white/10 transition text-sm"
                >
                    {loading ? "Generating..." : "Run weekly analysis"}
                </button>
            </div>

            {report ? (
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

