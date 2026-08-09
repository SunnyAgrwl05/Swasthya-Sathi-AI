import { memo, useMemo, useState } from "react";

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

function WorkerTable({
  workers = [],
  summary = [],
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [centerFilter, setCenterFilter] = useState("All");

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

        return {
          worker,
          pct,
          status,
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

        <div className="text-xs text-cyan-300 font-medium">
          {filteredRows.length} of {workers.length} Registered Workers
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
              <th className="py-3 px-2">30 Days</th>
              <th className="py-3 px-2">Status</th>
            </tr>
          </thead>

          <tbody>
            {filteredRows.map(({ worker, pct, status, center }) => {
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
                    <span className="font-semibold text-cyan-300">
                      {pct}%
                    </span>
                  </td>

                  <td className="py-3 px-2">
                    <span
                      className={`inline-flex items-center rounded-full px-3 py-1 text-[11px] font-semibold ${status.cls}`}
                    >
                      {status.text}
                    </span>
                  </td>
                </tr>
              );
            })}

            {filteredRows.length === 0 && (
              <tr>
                <td
                  colSpan={5}
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
    </div>
  );
}

export default memo(WorkerTable);
