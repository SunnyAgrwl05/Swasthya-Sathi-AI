/**
 * ChatAgent.test.jsx
 *
 * Tests the ChatAgent component:
 * - Welcome screen is shown before first message
 * - User message is appended and input cleared on submit
 * - Agent reply is rendered after api.sendChat resolves
 * - Error state renders a fallback message when api.sendChat rejects
 * - Action badge chips are rendered when actions_taken is non-empty
 * - Loading spinner is shown while request is in-flight
 * - Suggestion buttons trigger a send with correct text
 */

import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { vi } from "vitest";
import ChatAgent from "./ChatAgent";

// Mock the api module so we never hit a real backend
vi.mock("../api", () => ({
  api: {
    sendChat: vi.fn(),
  },
}));

// Mock generateAttendancePDF so jsPDF doesn't run in tests
vi.mock("../utils/pdfExport", () => ({
  generateAttendancePDF: vi.fn(),
}));

import { api } from "../api";

function setup() {
  return render(<ChatAgent />);
}

describe("ChatAgent – Welcome screen", () => {
  it("shows the welcome panel before any interaction", () => {
    setup();
    expect(screen.getByText(/Welcome to Swasthya Sathi AI/i)).toBeInTheDocument();
  });

  it("hides the welcome panel after the first message is sent", async () => {
    api.sendChat.mockResolvedValueOnce({
      reply: "Done.",
      actions_taken: [],
      language: "en",
    });
    setup();

    fireEvent.change(screen.getByPlaceholderText(/Type in Hindi/i), {
      target: { value: "Hello" },
    });
    fireEvent.submit(screen.getByRole("button", { name: /send/i }).closest("form"));

    await waitFor(() => expect(screen.queryByText(/Welcome to Swasthya Sathi AI/i)).not.toBeInTheDocument());
  });
});

describe("ChatAgent – Message flow", () => {
  it("displays the user message in the chat", async () => {
    api.sendChat.mockResolvedValueOnce({ reply: "OK", actions_taken: [], language: "en" });
    setup();

    fireEvent.change(screen.getByPlaceholderText(/Type in Hindi/i), {
      target: { value: "Who is absent today?" },
    });
    fireEvent.submit(screen.getByRole("button", { name: /send/i }).closest("form"));

    await waitFor(() => expect(screen.getByText("Who is absent today?")).toBeInTheDocument());
  });

  it("clears the input field after submitting", async () => {
    api.sendChat.mockResolvedValueOnce({ reply: "OK", actions_taken: [], language: "en" });
    setup();

    const input = screen.getByPlaceholderText(/Type in Hindi/i);
    fireEvent.change(input, { target: { value: "Test message" } });
    fireEvent.submit(screen.getByRole("button", { name: /send/i }).closest("form"));

    await waitFor(() => expect(input.value).toBe(""));
  });

  it("renders the agent reply after api.sendChat resolves", async () => {
    api.sendChat.mockResolvedValueOnce({
      reply: "Sunita Devi is absent today.",
      actions_taken: [],
      language: "en",
    });
    setup();

    fireEvent.change(screen.getByPlaceholderText(/Type in Hindi/i), {
      target: { value: "Who is absent?" },
    });
    fireEvent.submit(screen.getByRole("button", { name: /send/i }).closest("form"));

    await waitFor(() =>
      expect(screen.getByText(/Sunita Devi is absent today/i)).toBeInTheDocument()
    );
  });

  it("shows an error fallback message when api.sendChat rejects", async () => {
    api.sendChat.mockRejectedValueOnce(new Error("Network error"));
    setup();

    fireEvent.change(screen.getByPlaceholderText(/Type in Hindi/i), {
      target: { value: "Mark Ravi present" },
    });
    fireEvent.submit(screen.getByRole("button", { name: /send/i }).closest("form"));

    await waitFor(() =>
      expect(screen.getByText(/AI Agent is temporarily unavailable/i)).toBeInTheDocument()
    );
  });
});

describe("ChatAgent – Action badges", () => {
  it("renders action chip badges for each tool called", async () => {
    api.sendChat.mockResolvedValueOnce({
      reply: "Marked present.",
      actions_taken: ["mark_attendance", "get_attendance_summary"],
      language: "en",
    });
    setup();

    fireEvent.change(screen.getByPlaceholderText(/Type in Hindi/i), {
      target: { value: "Mark present" },
    });
    fireEvent.submit(screen.getByRole("button", { name: /send/i }).closest("form"));

    await waitFor(() => {
      expect(screen.getByText(/mark_attendance/i)).toBeInTheDocument();
      expect(screen.getByText(/get_attendance_summary/i)).toBeInTheDocument();
    });
  });

  it("renders no action badges when actions_taken is empty", async () => {
    api.sendChat.mockResolvedValueOnce({
      reply: "Hello there.",
      actions_taken: [],
      language: "en",
    });
    setup();

    fireEvent.change(screen.getByPlaceholderText(/Type in Hindi/i), {
      target: { value: "Hello" },
    });
    fireEvent.submit(screen.getByRole("button", { name: /send/i }).closest("form"));

    await waitFor(() => expect(screen.getByText("Hello there.")).toBeInTheDocument());
    // No chip elements expected
    expect(screen.queryAllByText(/✔/).length).toBe(0);
  });
});

describe("ChatAgent – Loading state", () => {
  it("shows the Processing indicator while awaiting reply", async () => {
    let resolve;
    api.sendChat.mockReturnValueOnce(
      new Promise((res) => { resolve = res; })
    );
    setup();

    fireEvent.change(screen.getByPlaceholderText(/Type in Hindi/i), {
      target: { value: "Hello" },
    });
    fireEvent.submit(screen.getByRole("button", { name: /send/i }).closest("form"));

    expect(screen.getByText(/Processing/i)).toBeInTheDocument();

    // Resolve so test cleans up without warnings
    await act(async () => { resolve({ reply: "Done", actions_taken: [], language: "en" }); });
  });
});

describe("ChatAgent – Suggestion chips", () => {
  it("sends the correct text when a suggestion chip is clicked", async () => {
    api.sendChat.mockResolvedValueOnce({ reply: "OK", actions_taken: [], language: "en" });
    setup();

    const suggestion = screen.getByRole("button", { name: /kajal kumari ka attendance/i });
    fireEvent.click(suggestion);

    await waitFor(() =>
      expect(api.sendChat).toHaveBeenCalledWith("Kajal Kumari ka attendance summary dikhao")
    );
  });
});
