import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import AttendanceChart from "./AttendanceChart";

describe("AttendanceChart Component", () => {
  const mockSummary = [
    { worker_id: 1, name: "Anita Devi", attendance_pct: 95 },
    { worker_id: 2, name: "Sunita Kumari", attendance_pct: 82 },
    { worker_id: 3, name: "Rina Devi", attendance_pct: 68 },
    { worker_id: 4, name: "Pooja Singh", attendance_pct: 54 },
  ];

  it("renders chart header, subtitle, and live data indicator", () => {
    render(<AttendanceChart summary={mockSummary} />);

    expect(screen.getByText("📊 Attendance Analytics")).toBeInTheDocument();
    expect(
      screen.getByText("Last 30 Days Attendance Performance")
    ).toBeInTheDocument();
    expect(screen.getByText("● Live AI Data")).toBeInTheDocument();
  });

  it("renders without error when summary data is empty", () => {
    render(<AttendanceChart summary={[]} />);

    expect(screen.getByText("📊 Attendance Analytics")).toBeInTheDocument();
  });
});
