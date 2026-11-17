import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ChatAgent from "./ChatAgent";
import { api } from "../api";
import { generateAttendancePDF } from "../utils/pdfExport";

vi.mock("../api", () => ({
  api: {
    sendChat: vi.fn(),
  },
}));

vi.mock("../utils/pdfExport", () => ({
  generateAttendancePDF: vi.fn(),
}));

describe("ChatAgent Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders header, welcome message, suggestions, and input form", () => {
    render(<ChatAgent />);

    expect(screen.getByText("🤖 AI Operations Agent")).toBeInTheDocument();
    expect(screen.getByText("AI Multi-Agent Runtime")).toBeInTheDocument();
    expect(screen.getByText(/Welcome to Swasthya Sathi AI/i)).toBeInTheDocument();

    // Check suggestion chips
    expect(
      screen.getByRole("button", { name: "Sunny Kumar ko aaj present mark karo" })
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Type in Hindi, English or Hinglish…")
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send" })).toBeInTheDocument();
  });

  it("sends message and displays agent response with action badges", async () => {
    api.sendChat.mockResolvedValueOnce({
      reply: "Sunny Kumar has been marked present for today.",
      actions_taken: ["mark_attendance"],
      language: "en",
    });

    render(<ChatAgent />);

    const input = screen.getByPlaceholderText("Type in Hindi, English or Hinglish…");
    const sendBtn = screen.getByRole("button", { name: "Send" });

    fireEvent.change(input, { target: { value: "Mark Sunny present" } });
    fireEvent.click(sendBtn);

    // Processing indicator should appear
    expect(screen.getByText("🧠 Processing...")).toBeInTheDocument();

    await waitFor(() => {
      expect(
        screen.getByText("Sunny Kumar has been marked present for today.")
      ).toBeInTheDocument();
    });

    // Check user message is displayed
    expect(screen.getByText("Mark Sunny present")).toBeInTheDocument();

    // Check action chip is displayed
    expect(screen.getByText("✓ mark_attendance")).toBeInTheDocument();

    // Download PDF button should appear for agent response
    const pdfBtn = screen.getByRole("button", { name: "📄 Download PDF" });
    expect(pdfBtn).toBeInTheDocument();

    fireEvent.click(pdfBtn);
    expect(generateAttendancePDF).toHaveBeenCalledWith(
      "Sunny Kumar has been marked present for today.",
      "en"
    );
  });

  it("sends message when clicking a suggestion chip", async () => {
    api.sendChat.mockResolvedValueOnce({
      reply: "Kajal Kumari attendance summary: 88% attendance rate.",
      actions_taken: ["get_worker_summary"],
      language: "hi",
    });

    render(<ChatAgent />);

    const suggestionBtn = screen.getByRole("button", {
      name: "Kajal Kumari ka attendance summary dikhao",
    });
    fireEvent.click(suggestionBtn);

    await waitFor(() => {
      expect(
        screen.getByText("Kajal Kumari attendance summary: 88% attendance rate.")
      ).toBeInTheDocument();
    });
  });

  it("handles agent error gracefully with fallback message", async () => {
    api.sendChat.mockRejectedValueOnce(new Error("Timeout"));

    render(<ChatAgent />);

    const input = screen.getByPlaceholderText("Type in Hindi, English or Hinglish…");
    const sendBtn = screen.getByRole("button", { name: "Send" });

    fireEvent.change(input, { target: { value: "Hello" } });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(
        screen.getByText(/AI Agent is temporarily unavailable/i)
      ).toBeInTheDocument();
    });
  });

  it("does not send empty or whitespace-only messages", () => {
    render(<ChatAgent />);

    const sendBtn = screen.getByRole("button", { name: "Send" });
    fireEvent.click(sendBtn);

    expect(api.sendChat).not.toHaveBeenCalled();
  });

  it("renders clinical verification chip and expands audit drawer on click", async () => {
    api.sendChat.mockResolvedValueOnce({
      reply: "ORS dosage for pediatric diarrhea is 5ml/kg.",
      actions_taken: [],
      hallucination_check: {
        is_flagged: false,
        confidence_score: 0.94,
        risk_level: "LOW",
        flagged_reasons: [],
        warning_message: null,
      },
    });

    render(<ChatAgent />);

    const input = screen.getByPlaceholderText("Type in Hindi, English or Hinglish…");
    const sendBtn = screen.getByRole("button", { name: "Send" });

    fireEvent.change(input, { target: { value: "ORS dosage" } });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(screen.getByText(/🛡️ MoHFW Verified/i)).toBeInTheDocument();
      expect(screen.getByText(/• 94%/i)).toBeInTheDocument();
    });

    // Click the verification chip to expand audit drawer
    const chipBtn = screen.getByRole("button", { name: /🛡️ MoHFW Verified/i });
    fireEvent.click(chipBtn);

    expect(screen.getByText("Clinical Safety & Hallucination Audit")).toBeInTheDocument();
    expect(screen.getByText(/MoHFW \/ National Health Mission \(NHM\) Bihar/i)).toBeInTheDocument();
    expect(screen.getByText(/No clinical hallucinations or protocol contradictions detected/i)).toBeInTheDocument();
  });

  it("renders mandatory medical disclaimer for high clinical risk response", async () => {
    api.sendChat.mockResolvedValueOnce({
      reply: "Administer injection oxytocin urgently.",
      actions_taken: [],
      hallucination_check: {
        is_flagged: true,
        confidence_score: 0.45,
        risk_level: "HIGH",
        flagged_reasons: ["Critical prescription medication without dosage validation"],
        warning_message: "High risk of adverse maternal event. Requires physician sign-off.",
      },
    });

    render(<ChatAgent />);

    const input = screen.getByPlaceholderText("Type in Hindi, English or Hinglish…");
    const sendBtn = screen.getByRole("button", { name: "Send" });

    fireEvent.change(input, { target: { value: "Oxytocin dosage" } });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(screen.getByText(/🚨 High Clinical Risk/i)).toBeInTheDocument();
      expect(screen.getByText(/🚨 Mandatory Medical Disclaimer/i)).toBeInTheDocument();
      expect(screen.getByText(/This response involves high-risk clinical advice/i)).toBeInTheDocument();
    });
  });
});
