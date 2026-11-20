import { memo, useMemo, useState } from "react";
import WorkerDetailModal from "./WorkerDetailModal";
import { api } from "../api";

function badge(pct) {
  if (pct >= 85) {
    return {
      text: "Strong",
      cls: "bg-pulse/15 text-pulse border border-pulse/30",
    };
  }

  if (pct >= 75) {
    return {
      text: "Steady",
      cls: "bg-pulse2/15 text-pulse2 border border-pulse2/30",
    };
  }

  if (pct >= 60) {
    return {
      text: "Watch",
      cls: "bg-warn/15 text-warn border border-warn/30",
    };
  }

  return {
    text: "Follow Up",
    cls: "bg-danger/15 text-danger border border-danger/30",
  };
}

function trendIndicator(delta, lastWeek, thisWeek) {
  if (delta === null || delta === undefined) {
    return null;
  }

  if (delta > 0) {
    return {
      arrow: "↑",
      text: `+${delta}%`,
      cls: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
      ariaLabel: `Increased by ${delta}% week-over-week`,
      tooltip: `Week-over-week: ${lastWeek ?? 0}% → ${thisWeek ?? 0}% (+${delta}%)`,
    };
  }

  if (delta < 0) {
    return {
      arrow: "↓",
      text: `${delta}%`,
      cls: "text-rose-400 bg-rose-500/10 border-rose-500/30",
      ariaLabel: `Decreased by ${Math.abs(delta)}% week-over-week`,
      tooltip: `Week-over-week: ${lastWeek ?? 0}% → ${thisWeek ?? 0}% (${delta}%)`,
    };
  }

  return {
    arrow: "→",
    text: "0%",
    cls: "text-white/50 bg-white/5 border-white/10",
    ariaLabel: "Unchanged week-over-week",
    tooltip: `Week-over-week: unchanged (${thisWeek ?? 0}%)`,
  };
}

function WorkerTable({
  workers = [],
  summary = [],
  onRefresh,
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [centerFilter, setCenterFilter] = useState("All");
  const [selectedWorker, setSelectedWorker] = useState(null);
  const [showImportModal, setShowImportModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [exportMonth] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  });

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    setUploadResult(null);
    try {
      const res = await api.importWorkersCsv(file);
      setUploadResult(res);
      if (res.created > 0 && onRefresh) {
        onRefresh();
      }
    } catch (err) {
      setUploadError(err.message || "Failed to upload CSV");
    } finally {
      setUploading(false);
    }
  };

  const byId = useMemo(
    () =>
      Object.fromEntries(
        (summary || []).map((item) => [item.worker_id, item])
      ),
    [summary]
  );

  const rows = useMemo(
    () =>
      workers.map((worker) => {
        const stats = byId[worker.id];
        const pct = stats?.attendance_pct ?? 0;
        const status = badge(pct);
        const trend = trendIndicator(
          stats?.trend_delta,
          stats?.last_week_pct,
          stats?.this_week_pct
        );

        return {
          worker,
          pct,
          status,
          trend,
          center: worker.center || "—",
        };
      }),
    [workers, byId]
  );

  const centers = useMemo(
    () =>
      Array.from(
        new Set(rows.map((row) => row.center))
      ).sort(),
    [rows]
  );

  const statuses = useMemo(
    () =>
      Array.from(
        new Set(rows.map((row) => row.status.text))
      ).sort(),
    [rows]
  );

  const filteredRows = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();

    return rows.filter(({ worker, center, status }) => {
      const matchesSearch =
        normalizedSearch === "" ||
        worker.name.toLowerCase().includes(normalizedSearch) ||
        center.toLowerCase().includes(normalizedSearch);
      const matchesStatus =
        statusFilter === "All" || status.text === statusFilter;
      const matchesCenter =
        centerFilter === "All" || center === centerFilter;

      return matchesSearch && matchesStatus && matchesCenter;
    });
  }, [rows, searchTerm, statusFilter, centerFilter]);

  const hasActiveFilters =
    searchTerm.trim() !== "" ||
    statusFilter !== "All" ||
    centerFilter !== "All";

  const clearFilters = () => {
    setSearchTerm("");
    setStatusFilter("All");
    setCenterFilter("All");
  };

  return (
    <div className="glass p-4 sm:p-5 fade-up mb-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-5">
        <div>
          <h2 className="font-display font-semibold text-base text-white">
            👩‍⚕️ Health Worker Roster
          </h2>

          <p className="text-xs text-white/50 mt-1">
            AI-monitored workforce attendance overview
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="text-xs text-cyan-300 font-medium mr-1">
            {filteredRows.length} of {workers.length} Registered Workers
          </div>

          <button
            type="button"
            onClick={() => {
              setShowImportModal(true);
              setUploadResult(null);
              setUploadError(null);
            }}
            className="inline-flex items-center gap-1.5 rounded-xl border border-line bg-white/[0.04] px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-white/[0.08] hover:border-white/30"
          >
            📥 Import CSV
          </button>

          <a
            href={api.exportAttendanceCsvUrl(exportMonth, centerFilter)}
            download
            className="inline-flex items-center gap-1.5 rounded-xl border border-cyan-400/30 bg-cyan-500/10 px-3 py-1.5 text-xs font-semibold text-cyan-200 transition hover:bg-cyan-500/20"
            title="Download Monthly Attendance Matrix (Excel-friendly CSV)"
          >
            📊 Export Sheet
          </a>
        </div>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_auto_auto] gap-3 mb-4">
        <label className="sr-only" htmlFor="worker-search">
          Search health workers
        </label>
        <input
          id="worker-search"
          type="search"
          value={searchTerm}
          onChange={(event) => setSearchTerm(event.target.value)}
          placeholder="Search by name or center..."
          className="w-full rounded-xl border border-line bg-white/[0.04] px-4 py-2.5 text-sm text-white placeholder:text-white/35 outline-none transition focus:border-cyan-300/70 focus:bg-white/[0.07]"
        />

        <label className="sr-only" htmlFor="status-filter">
          Filter by status
        </label>
        <select
          id="status-filter"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
          className="rounded-xl border border-line bg-slate-950/80 px-3 py-2.5 text-sm text-white outline-none transition focus:border-cyan-300/70"
        >
          <option value="All">All Statuses</option>
          {statuses.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>

        <label className="sr-only" htmlFor="center-filter">
          Filter by center
        </label>
        <select
          id="center-filter"
          value={centerFilter}
          onChange={(event) => setCenterFilter(event.target.value)}
          className="rounded-xl border border-line bg-slate-950/80 px-3 py-2.5 text-sm text-white outline-none transition focus:border-cyan-300/70"
        >
          <option value="All">All Centers</option>
          {centers.map((center) => (
            <option key={center} value={center}>
              {center}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <button
          type="button"
          onClick={() => setStatusFilter("All")}
          className={`rounded-full px-3 py-1 text-[11px] font-semibold border transition ${
            statusFilter === "All"
              ? "bg-cyan-300/15 text-cyan-200 border-cyan-300/40"
              : "bg-white/[0.03] text-white/60 border-line hover:text-white"
          }`}
        >
          All
        </button>
        {statuses.map((status) => (
          <button
            key={status}
            type="button"
            onClick={() => setStatusFilter(status)}
            className={`rounded-full px-3 py-1 text-[11px] font-semibold border transition ${
              statusFilter === status
                ? "bg-cyan-300/15 text-cyan-200 border-cyan-300/40"
                : "bg-white/[0.03] text-white/60 border-line hover:text-white"
            }`}
          >
            {status}
          </button>
        ))}

        {hasActiveFilters && (
          <button
            type="button"
            onClick={clearFilters}
            className="ml-auto text-xs font-medium text-white/50 transition hover:text-white"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto scrollbar-thin rounded-xl">
        <table className="min-w-[720px] w-full">
          <thead>
            <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-white/45">
              <th className="py-3 px-2">Name</th>
              <th className="py-3 px-2">Role</th>
              <th className="py-3 px-2">Center</th>
              <th className="py-3 px-2">30 Days (WoW)</th>
              <th className="py-3 px-2">Status</th>
              <th className="py-3 px-2">Timeline</th>
            </tr>
          </thead>

          <tbody>
            {filteredRows.map(({ worker, pct, status, trend, center }) => {
              return (
                <tr
                  key={worker.id}
                  className="border-b border-line/50 hover:bg-white/[0.03] transition-colors last:border-0"
                >
                  <td className="py-3 px-2 font-medium whitespace-nowrap">
                    {worker.name}
                  </td>

                  <td className="py-3 px-2 text-white/70 whitespace-nowrap">
                    {worker.role}
                  </td>

                  <td className="py-3 px-2 text-white/70 whitespace-nowrap">
                    {center}
                  </td>

                  <td className="py-3 px-2">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-cyan-300">
                        {pct}%
                      </span>
                      {trend && (
                        <span
                          title={trend.tooltip}
                          aria-label={trend.ariaLabel}
                          className={`inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-[11px] font-medium border cursor-help ${trend.cls}`}
                        >
                          <span className="font-bold">{trend.arrow}</span>
                          <span>{trend.text}</span>
                        </span>
                      )}
                    </div>
                  </td>

                  <td className="py-3 px-2">
                    <span
                      className={`inline-flex items-center rounded-full px-3 py-1 text-[11px] font-semibold ${status.cls}`}
                    >
                      {status.text}
                    </span>
                  </td>

                  <td className="py-3 px-2 whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => setSelectedWorker(worker)}
                      className="text-[11px] px-2.5 py-1 rounded-lg bg-white/5 border border-line hover:border-pulse/40 hover:text-pulse transition-colors cursor-pointer"
                    >
                      📊 Heatmap & Leave
                    </button>
                  </td>
                </tr>
              );
            })}

            {filteredRows.length === 0 && (
              <tr>
                <td
                  colSpan={6}
                  className="py-10 text-center text-white/40"
                >
                  {workers.length === 0
                    ? "No health workers available."
                    : "No workers match the selected filters."}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {selectedWorker && (
        <WorkerDetailModal
          worker={selectedWorker}
          onClose={() => setSelectedWorker(null)}
          onLeaveApplied={onRefresh}
        />
      )}

      {/* Bulk Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="glass w-full max-w-md p-6 rounded-2xl border border-white/10 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display font-semibold text-base text-white">
                📥 Bulk Import Health Workers
              </h3>
              <button
                type="button"
                onClick={() => setShowImportModal(false)}
                className="text-white/40 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-white/60">
              Upload a CSV file containing worker records (<code className="text-cyan-300">worker_code, name, role, center, phone</code>).
            </p>

            <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] border border-line text-xs">
              <span className="text-white/70">Need a template?</span>
              <a
                href={api.sampleWorkersCsvUrl}
                download
                className="text-cyan-300 hover:text-cyan-200 font-medium underline flex items-center gap-1"
              >
                📄 Download Sample CSV
              </a>
            </div>

            <label className="flex flex-col items-center justify-center p-6 border-2 border-dashed border-line hover:border-cyan-400/50 rounded-xl cursor-pointer bg-white/[0.02] hover:bg-white/[0.05] transition">
              <span className="text-2xl mb-1">📁</span>
              <span className="text-xs text-white/80 font-medium">
                {uploading ? "Importing workers..." : "Click or drag CSV file here"}
              </span>
              <span className="text-[10px] text-white/40 mt-1">Accepts standard .csv files</span>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileUpload}
                disabled={uploading}
                className="hidden"
              />
            </label>

            {uploadResult && (
              <div className="rounded-xl border border-pulse/30 bg-pulse/10 p-3 text-xs text-pulse space-y-1">
                <div className="font-semibold">Import Succeeded:</div>
                <div>✅ {uploadResult.created} workers created</div>
                {uploadResult.skipped > 0 && <div>⚠️ {uploadResult.skipped} duplicate workers skipped</div>}
                {uploadResult.errors?.length > 0 && (
                  <div className="text-warn text-[11px] mt-1">
                    Issues encountered:
                    <ul className="list-disc pl-4 mt-0.5">
                      {uploadResult.errors.map((err, i) => (
                        <li key={i}>{err}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {uploadError && (
              <div className="rounded-xl border border-danger/30 bg-danger/10 p-3 text-xs text-danger">
                ❌ {uploadError}
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => setShowImportModal(false)}
                className="rounded-xl bg-white/[0.08] hover:bg-white/[0.15] text-white px-4 py-2 text-xs font-semibold transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default memo(WorkerTable);
