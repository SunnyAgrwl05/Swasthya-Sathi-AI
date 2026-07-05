export default function StatCards({ workers, summary }) {
  const total = workers.length;

  const avg = summary.length
    ? Math.round(
      summary.reduce((s, w) => s + w.attendance_pct, 0) / summary.length
    )
    : 0;

  const flagged = summary.filter(
    (w) => w.attendance_pct < 75
  ).length;

  const centers = new Set(
    workers.map((w) => w.center)
  ).size;

  const cards = [
    {
      label: "Registered Workers",
      value: total,
      accent: "text-pulse",
    },
    {
      label: "Avg. Attendance (30 Days)",
      value: `${avg}%`,
      accent: avg >= 80 ? "text-pulse" : "text-warn",
    },
    {
      label: "Needs Follow-up",
      value: flagged,
      accent: flagged ? "text-danger" : "text-pulse",
    },
    {
      label: "Centers Covered",
      value: centers,
      accent: "text-pulse2",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6">
      {cards.map((card) => (
        <div
          key={card.label}
          className="glass p-3 sm:p-4 rounded-2xl transition-all duration-300 hover:scale-[1.02] hover:border-pulse/40 fade-up"
        >
          <p
            className={`font-display text-xl sm:text-2xl font-bold ${card.accent}`}
          >
            {card.value}
          </p>

          <p className="mt-1 text-[11px] sm:text-xs text-white/55 leading-snug">
            {card.label}
          </p>
        </div>
      ))}
    </div>
  );
}