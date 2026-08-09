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
});
