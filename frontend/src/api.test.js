import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { api } from "./api";

describe("api service", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it("getWorkers fetches /api/workers with correct headers", async () => {
    const mockWorkers = [{ id: 1, name: "Anita Devi", role: "ASHA" }];
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockWorkers,
    });

    const result = await api.getWorkers();

    expect(global.fetch).toHaveBeenCalledWith("/api/workers", {
      headers: { "Content-Type": "application/json" },
    });
    expect(result).toEqual(mockWorkers);
  });

  it("getSummary fetches /api/analytics/summary with default and custom days", async () => {
    const mockSummary = [{ worker_id: 1, attendance_pct: 90 }];
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockSummary,
    });

    // Default days = 30
    const result30 = await api.getSummary();
    expect(global.fetch).toHaveBeenCalledWith("/api/analytics/summary?days=30", {
      headers: { "Content-Type": "application/json" },
    });
    expect(result30).toEqual(mockSummary);

    // Custom days = 7
    await api.getSummary(7);
    expect(global.fetch).toHaveBeenCalledWith("/api/analytics/summary?days=7", {
      headers: { "Content-Type": "application/json" },
    });
  });

  it("sendChat posts JSON body to /api/chat", async () => {
    const mockReply = { reply: "Attendance marked", actions_taken: ["mark_attendance"] };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockReply,
    });

    const result = await api.sendChat("Mark Anita present");

    expect(global.fetch).toHaveBeenCalledWith("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: "Mark Anita present", context: null }),
    });
    expect(result).toEqual(mockReply);
  });

  it("getDailyBroadcast fetches /api/broadcast/daily", async () => {
    const mockBroadcast = { message: "Today 14/15 workers present." };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockBroadcast,
    });

    const result = await api.getDailyBroadcast();

    expect(global.fetch).toHaveBeenCalledWith("/api/broadcast/daily", {
      headers: { "Content-Type": "application/json" },
    });
    expect(result).toEqual(mockBroadcast);
  });

  it("getWeeklyInsights posts language payload to /api/insights/weekly", async () => {
    const mockInsights = { insight: "High performance across all centers." };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockInsights,
    });

    const result = await api.getWeeklyInsights("en");

    expect(global.fetch).toHaveBeenCalledWith("/api/insights/weekly", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ language: "en" }),
    });
    expect(result).toEqual(mockInsights);
  });

  it("checkHallucination posts query and response to /api/safety/check-hallucination", async () => {
    const mockCheck = { is_flagged: false, confidence_score: 0.95, risk_level: "LOW" };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockCheck,
    });

    const result = await api.checkHallucination("dosage", "Take ORS", "clinical context", 0.9);

    expect(global.fetch).toHaveBeenCalledWith("/api/safety/check-hallucination", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: "dosage",
        response: "Take ORS",
        context: "clinical context",
        retrieval_score: 0.9,
      }),
    });
    expect(result).toEqual(mockCheck);
  });

  it("throws error when response status is not ok", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
    });

    await expect(api.getWorkers()).rejects.toThrow("API error 500");
  });
});
