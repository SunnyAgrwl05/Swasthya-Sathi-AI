import { useState, useEffect, useCallback } from "react";
import { api } from "../api";

export default function WorkerDetailModal({ worker, onClose, onLeaveApplied }) {
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [leaveLoading, setLeaveLoading] = useState(false);
  const [leaveSuccess, setLeaveSuccess] = useState(null);
  const [leaveError, setLeaveError] = useState(null);

  const today = new Date().toISOString().split("T")[0];
  const [startDate, setStartDate] = useState(today);
  const [endDate, setEndDate] = useState(today);
  const [leaveType, setLeaveType] = useState("casual");
  const [reason, setReason] = useState("");

  const loadHistory = useCallback(async () => {
    if (!worker?.id) return;
    setLoading(true);
    try {
      const data = await api.getWorkerAttendanceHistory(worker.id, 30);
      setHistory(data);
    } catch {
      // fallback empty state
    } finally {
      setLoading(false);
    }
  }, [worker?.id]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  async function handleApplyLeave(e) {
    e.preventDefault();
    if (!startDate || !endDate) return;
    setLeaveLoading(true);
    setLeaveError(null);
    setLeaveSuccess(null);

    try {
      const res = await api.applyLeave({
        worker_id: worker.id,
        start_date: startDate,
        end_date: endDate,
        leave_type: leaveType,
        reason: reason || undefined,
      });
      setLeaveSuccess(`✓ Approved ${res.leave_type} leave from ${res.start_date} to ${res.end_date}`);
      setReason("");
      await loadHistory();
      if (onLeaveApplied) onLeaveApplied();
    } catch (err) {
      setLeaveError(err.message || "Failed to submit leave request.");
    } finally {
      setLeaveLoading(false);
    }
  }

  if (!worker) return null;

  function tileColor(status) {
    switch (status) {
      case "present":
        return "bg-emerald-500/80 border-emerald-400/90 text-white shadow-emerald-500/20";
      case "absent":
        return "bg-rose-500/80 border-rose-400/90 text-white shadow-rose-500/20";
      case "half-day":
        return "bg-amber-500/80 border-amber-400/90 text-white shadow-amber-500/20";
      case "leave":
        return "bg-purple-500/80 border-purple-400/90 text-white shadow-purple-500/20";
      default:
        return "bg-slate-800/80 border-slate-700/80 text-slate-400";
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="worker-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/70 backdrop-blur-sm animate-fade-in"
    >
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-slate-900 border border-white/10 rounded-2xl p-5 sm:p-6 shadow-2xl text-slate-200">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-white/10 pb-4 mb-5">
          <div>
            <h2 id="worker-modal-title" className="text-lg font-semibold text-white flex items-center gap-2">
              <span>👤 {worker.name}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-pulse/15 text-pulse border border-pulse/25 font-normal">
                {worker.role || "ASHA"}
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Health Center: <span className="text-slate-200">{worker.center}</span> • Phone:{" "}
              <span className="text-slate-200">{worker.phone}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close modal"
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/5 transition-colors cursor-pointer text-sm"
          >
            ✕
          </button>
        </div>

        {/* 30-Day Attendance Heatmap */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              📊 30-Day Attendance Heatmap
            </h3>
            {history && (
              <span className="text-xs text-pulse font-semibold">
                Rate: {history.attendance_pct}% ({history.present_days}/{history.total_days} Days)
              </span>
            )}
          </div>

          {loading ? (
            <div className="py-8 text-center text-xs text-slate-400 animate-pulse">
              Loading 30-day timeline...
            </div>
          ) : history?.days ? (
            <div>
              {/* Heatmap Grid */}
              <div className="grid grid-cols-6 sm:grid-cols-10 gap-1.5 p-3 rounded-xl bg-slate-950/60 border border-white/5">
                {history.days.map((d) => (
                  <div
                    key={d.date}
                    title={`${d.date}: ${d.status.toUpperCase()}${d.note ? ` - ${d.note}` : ""}`}
                    className={`h-9 rounded-lg border text-[10px] flex flex-col items-center justify-center font-mono cursor-help transition-transform hover:scale-110 shadow-sm ${tileColor(
                      d.status
                    )}`}
                  >
                    <span className="font-semibold leading-none">{d.date.slice(8)}</span>
                    <span className="text-[8px] opacity-75 capitalize leading-none mt-0.5">
                      {d.status === "half-day" ? "half" : d.status.slice(0, 4)}
                    </span>
                  </div>
                ))}
              </div>

              {/* Legend */}
              <div className="flex flex-wrap items-center gap-3 mt-3 text-[11px] text-slate-400">
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded bg-emerald-500 inline-block" /> Present
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded bg-amber-500 inline-block" /> Half-day
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded bg-rose-500 inline-block" /> Absent
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded bg-purple-500 inline-block" /> Leave ({history.leave_days})
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded bg-slate-700 inline-block" /> Unmarked
                </span>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-400 py-4 text-center">No timeline records found.</div>
          )}
        </div>

        {/* Leave Management Form */}
        <div className="border-t border-white/10 pt-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 mb-3">
            📋 Apply Official Leave Date Range
          </h3>

          <form onSubmit={handleApplyLeave} className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Start Date</label>
                <input
                  type="date"
                  required
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full text-xs px-3 py-2 rounded-xl bg-slate-950 border border-white/10 text-white focus:outline-none focus:border-pulse/50"
                />
              </div>

              <div>
                <label className="block text-[11px] text-slate-400 mb-1">End Date</label>
                <input
                  type="date"
                  required
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full text-xs px-3 py-2 rounded-xl bg-slate-950 border border-white/10 text-white focus:outline-none focus:border-pulse/50"
                />
              </div>

              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Leave Type</label>
                <select
                  value={leaveType}
                  onChange={(e) => setLeaveType(e.target.value)}
                  className="w-full text-xs px-3 py-2 rounded-xl bg-slate-950 border border-white/10 text-white focus:outline-none focus:border-pulse/50"
                >
                  <option value="casual">Casual Leave</option>
                  <option value="maternity">Maternity Leave</option>
                  <option value="sick">Sick Leave</option>
                  <option value="training">Field Training</option>
                  <option value="bereavement">Bereavement Leave</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-[11px] text-slate-400 mb-1">Reason / Remarks</label>
              <input
                type="text"
                placeholder="e.g. Official ANM district immunization workshop"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="w-full text-xs px-3 py-2 rounded-xl bg-slate-950 border border-white/10 text-white focus:outline-none focus:border-pulse/50"
              />
            </div>

            {leaveSuccess && (
              <div className="p-2.5 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs">
                {leaveSuccess}
              </div>
            )}

            {leaveError && (
              <div className="p-2.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs">
                {leaveError}
              </div>
            )}

            <button
              type="submit"
              disabled={leaveLoading}
              className="w-full sm:w-auto text-xs px-4 py-2 rounded-xl bg-purple-600/30 text-purple-200 border border-purple-500/40 hover:bg-purple-600/50 transition-colors disabled:opacity-50 cursor-pointer font-medium"
            >
              {leaveLoading ? "Submitting Leave..." : "📋 Record Approved Leave"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
