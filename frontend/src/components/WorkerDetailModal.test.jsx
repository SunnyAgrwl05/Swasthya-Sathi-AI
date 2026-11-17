import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import WorkerDetailModal from "./WorkerDetailModal";
import WorkerTable from "./WorkerTable";
import { api } from "../api";

vi.mock("../api", () => ({
  api: {
    getAttendance: vi.fn(),
    getLeaves: vi.fn(),
    createLeave: vi.fn(),
  },
}));

const mockWorker = {
  id: 1,
  name: "Anita Devi",
  worker_code: "ASHA-PAT-001",
  role: "ASHA Worker",
  center: "Patna Central",
  phone: "9876543210",
};

const mockSummary = [
  { worker_id: 1, attendance_pct: 88 },
];

describe("WorkerDetailModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getAttendance.mockResolvedValue([
      { id: 101, worker_id: 1, date: "2026-11-10", status: "present", note: null },
      { id: 102, worker_id: 1, date: "2026-11-11", status: "absent", note: "Fever" },
      { id: 103, worker_id: 1, date: "2026-11-12", status: "half-day", note: null },
      { id: 104, worker_id: 1, date: "2026-11-13", status: "leave", note: "Casual leave" },
    ]);
    api.getLeaves.mockResolvedValue([
      {
        id: 1,
        worker_id: 1,
        start_date: "2026-11-13",
        end_date: "2026-11-13",
        leave_type: "casual",
        reason: "Personal work",
        approved_by: "Supervisor",
      },
    ]);
  });

  it("renders worker details and header correctly", async () => {
    const handleClose = vi.fn();
    render(<WorkerDetailModal worker={mockWorker} onClose={handleClose} />);

    expect(screen.getByText("Anita Devi")).toBeInTheDocument();
    expect(screen.getByText("ASHA-PAT-001")).toBeInTheDocument();
    expect(screen.getByText("ASHA Worker")).toBeInTheDocument();
    expect(screen.getByText("Patna Central")).toBeInTheDocument();
    expect(screen.getByText(/9876543210/)).toBeInTheDocument();

    await waitFor(() => {
      expect(api.getAttendance).toHaveBeenCalledWith(1);
      expect(api.getLeaves).toHaveBeenCalledWith(1);
    });
  });

  it("displays 30-day heatmap section and legend", async () => {
    render(<WorkerDetailModal worker={mockWorker} onClose={vi.fn()} />);

    expect(
      screen.getByText("30-Day Attendance Timeline & Heatmap")
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getAllByText("Present").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Absent").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Half-day").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Leave").length).toBeGreaterThan(0);
      expect(screen.getByText("Unrecorded")).toBeInTheDocument();
    });
  });

  it("closes modal on close button click and on Escape key", async () => {
    const handleClose = vi.fn();
    render(<WorkerDetailModal worker={mockWorker} onClose={handleClose} />);

    const closeBtn = screen.getByRole("button", { name: /close modal/i });
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(window, { key: "Escape" });
    expect(handleClose).toHaveBeenCalledTimes(2);
  });

  it("validates that start date cannot be after end date", async () => {
    render(<WorkerDetailModal worker={mockWorker} onClose={vi.fn()} />);

    const inputs = screen.getAllByDisplayValue(/2026-/);
    const startDateInput = inputs[0];
    const endDateInput = inputs[1];

    fireEvent.change(startDateInput, { target: { value: "2026-11-20" } });
    fireEvent.change(endDateInput, { target: { value: "2026-11-15" } });

    const submitBtn = screen.getByRole("button", { name: /log leave/i });
    fireEvent.click(submitBtn);

    expect(
      screen.getByText("Start date cannot be after end date.")
    ).toBeInTheDocument();
    expect(api.createLeave).not.toHaveBeenCalled();
  });

  it("submits leave successfully and refreshes attendance records", async () => {
    api.createLeave.mockResolvedValue({
      id: 5,
      worker_id: 1,
      start_date: "2026-11-15",
      end_date: "2026-11-19",
      leave_type: "medical",
      reason: "Dengue treatment",
      approved_by: "Dr. Sharma",
    });

    const handleLeaveLogged = vi.fn();
    render(
      <WorkerDetailModal
        worker={mockWorker}
        onClose={vi.fn()}
        onLeaveLogged={handleLeaveLogged}
      />
    );

    const inputs = screen.getAllByDisplayValue(/2026-/);
    fireEvent.change(inputs[0], { target: { value: "2026-11-15" } });
    fireEvent.change(inputs[1], { target: { value: "2026-11-19" } });

    const leaveTypeSelect = screen.getByRole("combobox");
    fireEvent.change(leaveTypeSelect, { target: { value: "medical" } });

    const reasonInput = screen.getByPlaceholderText(/viral fever/i);
    fireEvent.change(reasonInput, { target: { value: "Dengue treatment" } });

    const submitBtn = screen.getByRole("button", { name: /log leave/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.createLeave).toHaveBeenCalledWith({
        worker_id: 1,
        start_date: "2026-11-15",
        end_date: "2026-11-19",
        leave_type: "medical",
        reason: "Dengue treatment",
        approved_by: "Supervisor",
      });
      expect(
        screen.getByText("Leave logged successfully! Attendance records updated.")
      ).toBeInTheDocument();
      expect(handleLeaveLogged).toHaveBeenCalledWith(1);
    });
  });

  it("opens detail modal when clicking a worker row in WorkerTable", async () => {
    render(
      <WorkerTable workers={[mockWorker]} summary={mockSummary} />
    );

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

    const workerRowName = screen.getByText("Anita Devi");
    fireEvent.click(workerRowName);

    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("30-Day Attendance Timeline & Heatmap")).toBeInTheDocument();
  });
});
