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
  });
});
