import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { api } from "../api";
import WeeklyInsights from "./WeeklyInsights";

vi.mock("../api", () => ({
  api: {
    getWeeklyInsights: vi.fn(),
  },
}));

describe("WeeklyInsights", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a loading skeleton and disables controls while analysis is running", async () => {
    let resolveRequest;
    api.getWeeklyInsights.mockReturnValue(
      new Promise((resolve) => {
        resolveRequest = resolve;
      })
    );

    render(<WeeklyInsights />);

    fireEvent.click(screen.getByRole("button", { name: "Run weekly analysis" }));

    expect(
      screen.getByRole("status", {
        name: "Generating weekly attendance insights",
      })
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Generating..." })).toBeDisabled();
    expect(screen.getByRole("button", { name: "हिंदी" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "English" })).toBeDisabled();

    resolveRequest({ report: "Weekly attendance report" });

    expect(await screen.findByText("Weekly attendance report")).toBeInTheDocument();
  });

  it("renders the returned weekly report", async () => {
    api.getWeeklyInsights.mockResolvedValue({ report: "Attendance is improving." });

    render(<WeeklyInsights />);

    fireEvent.click(screen.getByRole("button", { name: "Run weekly analysis" }));

    expect(await screen.findByText("Attendance is improving.")).toBeInTheDocument();
  });

  it("shows a friendly error message when analysis fails", async () => {
    api.getWeeklyInsights.mockRejectedValue(new Error("Request failed"));

    render(<WeeklyInsights />);

    fireEvent.click(screen.getByRole("button", { name: "Run weekly analysis" }));

    await waitFor(() => {
      expect(
        screen.getByRole("alert")
      ).toHaveTextContent("Unable to generate weekly attendance insights. Please try again.");
    });
  });
});
