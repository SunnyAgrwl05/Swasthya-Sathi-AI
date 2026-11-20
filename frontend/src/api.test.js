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

  it("importWorkersCsv sends multipart form data to /api/workers/import-csv", async () => {
    const mockSummary = { total_rows: 5, created: 4, skipped: 1, errors: [] };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockSummary,
    });

    const fakeFile = new File(["worker_code,name\nHW1,Pooja"], "test.csv", { type: "text/csv" });
    const result = await api.importWorkersCsv(fakeFile);

    expect(global.fetch).toHaveBeenCalledWith("/api/workers/import-csv", expect.objectContaining({
      method: "POST",
      body: expect.any(FormData),
    }));
    expect(result).toEqual(mockSummary);
  });

  it("exportAttendanceCsvUrl constructs correct query params", () => {
    const url1 = api.exportAttendanceCsvUrl("2026-11", "Danapur");
    expect(url1).toBe("/api/attendance/export-csv?month=2026-11&center=Danapur");

    const url2 = api.exportAttendanceCsvUrl("2026-11", "All");
    expect(url2).toBe("/api/attendance/export-csv?month=2026-11");
  });

  it("sampleWorkersCsvUrl points to sample-csv endpoint", () => {
    expect(api.sampleWorkersCsvUrl).toBe("/api/workers/sample-csv");
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

  it("getAttendance fetches /api/attendance with optional workerId", async () => {
    const mockAtt = [{ id: 1, date: "2026-11-01", status: "present" }];
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockAtt,
    });

    const resAll = await api.getAttendance();
    expect(global.fetch).toHaveBeenCalledWith("/api/attendance", {
      headers: { "Content-Type": "application/json" },
    });
    expect(resAll).toEqual(mockAtt);

    await api.getAttendance(5);
    expect(global.fetch).toHaveBeenCalledWith("/api/attendance?worker_id=5", {
      headers: { "Content-Type": "application/json" },
    });
  });

  it("getLeaves fetches /api/leaves with optional workerId", async () => {
    const mockLeaves = [{ id: 1, start_date: "2026-11-01", leave_type: "casual" }];
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockLeaves,
    });

    const resAll = await api.getLeaves();
    expect(global.fetch).toHaveBeenCalledWith("/api/leaves", {
      headers: { "Content-Type": "application/json" },
    });
    expect(resAll).toEqual(mockLeaves);

    await api.getLeaves(3);
    expect(global.fetch).toHaveBeenCalledWith("/api/leaves?worker_id=3", {
      headers: { "Content-Type": "application/json" },
    });
  });

  it("createLeave posts leave payload to /api/leaves", async () => {
    const leavePayload = {
      worker_id: 1,
      start_date: "2026-11-01",
      end_date: "2026-11-05",
      leave_type: "medical",
      reason: "Viral fever",
    };
    const mockCreated = { id: 10, ...leavePayload };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockCreated,
    });

    const res = await api.createLeave(leavePayload);
    expect(global.fetch).toHaveBeenCalledWith("/api/leaves", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(leavePayload),
    });
    expect(res).toEqual(mockCreated);
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

  it("getWorker fetches /api/workers/:id", async () => {
    const mockWorker = { id: 1, name: "Anita Devi" };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockWorker,
    });

    const res = await api.getWorker(1);
    expect(global.fetch).toHaveBeenCalledWith("/api/workers/1", {
      headers: { "Content-Type": "application/json" },
    });
    expect(res).toEqual(mockWorker);
  });

  it("updateWorker sends PUT to /api/workers/:id", async () => {
    const payload = { name: "Updated Name" };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 1, ...payload }),
    });

    await api.updateWorker(1, payload);
    expect(global.fetch).toHaveBeenCalledWith("/api/workers/1", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  });

  it("exportAttendanceCSVUrl builds valid CSV download query", () => {
    const url = api.exportAttendanceCSVUrl({ status: "present", center: "Patna PHC" });
    expect(url).toContain("/api/attendance/export-csv?status=present&center=Patna+PHC");
  });

  it("exportWorkersCSVUrl builds valid workers CSV download query", () => {
    const url = api.exportWorkersCSVUrl({ center: "Patna Sadar", role: "ASHA" });
    expect(url).toContain("/api/workers/export-csv?center=Patna+Sadar&role=ASHA");
  });

  it("importWorkersCSV sends FormData to /api/workers/import-csv", async () => {
    const mockFile = new Blob(["name,center\nAnita,Danapur"], { type: "text/csv" });
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ total_rows: 1, created: 1, updated: 0, errors: [] }),
    });

    const res = await api.importWorkersCSV(mockFile);
    expect(global.fetch).toHaveBeenCalledWith("/api/workers/import-csv", expect.objectContaining({
      method: "POST",
    }));
    expect(res.created).toBe(1);
  });

  it("importAttendanceCSV sends FormData to /api/attendance/import-csv", async () => {
    const mockFile = new Blob(["worker_code,date,status\nHW001,2026-11-01,present"], { type: "text/csv" });
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ total_rows: 1, processed: 1, errors: [] }),
    });

    const res = await api.importAttendanceCSV(mockFile);
    expect(global.fetch).toHaveBeenCalledWith("/api/attendance/import-csv", expect.objectContaining({
      method: "POST",
    }));
    expect(res.processed).toBe(1);
  it("dispatchSMSAlerts posts payload to /api/notifications/dispatch-sms", async () => {
    const mockSummary = { status: "completed", total_recipients: 10, sent: 10, failed: 0 };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockSummary,
    });

    const payload = { target: "all", message: "Duty alert" };
    const res = await api.dispatchSMSAlerts(payload);

    expect(global.fetch).toHaveBeenCalledWith("/api/notifications/dispatch-sms", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    expect(res).toEqual(mockSummary);
  });

  it("getNotificationLogs fetches /api/notifications/logs with limit", async () => {
    const mockLogs = [{ id: 1, worker_name: "Anita", status: "Sent" }];
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockLogs,
    });

    const res = await api.getNotificationLogs(15);
    expect(global.fetch).toHaveBeenCalledWith("/api/notifications/logs?limit=15", {
      headers: { "Content-Type": "application/json" },
    });
    expect(res).toEqual(mockLogs);
  });
});
