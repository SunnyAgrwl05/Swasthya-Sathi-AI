import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import StatCards from "./StatCards";

describe("StatCards Component", () => {
  const mockWorkers = [
    { id: 1, name: "Anita Devi", center: "Patna Central" },
    { id: 2, name: "Sunita Kumari", center: "Patna Central" },
    { id: 3, name: "Rina Devi", center: "Danapur Sub-Center" },
    { id: 4, name: "Pooja Singh", center: "Phulwari Sharif" },
  ];

  const mockSummary = [
    { worker_id: 1, attendance_pct: 90 },
    { worker_id: 2, attendance_pct: 80 },
    { worker_id: 3, attendance_pct: 70 }, // < 75 -> flagged
    { worker_id: 4, attendance_pct: 60 }, // < 75 -> flagged
  ];

  it("renders all four stat metric cards accurately", () => {
    render(<StatCards workers={mockWorkers} summary={mockSummary} />);

    // Total registered workers = 4
    expect(screen.getByText("Registered Workers")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();

    // Average attendance = (90 + 80 + 70 + 60) / 4 = 75%
    expect(screen.getByText("Avg. Attendance (30 Days)")).toBeInTheDocument();
    expect(screen.getByText("75%")).toBeInTheDocument();

    // Flagged workers (< 75%) = 2 (70% and 60%)
    expect(screen.getByText("Needs Follow-up")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();

    // Unique centers covered: Patna Central, Danapur Sub-Center, Phulwari Sharif = 3
    expect(screen.getByText("Centers Covered")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("handles empty workers and summary data without error", () => {
    render(<StatCards workers={[]} summary={[]} />);

    expect(screen.getByText("Registered Workers")).toBeInTheDocument();
    expect(screen.getByText("0%")).toBeInTheDocument(); // avg is 0%
    expect(screen.getByText("Centers Covered")).toBeInTheDocument();
  });

  it("applies pulse accent styling when attendance is high (>= 80%)", () => {
    const highSummary = [
      { worker_id: 1, attendance_pct: 85 },
      { worker_id: 2, attendance_pct: 95 },
    ];
    render(<StatCards workers={mockWorkers.slice(0, 2)} summary={highSummary} />);

    const avgEl = screen.getByText("90%");
    expect(avgEl).toHaveClass("text-pulse");
  });
});
