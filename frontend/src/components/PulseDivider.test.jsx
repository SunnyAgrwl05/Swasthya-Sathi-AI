import { render } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import PulseDivider from "./PulseDivider";

describe("PulseDivider Component", () => {
  it("renders the SVG heartbeat pulse graphic", () => {
    const { container } = render(<PulseDivider />);
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveAttribute("viewBox", "0 0 400 40");

    const line = container.querySelector("line");
    expect(line).toBeInTheDocument();

    const path = container.querySelector("path");
    expect(path).toBeInTheDocument();
    expect(path).toHaveClass("animate-pulseLine");
  });
});
