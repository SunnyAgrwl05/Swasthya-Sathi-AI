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

  it("renders verified guidance chip and expands safety breakdown on click", async () => {
    api.sendChat.mockResolvedValueOnce({
      reply: "ORS and Zinc solution is the standard IMNCI protocol for acute diarrhea.",
      actions_taken: [],
      language: "en",
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
    fireEvent.change(input, { target: { value: "ORS diarrhea protocol" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => {
      expect(screen.getByText(/Verified Guidance/i)).toBeInTheDocument();
      expect(screen.getByText("94%")).toBeInTheDocument();
    });

    // Click chip to toggle clinical safety breakdown drawer
    const chip = screen.getByRole("button", { name: /verified guidance/i });
    fireEvent.click(chip);

    expect(screen.getByText("Clinical Safety Breakdown")).toBeInTheDocument();
    expect(screen.getByText("MoHFW Bihar / IMNCI")).toBeInTheDocument();
    expect(screen.getByText(/Mandatory Clinical Notice/i)).toBeInTheDocument();
  });

  it("renders warning banner and flagged badge for high-risk responses", async () => {
    api.sendChat.mockResolvedValueOnce({
      reply: "Administer high dose medication immediately.",
      actions_taken: [],
      language: "en",
      hallucination_check: {
        is_flagged: true,
        confidence_score: 0.58,
        risk_level: "HIGH",
        flagged_reasons: ["Critical dosage instruction without physician consultation"],
        warning_message: "Requires physician authorization.",
      },
    });

    render(<ChatAgent />);

    const input = screen.getByPlaceholderText("Type in Hindi, English or Hinglish…");
    fireEvent.change(input, { target: { value: "Administer drug" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => {
      expect(
        screen.getByText(/Requires verification by PHC Medical Officer/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/Flagged for Clinical Review/i)).toBeInTheDocument();
      expect(screen.getByText("58%")).toBeInTheDocument();
    });
  });

  it("renders moderate clinical advisory badge for medium risk responses", async () => {
    api.sendChat.mockResolvedValueOnce({
      reply: "Monitor temperature every 4 hours.",
      actions_taken: [],
      language: "en",
      hallucination_check: {
        is_flagged: false,
        confidence_score: 0.76,
        risk_level: "MEDIUM",
        flagged_reasons: [],
      },
    });

    render(<ChatAgent />);

    const input = screen.getByPlaceholderText("Type in Hindi, English or Hinglish…");
    fireEvent.change(input, { target: { value: "Fever monitoring" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => {
      expect(screen.getByText(/Clinical Advisory/i)).toBeInTheDocument();
      expect(screen.getByText("76%")).toBeInTheDocument();
    });
  });
});
