import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import DailyBroadcast from "./DailyBroadcast";
import { api } from "../api";

vi.mock("../api", () => ({
  api: {
    getDailyBroadcast: vi.fn(),
    dispatchSMSAlerts: vi.fn(),
  },
}));

describe("DailyBroadcast Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders initial state with heading and generate button", () => {
    render(<DailyBroadcast />);

    expect(screen.getByText("📢 Daily Broadcast")).toBeInTheDocument();
    expect(
      screen.getByText("AI-generated daily operational update")
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "✨ Generate Today's Update" })
    ).toBeInTheDocument();
  });

  it("generates broadcast successfully and displays formatted message and WhatsApp link", async () => {
    const mockMessage = "*Daily Health Ops Update*\nAll 15 centers active.\nAttendance rate: 94%.";
    api.getDailyBroadcast.mockResolvedValueOnce({ message: mockMessage });

    render(<DailyBroadcast />);

    const generateBtn = screen.getByRole("button", {
      name: "✨ Generate Today's Update",
    });
    fireEvent.click(generateBtn);

    expect(screen.getByText("Generating...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Daily Health Ops Update")).toBeInTheDocument();
    });

    expect(screen.getByText("All 15 centers active.")).toBeInTheDocument();
    expect(screen.getByText("Attendance rate: 94%.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "🔄 Regenerate" })).toBeInTheDocument();

    const waLink = screen.getByRole("link", { name: /Share on WhatsApp/i });
    expect(waLink).toBeInTheDocument();
    expect(waLink.getAttribute("href")).toContain("https://wa.me/?text=");
  });

  it("displays error message when broadcast API call fails", async () => {
    api.getDailyBroadcast.mockRejectedValueOnce(new Error("Network Error"));

    render(<DailyBroadcast />);

    const generateBtn = screen.getByRole("button", {
      name: "✨ Generate Today's Update",
    });
    fireEvent.click(generateBtn);

    await waitFor(() => {
      expect(
        screen.getByText("Backend se connect nahi ho pa raha.")
      ).toBeInTheDocument();
    });
  });

  it("dispatches SMS alerts and displays successful delivery badge", async () => {
    api.getDailyBroadcast.mockResolvedValueOnce({ message: "Attendance alert: 3 workers pending." });
    api.dispatchSMSAlerts.mockResolvedValueOnce({
      status: "completed",
      total_recipients: 15,
      sent: 15,
      failed: 0,
    });

    render(<DailyBroadcast />);

    const generateBtn = screen.getByRole("button", {
      name: "✨ Generate Today's Update",
    });
    fireEvent.click(generateBtn);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "📨 Dispatch SMS Alerts" })).toBeInTheDocument();
    });

    const smsBtn = screen.getByRole("button", { name: "📨 Dispatch SMS Alerts" });
    fireEvent.click(smsBtn);

    await waitFor(() => {
      expect(screen.getByText(/✓ SMS Broadcast Dispatched:/i)).toBeInTheDocument();
      expect(screen.getByText(/15 messages delivered to offline field workers/i)).toBeInTheDocument();
    });

    expect(api.dispatchSMSAlerts).toHaveBeenCalledWith({
      message: "Attendance alert: 3 workers pending.",
      target: "all",
    });
  });

  it("handles SMS dispatch failure gracefully with alert notice", async () => {
    api.getDailyBroadcast.mockResolvedValueOnce({ message: "Test Broadcast" });
    api.dispatchSMSAlerts.mockRejectedValueOnce(new Error("Gateway Error"));

    render(<DailyBroadcast />);

    fireEvent.click(screen.getByRole("button", { name: "✨ Generate Today's Update" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "📨 Dispatch SMS Alerts" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "📨 Dispatch SMS Alerts" }));

    await waitFor(() => {
      expect(screen.getByText(/⚠️ Dispatch Notice:/i)).toBeInTheDocument();
      expect(screen.getByText(/0 messages delivered to offline field workers \(1 failed\)/i)).toBeInTheDocument();
    });
  });
});
