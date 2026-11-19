import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import WorkerDetailModal from "./WorkerDetailModal";
import { api } from "../api";

vi.mock("../api", () => ({
  api: {
    getWorkerAttendanceHistory: vi.fn(),
    getLeaves: vi.fn(),
    applyLeave: vi.fn(),
    updateLeaveStatus: vi.fn(),
  },
}));

describe("WorkerDetailModal Component", () => {
  const mockWorker = {
    id: 1,
    name: "Sunita Devi",
    role: "ASHA",
    center: "Patna Central",
    phone: "9876543210",
  };

  const mockHistory = {
    worker_id: 1,
    name: "Sunita Devi",
    role: "ASHA",
    center: "Patna Central",
    days: [
      { date: "2026-11-17", status: "present", note: "Vaccination drive", marked_by: "agent" },
      { date: "2026-11-16", status: "half-day", note: "Field visit", marked_by: "agent" },
      { date: "2026-11-15", status: "leave", note: "Casual leave", marked_by: "supervisor" },
      { date: "2026-11-14", status: "absent", note: null, marked_by: "agent" },
    ],
    total_days: 4,
    present_days: 1,
    absent_days: 1,
    leave_days: 1,
    attendance_pct: 25.0,
  };

  const mockLeaves = [
    {
      id: 10,
      worker_id: 1,
      start_date: "2026-11-15",
      end_date: "2026-11-15",
      leave_type: "casual",
      reason: "Family emergency",
      status: "Approved",
      approved_by: "Dr. Sharma",
    },
    {
      id: 11,
      worker_id: 1,
      start_date: "2026-11-20",
      end_date: "2026-11-22",
      leave_type: "training",
      reason: "District workshop",
      status: "Pending",
      approved_by: "Supervisor",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    api.getWorkerAttendanceHistory.mockResolvedValue(mockHistory);
    api.getLeaves.mockResolvedValue(mockLeaves);
    api.applyLeave.mockResolvedValue({
      id: 12,
      worker_id: 1,
      start_date: "2026-11-25",
      end_date: "2026-11-26",
      leave_type: "sick",
      status: "Approved",
    });
    api.updateLeaveStatus.mockResolvedValue({
      id: 11,
      status: "Approved",
    });
  });

  it("renders worker details and 30-day heatmap metrics", async () => {
    render(<WorkerDetailModal worker={mockWorker} onClose={vi.fn()} />);

    expect(screen.getByText(/Sunita Devi/i)).toBeInTheDocument();
    expect(screen.getByText(/Patna Central/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/Overall Rate: 25%/i)).toBeInTheDocument();
      expect(screen.getByText(/1 Present/i)).toBeInTheDocument();
    });
  });

  it("renders GitHub Graph SVG and can toggle to Day Matrix view", async () => {
    render(<WorkerDetailModal worker={mockWorker} onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Attendance intensity graph/i)).toBeInTheDocument();
    });

    const matrixBtn = screen.getByRole("button", { name: /Day Matrix/i });
    fireEvent.click(matrixBtn);

    // Matrix view shows day numbers
    expect(screen.getByText("17")).toBeInTheDocument();
    expect(screen.getByText("16")).toBeInTheDocument();
  });

  it("displays existing leave records with status badges and approve/reject actions", async () => {
    render(<WorkerDetailModal worker={mockWorker} onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getAllByText(/Casual Leave/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Training Leave/i).length).toBeGreaterThan(0);
      expect(screen.getByText(/Pending/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Approved/i).length).toBeGreaterThan(0);
    });

    // Click Approve on pending leave
    const approveBtn = screen.getByRole("button", { name: /✓ Approve/i });
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(api.updateLeaveStatus).toHaveBeenCalledWith(11, "Approved");
    });
  });

  it("submits a new leave request and triggers reload", async () => {
    const onLeaveApplied = vi.fn();
    render(<WorkerDetailModal worker={mockWorker} onClose={vi.fn()} onLeaveApplied={onLeaveApplied} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Record Leave Request/i })).toBeInTheDocument();
    });

    const submitBtn = screen.getByRole("button", { name: /Record Leave Request/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.applyLeave).toHaveBeenCalled();
      expect(onLeaveApplied).toHaveBeenCalled();
    });
  });
});
