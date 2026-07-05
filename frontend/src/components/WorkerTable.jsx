import { memo, useMemo } from "react";

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
  const byId = useMemo(
    () =>
      Object.fromEntries(
        (summary || []).map((item) => [item.worker_id, item])
      ),
    [summary]
  );

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
          {workers.length} Registered Workers
        </div>
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
            {workers.map((worker) => {
              const stats = byId[worker.id];
              const pct = stats?.attendance_pct ?? 0;
              const status = badge(pct);

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
                    {worker.center || "—"}
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

            {workers.length === 0 && (
              <tr>
                <td
                  colSpan={5}
                  className="py-10 text-center text-white/40"
                >
                  No health workers available.
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