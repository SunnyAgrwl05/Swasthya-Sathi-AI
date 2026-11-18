import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api";

function formatDateStr(dateObj) {
  const y = dateObj.getFullYear();
  const m = String(dateObj.getMonth() + 1).padStart(2, "0");
  const d = String(dateObj.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export default function WorkerDetailModal({ worker, onClose, onLeaveLogged }) {
  const [attendance, setAttendance] = useState([]);
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Leave Form State
  const todayStr = useMemo(() => formatDateStr(new Date()), []);
  const [startDate, setStartDate] = useState(todayStr);
  const [endDate, setEndDate] = useState(todayStr);
  const [leaveType, setLeaveType] = useState("casual");
  const [reason, setReason] = useState("");
  const [approvedBy, setApprovedBy] = useState("Supervisor");
  const [submitting, setSubmitting] = useState(false);
  const [formFeedback, setFormFeedback] = useState(null);

  const fetchWorkerData = useCallback(async () => {
    if (!worker?.id) return;
    setLoading(true);
    setError(null);
    try {
      const [attData, leaveData] = await Promise.all([
        api.getAttendance(worker.id),
        api.getLeaves(worker.id),
      ]);
      setAttendance(attData || []);
      setLeaves(leaveData || []);
    } catch (_err) {
      setError("Failed to load worker attendance data.");
    } finally {
      setLoading(false);
    }
  }, [worker]);

  useEffect(() => {
    fetchWorkerData();
  }, [fetchWorkerData]);

  // Handle ESC key to close modal
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  // Generate the last 30 calendar days
  const thirtyDays = useMemo(() => {
    const list = [];
    const base = new Date();
    for (let i = 29; i >= 0; i--) {
      const d = new Date(base);
      d.setDate(base.getDate() - i);
      list.push(formatDateStr(d));
    }
    return list;
  }, []);

  // Map attendance records by date
  const attendanceByDate = useMemo(() => {
    const map = {};
    for (const rec of attendance) {
      map[rec.date] = rec;
    }
    return map;
  }, [attendance]);

  // Heatmap metrics
  const metrics = useMemo(() => {
    let present = 0;
    let absent = 0;
    let halfDay = 0;
    let leaveCount = 0;

    for (const dateStr of thirtyDays) {
      const rec = attendanceByDate[dateStr];
      if (!rec) continue;
      if (rec.status === "present") present++;
      else if (rec.status === "absent") absent++;
      else if (rec.status === "half-day") halfDay++;
      else if (rec.status === "leave") leaveCount++;
    }

    const recordedDays = present + absent + halfDay + leaveCount;
    const rate = recordedDays > 0 ? Math.round((present / recordedDays) * 100) : 0;

    return { present, absent, halfDay, leaveCount, rate, recordedDays };
  }, [thirtyDays, attendanceByDate]);

  const handleLogLeave = async (e) => {
    e.preventDefault();
    setFormFeedback(null);

    if (startDate > endDate) {
      setFormFeedback({
        type: "error",
        message: "Start date cannot be after end date.",
      });
      return;
    }

    setSubmitting(true);
    try {
      await api.createLeave({
        worker_id: worker.id,
        start_date: startDate,
        end_date: endDate,
        leave_type: leaveType,
        reason: reason.trim(),
        approved_by: approvedBy.trim() || "Supervisor",
      });

      setFormFeedback({
        type: "success",
        message: "Leave logged successfully! Attendance records updated.",
      });
      setReason("");

      // Refresh local worker data & notify parent table/dashboard
      await fetchWorkerData();
      if (onLeaveLogged) {
        onLeaveLogged(worker.id);
      }
    } catch (_err) {
      setFormFeedback({
        type: "error",
        message: "Failed to record leave. Please try again.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (!worker) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-worker-name"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl border border-line bg-panel p-6 shadow-2xl scrollbar-thin text-white"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Close modal"
          className="absolute top-5 right-5 text-white/50 hover:text-white transition p-1.5 rounded-lg hover:bg-white/[0.08]"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Worker Header */}
        <div className="flex flex-wrap items-center gap-3 pb-5 border-b border-line">
          <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-300 font-bold text-lg">
            {worker.name ? worker.name.charAt(0) : "W"}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 id="modal-worker-name" className="text-xl font-bold font-display text-white">
                {worker.name}
              </h2>
              <span className="px-2 py-0.5 rounded-md bg-white/[0.06] text-white/60 text-xs font-mono border border-line">
                {worker.worker_code}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-white/60 mt-1">
              <span className="text-pulse">{worker.role}</span>
              <span>•</span>
              <span>{worker.center}</span>
              <span>•</span>
              <span>📞 {worker.phone}</span>
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-danger/10 border border-danger/30 text-danger text-xs">
            {error}
          </div>
        )}

        {/* 30-Day Attendance Heatmap Section */}
        <div className="mt-6">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <div>
              <h3 className="text-sm font-semibold font-display text-white">
                30-Day Attendance Timeline & Heatmap
              </h3>
              <p className="text-xs text-white/50">
                GitHub-style daily activity and presence record
              </p>
            </div>
            {/* Quick Metrics */}
            <div className="flex items-center gap-3 text-xs">
              <span className="px-2.5 py-1 rounded-lg bg-pulse/10 text-pulse border border-pulse/20 font-semibold">
                {metrics.rate}% Attendance
              </span>
              <span className="text-white/60">
                {metrics.present} Present / {metrics.leaveCount} Leaves
              </span>
            </div>
          </div>

          {/* Heatmap Grid */}
          <div className="p-4 rounded-xl bg-white/[0.02] border border-line">
            {loading ? (
              <div className="h-20 flex items-center justify-center text-xs text-white/40">
                Loading attendance history...
              </div>
            ) : (
              <div>
                <div className="grid grid-cols-10 sm:grid-cols-15 md:grid-cols-30 gap-1.5 justify-items-center">
                  {thirtyDays.map((dateStr) => {
                    const rec = attendanceByDate[dateStr];
                    const status = rec?.status || "unrecorded";
                    let colorCls = "bg-white/[0.04] border-line text-white/30";
                    let label = "No record";

                    if (status === "present") {
                      colorCls = "bg-pulse text-base border-pulse/60 font-semibold shadow-sm";
                      label = "Present";
                    } else if (status === "absent") {
                      colorCls = "bg-danger text-white border-danger/60 font-semibold shadow-sm";
                      label = "Absent";
                    } else if (status === "half-day") {
                      colorCls = "bg-warn text-base border-warn/60 font-semibold shadow-sm";
                      label = "Half-day";
                    } else if (status === "leave") {
                      colorCls = "bg-purple-500 text-white border-purple-400 font-semibold shadow-sm";
                      label = `Leave (${rec?.note || "Approved"})`;
                    }

                    const dayNum = dateStr.slice(8);

                    return (
                      <div
                        key={dateStr}
                        className="group relative flex flex-col items-center"
                      >
                        <div
                          className={`w-7 h-7 rounded-md border flex items-center justify-center text-[10px] transition-transform hover:scale-110 cursor-pointer ${colorCls}`}
                        >
                          {dayNum}
                        </div>
                        {/* Tooltip */}
                        <div className="absolute bottom-full mb-1.5 hidden group-hover:flex flex-col items-center z-20 pointer-events-none whitespace-nowrap">
                          <div className="bg-panel/95 border border-line text-[11px] rounded-lg px-2.5 py-1.5 shadow-xl text-center">
                            <span className="font-semibold text-white">{dateStr}</span>
                            <span className="text-white/60 block">{label}</span>
                            {rec?.note && (
                              <span className="text-white/40 block text-[10px] italic">
                                &quot;{rec.note}&quot;
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Heatmap Legend */}
                <div className="flex flex-wrap items-center justify-center gap-4 mt-4 pt-3 border-t border-line/60 text-xs text-white/60">
                  <div className="flex items-center gap-1.5">
                    <span className="w-3.5 h-3.5 rounded bg-pulse border border-pulse/60" />
                    <span>Present</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3.5 h-3.5 rounded bg-warn border border-warn/60" />
                    <span>Half-day</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3.5 h-3.5 rounded bg-purple-500 border border-purple-400" />
                    <span>Leave</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3.5 h-3.5 rounded bg-danger border border-danger/60" />
                    <span>Absent</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3.5 h-3.5 rounded bg-white/[0.04] border border-line" />
                    <span>Unrecorded</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Log Leave Form Section */}
        <div className="mt-6 pt-5 border-t border-line">
          <div className="mb-3">
            <h3 className="text-sm font-semibold font-display text-white">
              Log Leave for Health Worker
            </h3>
            <p className="text-xs text-white/50">
              Submit an approved leave period. Corresponding daily attendance records will be auto-populated.
            </p>
          </div>

          {formFeedback && (
            <div
              className={`mb-4 p-3 rounded-xl border text-xs ${
                formFeedback.type === "success"
                  ? "bg-pulse/10 border-pulse/30 text-pulse"
                  : "bg-danger/10 border-danger/30 text-danger"
              }`}
            >
              {formFeedback.message}
            </div>
          )}

          <form onSubmit={handleLogLeave} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <label className="block text-xs text-white/60 mb-1 font-medium">
                  Start Date
                </label>
                <input
                  type="date"
                  required
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full rounded-xl bg-white/[0.04] border border-line px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400 transition"
                />
              </div>

              <div>
                <label className="block text-xs text-white/60 mb-1 font-medium">
                  End Date
                </label>
                <input
                  type="date"
                  required
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full rounded-xl bg-white/[0.04] border border-line px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400 transition"
                />
              </div>

              <div>
                <label className="block text-xs text-white/60 mb-1 font-medium">
                  Leave Type
                </label>
                <select
                  value={leaveType}
                  onChange={(e) => setLeaveType(e.target.value)}
                  className="w-full rounded-xl bg-white/[0.04] border border-line px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400 transition"
                >
                  <option value="casual" className="bg-panel text-white">Casual Leave</option>
                  <option value="medical" className="bg-panel text-white">Medical Leave</option>
                  <option value="maternity" className="bg-panel text-white">Maternity Leave</option>
                  <option value="annual" className="bg-panel text-white">Earned / Annual Leave</option>
                  <option value="other" className="bg-panel text-white">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs text-white/60 mb-1 font-medium">
                  Approved By
                </label>
                <input
                  type="text"
                  value={approvedBy}
                  onChange={(e) => setApprovedBy(e.target.value)}
                  placeholder="Supervisor Name"
                  className="w-full rounded-xl bg-white/[0.04] border border-line px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400 transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs text-white/60 mb-1 font-medium">
                Reason / Remarks
              </label>
              <input
                type="text"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="e.g. Viral fever recovery, family emergency, official training"
                className="w-full rounded-xl bg-white/[0.04] border border-line px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400 transition"
              />
            </div>

            <div className="flex justify-end gap-2 pt-1">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-white/60 hover:text-white border border-line hover:bg-white/[0.04] transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-5 py-2 rounded-xl text-xs font-semibold bg-pulse text-base hover:bg-pulse/90 transition shadow-glow disabled:opacity-50"
              >
                {submitting ? "Logging leave..." : "Log Leave"}
              </button>
            </div>
          </form>
        </div>

        {/* Recent Leave History */}
        {leaves.length > 0 && (
          <div className="mt-6 pt-5 border-t border-line">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-white/50 mb-3">
              Approved Leave History
            </h4>
            <div className="space-y-2 max-h-36 overflow-y-auto scrollbar-thin">
              {leaves.map((l) => (
                <div
                  key={l.id}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-white/[0.02] border border-line text-xs"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-purple-400" />
                    <span className="font-semibold text-white capitalize">{l.leave_type} Leave</span>
                    <span className="text-white/40">({l.start_date} to {l.end_date})</span>
                  </div>
                  <div className="text-white/60 text-[11px]">
                    {l.reason ? `"${l.reason}"` : "Approved"} • by {l.approved_by}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
