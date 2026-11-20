import { fireEvent, render, screen, within } from "@testing-library/react";
import WorkerTable from "./WorkerTable";

const workers = [
  {
    id: 1,
    name: "Asha Devi",
    role: "ASHA",
    center: "PHC Patna",
  },
  {
    id: 2,
    name: "Kajal Kumari",
    role: "ANM",
    center: "PHC Bakhtiyarpur",
  },
  {
    id: 3,
    name: "Ravi Kumar",
    role: "Supervisor",
    center: "PHC Patna",
  },
];

const summary = [
  {
    worker_id: 1,
    attendance_pct: 92,
  },
  {
    worker_id: 2,
    attendance_pct: 55,
  },
  {
    worker_id: 3,
    attendance_pct: 68,
  },
];

describe("WorkerTable", () => {
  it("filters workers by name search", () => {
    render(<WorkerTable workers={workers} summary={summary} />);

    fireEvent.change(screen.getByLabelText("Search health workers"), {
      target: { value: "kajal" },
    });

    expect(screen.getByText("Kajal Kumari")).toBeInTheDocument();
    expect(screen.queryByText("Asha Devi")).not.toBeInTheDocument();
    expect(screen.queryByText("Ravi Kumar")).not.toBeInTheDocument();
  });

  it("filters workers by status", () => {
    render(<WorkerTable workers={workers} summary={summary} />);

    fireEvent.click(screen.getByRole("button", { name: "Follow Up" }));

    expect(screen.getByText("Kajal Kumari")).toBeInTheDocument();
    expect(screen.queryByText("Asha Devi")).not.toBeInTheDocument();
    expect(screen.queryByText("Ravi Kumar")).not.toBeInTheDocument();
  });

  it("filters workers by center", () => {
    render(<WorkerTable workers={workers} summary={summary} />);

    fireEvent.change(screen.getByLabelText("Filter by center"), {
      target: { value: "PHC Bakhtiyarpur" },
    });

    expect(screen.getByText("Kajal Kumari")).toBeInTheDocument();
    expect(screen.queryByText("Asha Devi")).not.toBeInTheDocument();
    expect(screen.queryByText("Ravi Kumar")).not.toBeInTheDocument();
  });

  it("clears active filters", () => {
    render(<WorkerTable workers={workers} summary={summary} />);

    fireEvent.change(screen.getByLabelText("Search health workers"), {
      target: { value: "kajal" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Clear filters" }));

    const table = screen.getByRole("table");
    expect(within(table).getByText("Asha Devi")).toBeInTheDocument();
    expect(within(table).getByText("Kajal Kumari")).toBeInTheDocument();
    expect(within(table).getByText("Ravi Kumar")).toBeInTheDocument();
  });

  it("renders week-over-week trend arrows and tooltips", () => {
    const trendSummary = [
      {
        worker_id: 1,
        attendance_pct: 92,
        trend: "up",
        change_pct: 12.5,
        this_week_pct: 95.0,
        last_week_pct: 82.5,
    const summaryWithTrends = [
      {
        worker_id: 1,
        attendance_pct: 92,
        trend_delta: 5.5,
        this_week_pct: 95.0,
        last_week_pct: 89.5,
      },
      {
        worker_id: 2,
        attendance_pct: 55,
        trend: "down",
        change_pct: -16.7,
        this_week_pct: 50.0,
        last_week_pct: 66.7,
      },
    ];

    render(<WorkerTable workers={workers} summary={trendSummary} />);

    expect(screen.getByLabelText("Trending up by 12.5%")).toBeInTheDocument();
    expect(screen.getByLabelText("Trending down by -16.7%")).toBeInTheDocument();
        trend_delta: -10.0,
        this_week_pct: 50.0,
        last_week_pct: 60.0,
      },
      {
        worker_id: 3,
        attendance_pct: 68,
        trend_delta: 0,
        this_week_pct: 70.0,
        last_week_pct: 70.0,
      },
    ];

    render(<WorkerTable workers={workers} summary={summaryWithTrends} />);

    // Check header
    expect(screen.getByText("30 Days (WoW)")).toBeInTheDocument();

    // Check upward trend for worker 1
    const upBadge = screen.getByLabelText("Increased by 5.5% week-over-week");
    expect(upBadge).toBeInTheDocument();
    expect(upBadge).toHaveAttribute("title", "Week-over-week: 89.5% → 95% (+5.5%)");

    // Check downward trend for worker 2
    const downBadge = screen.getByLabelText("Decreased by 10% week-over-week");
    expect(downBadge).toBeInTheDocument();
    expect(downBadge).toHaveAttribute("title", "Week-over-week: 60% → 50% (-10%)");

    // Check neutral trend for worker 3
    const neutralBadge = screen.getByLabelText("Unchanged week-over-week");
    expect(neutralBadge).toBeInTheDocument();
    expect(neutralBadge).toHaveAttribute("title", "Week-over-week: unchanged (70%)");
  });

  it("renders Import CSV and Export Sheet actions", () => {
    render(<WorkerTable workers={workers} summary={summary} />);

    const importBtn = screen.getByRole("button", { name: /import csv/i });
    const exportBtn = screen.getByRole("link", { name: /export sheet/i });

    expect(importBtn).toBeInTheDocument();
    expect(exportBtn).toBeInTheDocument();
    expect(exportBtn).toHaveAttribute("download");
  });

  it("opens import modal with sample CSV template download link", () => {
    render(<WorkerTable workers={workers} summary={summary} />);

    const importBtn = screen.getByRole("button", { name: /import csv/i });
    fireEvent.click(importBtn);

    expect(screen.getByText("📥 Bulk Import Health Workers")).toBeInTheDocument();
    const downloadSample = screen.getByRole("link", { name: /download sample csv/i });
    expect(downloadSample).toBeInTheDocument();
    expect(downloadSample).toHaveAttribute("href", "/api/workers/sample-csv");
  });
});
