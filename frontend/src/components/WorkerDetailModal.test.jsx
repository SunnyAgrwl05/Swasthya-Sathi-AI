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

describe("WorkerDetailModal Component", () => {
  const mockWorker = {
    id: 1,
    worker_code: "HW-001",
    name: "Anita Devi",
    role: "ASHA Worker",
    center: "Phulwari Sharif PHC",
    phone: "9876543210",
  };

  const mockAttendance = [
    { id: 1, worker_id: 1, date: "2026-11-17", status: "present", note: "On time" },
    { id: 2, worker_id: 1, date: "2026-11-16", status: "half-day", note: "Field visit" },
    { id: 3, worker_id: 1, date: "2026-11-15", status: "leave", note: "Medical leave" },
    { id: 4, worker_id: 1, date: "2026-11-14", status: "absent", note: "Uninformed" },
  ];

  const mockLeaves = [
    {
      id: 1,
      worker_id: 1,
      start_date: "2026-11-10",
      end_date: "2026-11-12",
      leave_type: "casual",
      reason: "Family wedding",
      approved_by: "Supervisor Kumar",
    },
  ];

  const mockSummary = [
    { worker_id: 1, present: 22, absent: 3, half_day: 2, leave: 1, total_days: 28 },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    api.getAttendance.mockResolvedValue(mockAttendance);
    api.getLeaves.mockResolvedValue(mockLeaves);
  });

  it("renders worker profile details and header correctly", async () => {
    render(<WorkerDetailModal worker={mockWorker} onClose={vi.fn()} />);

    expect(screen.getByText("Anita Devi")).toBeInTheDocument();
    expect(screen.getByText("HW-001")).toBeInTheDocument();
    expect(screen.getByText("ASHA Worker")).toBeInTheDocument();
    expect(screen.getByText("Phulwari Sharif PHC")).toBeInTheDocument();
    expect(screen.getByText(/9876543210/)).toBeInTheDocument();
    expect(
      screen.getByText("30-Day Attendance Timeline & Heatmap")
    ).toBeInTheDocument();
  });

  it("renders heatmap grid, legend, and past approved leaves", async () => {
    render(<WorkerDetailModal worker={mockWorker} onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Approved Leave History")).toBeInTheDocument();
      expect(screen.getByText("Casual Leave")).toBeInTheDocument();
      expect(screen.getByText(/Family wedding/)).toBeInTheDocument();
    });

    expect(screen.getAllByText("Present").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Half-day").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Leave").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Absent").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Unrecorded").length).toBeGreaterThan(0);
  });

  it("calls onClose when clicking close button or pressing Escape", async () => {
    const handleClose = vi.fn();
    render(<WorkerDetailModal worker={mockWorker} onClose={handleClose} />);

    const closeBtn = screen.getByLabelText("Close modal");
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
