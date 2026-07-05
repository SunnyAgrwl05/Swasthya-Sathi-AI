import { memo, useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from "recharts";

function colorFor(pct) {
  if (pct >= 85) return "#22E1B2";
  if (pct >= 75) return "#5B8CFF";
  if (pct >= 60) return "#F2A93C";
  return "#FF6B6B";
}

function AttendanceChart({ summary }) {
  const data = useMemo(
    () => [...summary].sort((a, b) => b.attendance_pct - a.attendance_pct),
    [summary]
  );

  return (
    <div className="glass p-4 sm:p-5 mb-6 fade-up overflow-hidden">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
        <div>
          <h2 className="font-display font-semibold text-sm text-white/90">
            📊 Attendance Analytics
          </h2>

          <p className="text-xs text-white/50 mt-1">
            Last 30 Days Attendance Performance
          </p>
        </div>

        <span className="text-[10px] sm:text-xs text-cyan-300 font-medium">
          ● Live AI Data
        </span>
      </div>

      <div className="h-60 sm:h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{
              top: 5,
              right: 10,
              left: -20,
              bottom: 5,
            }}
          >
            <CartesianGrid
              stroke="#1B2433"
              vertical={false}
            />

            <XAxis
              dataKey="name"
              tick={{
                fill: "#8B96A5",
                fontSize: 10,
              }}
              interval={0}
              angle={-20}
              textAnchor="end"
              height={60}
              axisLine={{ stroke: "#1B2433" }}
              tickLine={false}
            />

            <YAxis
              tick={{
                fill: "#8B96A5",
                fontSize: 10,
              }}
              axisLine={false}
              tickLine={false}
              domain={[0, 100]}
            />

            <Tooltip
              contentStyle={{
                background: "#0E1420",
                border: "1px solid #1B2433",
                borderRadius: 12,
                color: "#fff",
                fontSize: 12,
              }}
              cursor={{
                fill: "rgba(255,255,255,0.04)",
              }}
            />

            <Bar
              dataKey="attendance_pct"
              radius={[8, 8, 0, 0]}
            >
              {data.map((item) => (
                <Cell
                  key={item.worker_id}
                  fill={colorFor(item.attendance_pct)}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default memo(AttendanceChart);