import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import App from "./App";

vi.mock("./api", () => ({
    api: {
        getWorkers: vi.fn().mockResolvedValue([]),
        getSummary: vi.fn().mockResolvedValue([]),
    },
}));

vi.mock("./components/Header", () => ({
    default: () => <div>Header</div>,
}));

vi.mock("./components/StatCards", () => ({
    default: () => <div>StatCards</div>,
}));

vi.mock("./components/AttendanceChart", () => ({
    default: () => <div>AttendanceChart</div>,
}));

vi.mock("./components/WorkerTable", () => ({
    default: () => <div>WorkerTable</div>,
}));

vi.mock("./components/ChatAgent", () => ({
    default: () => <div>ChatAgent</div>,
}));

vi.mock("./components/DailyBroadcast", () => ({
    default: () => <div>DailyBroadcast</div>,
}));

vi.mock("./components/WeeklyInsights", () => ({
    default: () => <div>WeeklyInsights</div>,
}));

describe("App", () => {
    it("renders successfully", async () => {
        render(<App />);

        expect(await screen.findByText("Header")).toBeInTheDocument();
        expect(screen.getByText("ChatAgent")).toBeInTheDocument();
    });
});