import { useState, useEffect, useCallback, useMemo } from "react";
import { api } from "../api";

function parseLocalDate(dateStr) {
  if (!dateStr) return null;
  const [y, m, d] = dateStr.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function getTodayDate() {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export default function WorkerDetailModal({ worker, onClose, onLeaveApplied }) {
  const [history, setHistory] = useState(null);
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [leavesLoading, setLeavesLoading] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState(null);
  const [leaveLoading, setLeaveLoading] = useState(false);
  const [leaveSuccess, setLeaveSuccess] = useState(null);
  const [leaveError, setLeaveError] = useState(null);
  const [viewMode, setViewMode] = useState("graph"); // "graph" or "tiles"
  const [hoveredDay, setHoveredDay] = useState(null);

  const [startDate, setStartDate] = useState(getTodayDate);
  const [endDate, setEndDate] = useState(getTodayDate);
  const [leaveType, setLeaveType] = useState("casual");
  const [reason, setReason] = useState("");

  const workerId = worker?.id;

  const loadHistory = useCallback(async () => {
    if (!workerId) return;
    setLoading(true);
    try {
      const data = await api.getWorkerAttendanceHistory(workerId, 30);
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
  }, [workerId]);

  const loadLeaves = useCallback(async () => {
    if (!workerId) return;
    setLeavesLoading(true);
    try {
      const list = await api.getLeaves(workerId);
      setLeaves(list || []);
    } catch {
      // ignore
    } finally {
      setLeavesLoading(false);
    }
  }, [workerId]);

  useEffect(() => {
    loadHistory();
    loadLeaves();
  }, [loadHistory, loadLeaves]);

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
      setLeaveSuccess(`✓ Submitted ${res.leave_type} leave (${res.start_date} to ${res.end_date})`);
      setReason("");
      await Promise.all([loadHistory(), loadLeaves()]);
      if (onLeaveApplied) onLeaveApplied();
    } catch (err) {
      setLeaveError(err.message || "Failed to submit leave request.");
    } finally {
      setLeaveLoading(false);
    }
  }

  async function handleUpdateLeaveStatus(leaveId, newStatus) {
    setActionLoadingId(leaveId);
    setLeaveError(null);
    try {
      await api.updateLeaveStatus(leaveId, newStatus);
      await Promise.all([loadHistory(), loadLeaves()]);
      if (onLeaveApplied) onLeaveApplied();
    } catch (err) {
      setLeaveError(err.message || `Failed to set status to ${newStatus}`);
    } finally {
      setActionLoadingId(null);
    }
  }

  // GitHub commit graph matrix layout (7 rows for days of week, columns for weeks)
  const historyDays = history?.days;
  const commitGraphData = useMemo(() => {
    if (!historyDays || historyDays.length === 0) return { weeks: [], daysCount: 0 };

    const days = [...historyDays];
    // Group days into week chunks
    const weeks = [];
    let currentWeek = [];

    days.forEach((dayObj) => {
      const d = parseLocalDate(dayObj.date);
      const dayOfWeek = (d.getDay() + 6) % 7; // 0 = Mon, 6 = Sun
      currentWeek.push({ ...dayObj, dayOfWeek });
      if (dayOfWeek === 6 || currentWeek.length === 7) {
        weeks.push(currentWeek);
        currentWeek = [];
      }
    });
    if (currentWeek.length > 0) {
      weeks.push(currentWeek);
    }

    return { weeks, daysCount: days.length };
  }, [historyDays]);

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

  function getSvgColor(status) {
    switch (status) {
      case "present":
        return "#10b981"; // emerald-500
      case "absent":
        return "#ef4444"; // rose-500
      case "half-day":
        return "#f59e0b"; // amber-500
      case "leave":
        return "#a855f7"; // purple-500
      default:
        return "#334155"; // slate-700
    }
  }

  const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="worker-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/70 backdrop-blur-sm animate-fade-in"
    >
      <div className="relative w-full max-w-3xl max-h-[92vh] overflow-y-auto bg-slate-900 border border-white/10 rounded-2xl p-5 sm:p-6 shadow-2xl text-slate-200">
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

        {/* 30-Day Attendance Heatmap Header */}
        <div className="mb-6">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                📊 30-Day Attendance Calendar Heatmap
              </h3>
              {history && (
                <span className="text-xs text-pulse font-semibold">
                  Overall Rate: {history.attendance_pct}% ({history.present_days} Present / {history.absent_days} Absent / {history.leave_days} Leave)
                </span>
              )}
            </div>

            {/* Toggle Graph vs Tile View */}
            <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-white/10 text-[11px]">
              <button
                type="button"
                onClick={() => setViewMode("graph")}
                className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                  viewMode === "graph" ? "bg-pulse/20 text-pulse font-medium" : "text-slate-400 hover:text-white"
                }`}
              >
                GitHub Graph
              </button>
              <button
                type="button"
                onClick={() => setViewMode("tiles")}
                className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                  viewMode === "tiles" ? "bg-pulse/20 text-pulse font-medium" : "text-slate-400 hover:text-white"
                }`}
              >
                Day Matrix
              </button>
            </div>
          </div>

          {loading ? (
            <div className="py-10 text-center text-xs text-slate-400 animate-pulse">
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
              {/* GitHub Commit Graph SVG Representation */}
              {viewMode === "graph" ? (
                <div className="p-4 rounded-xl bg-slate-950/80 border border-white/5 overflow-x-auto">
                  <svg
                    viewBox={`0 0 ${Math.max(380, commitGraphData.weeks.length * 48 + 50)} 150`}
                    className="w-full h-auto min-w-[360px]"
                    aria-label="Attendance intensity graph"
                  >
                    {/* Y-axis Day labels */}
                    {DAY_LABELS.map((dayLabel, rowIndex) => (
                      <text
                        key={dayLabel}
                        x="24"
                        y={rowIndex * 17 + 24}
                        fill="#94a3b8"
                        fontSize="9"
                        textAnchor="end"
                        className="font-mono select-none"
                      >
                        {rowIndex % 2 === 0 ? dayLabel : ""}
                      </text>
                    ))}

                    {/* Columns of weeks */}
                    {commitGraphData.weeks.map((week, colIndex) => {
                      const firstDay = parseLocalDate(week[0]?.date);
                      const monthLabel = firstDay ? firstDay.toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "";

                      return (
                        <g key={colIndex} transform={`translate(${colIndex * 50 + 35}, 0)`}>
                          {/* Column Date Header */}
                          <text
                            x="6"
                            y="10"
                            fill="#64748b"
                            fontSize="8"
                            className="font-mono select-none"
                          >
                            {colIndex % 2 === 0 ? monthLabel : ""}
                          </text>

                          {/* Days in week */}
                          {week.map((day) => {
                            const yPos = day.dayOfWeek * 17 + 16;
                            const isHovered = hoveredDay?.date === day.date;

                            return (
                              <rect
                                key={day.date}
                                x="0"
                                y={yPos}
                                width="13"
                                height="13"
                                rx="3"
                                fill={getSvgColor(day.status)}
                                stroke={isHovered ? "#ffffff" : "rgba(255,255,255,0.1)"}
                                strokeWidth={isHovered ? "1.5" : "0.5"}
                                className="cursor-pointer transition-all duration-150"
                                onMouseEnter={() => setHoveredDay(day)}
                                onMouseLeave={() => setHoveredDay(null)}
                              >
                                <title>{`${day.date} (${DAY_LABELS[day.dayOfWeek]}): ${day.status.toUpperCase()}${day.note ? ` - ${day.note}` : ""}`}</title>
                              </rect>
                            );
                          })}
                        </g>
                      );
                    })}
                  </svg>

                  {/* Active Hover Inspection Card */}
                  <div className="mt-2 text-xs py-1.5 px-3 rounded-lg bg-slate-900 border border-white/10 flex items-center justify-between text-slate-300">
                    {hoveredDay ? (
                      <>
                        <span className="font-mono font-medium text-white">
                          📅 {hoveredDay.date} ({DAY_LABELS[hoveredDay.dayOfWeek]})
                        </span>
                        <span className="flex items-center gap-1.5 capitalize">
                          Status:{" "}
                          <span
                            className="inline-block w-2.5 h-2.5 rounded-full"
                            style={{ backgroundColor: getSvgColor(hoveredDay.status) }}
                          />
                          <strong className="text-white">{hoveredDay.status}</strong>
                          {hoveredDay.note && <span className="text-slate-400 font-normal">({hoveredDay.note})</span>}
                        </span>
                      </>
                    ) : (
                      <span className="text-slate-500 italic text-[11px]">
                        Hover over any cell in the graph to view attendance details.
                      </span>
                    )}
                  </div>
                </div>
              ) : (
                /* 30-Day Tile Matrix */
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
              )}

              {/* Heatmap Legend */}
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

        {/* Leave Requests Management & Live Approval Section */}
        <div className="border-t border-white/10 pt-4 mb-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              📋 Leave Records & Status Approvals
            </h3>
            {leavesLoading && <span className="text-xs text-slate-400 animate-pulse">Updating leaves...</span>}
          </div>

          {leaves && leaves.length > 0 ? (
            <div className="space-y-2 mb-4 max-h-44 overflow-y-auto pr-1">
              {leaves.map((lv) => (
                <div
                  key={lv.id}
                  className="p-3 rounded-xl bg-slate-950/80 border border-white/5 flex flex-wrap items-center justify-between gap-3 text-xs"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-white capitalize">{lv.leave_type} Leave</span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                          lv.status === "Approved"
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            : lv.status === "Rejected"
                            ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                            : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                        }`}
                      >
                        {lv.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      {lv.start_date} → {lv.end_date} {lv.reason ? `• "${lv.reason}"` : ""}
                    </p>
                  </div>

                  {/* Quick Action Approval/Rejection buttons */}
                  <div className="flex items-center gap-1.5">
                    {lv.status !== "Approved" && (
                      <button
                        type="button"
                        disabled={actionLoadingId === lv.id}
                        onClick={() => handleUpdateLeaveStatus(lv.id, "Approved")}
                        className="px-2.5 py-1 text-[11px] rounded-lg bg-emerald-600/30 text-emerald-200 border border-emerald-500/40 hover:bg-emerald-600/50 transition-colors disabled:opacity-50 cursor-pointer"
                      >
                        {actionLoadingId === lv.id ? "..." : "✓ Approve"}
                      </button>
                    )}
                    {lv.status !== "Rejected" && (
                      <button
                        type="button"
                        disabled={actionLoadingId === lv.id}
                        onClick={() => handleUpdateLeaveStatus(lv.id, "Rejected")}
                        className="px-2.5 py-1 text-[11px] rounded-lg bg-rose-600/30 text-rose-200 border border-rose-500/40 hover:bg-rose-600/50 transition-colors disabled:opacity-50 cursor-pointer"
                      >
                        {actionLoadingId === lv.id ? "..." : "✕ Reject"}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic mb-4">No leave records registered for this worker.</p>
          )}

          {/* Form to Apply New Leave */}
          <form onSubmit={handleApplyLeave} className="space-y-3 bg-slate-950/40 p-3.5 rounded-xl border border-white/5">
            <h4 className="text-[11px] font-semibold text-slate-300 uppercase tracking-wide">
              ➕ Submit New Leave Request
            </h4>
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
              {leaveLoading ? "Submitting Leave..." : "📋 Record Leave Request"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
