import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusBadge } from "./status-badge";

describe("StatusBadge", () => {
  it("uses safe human-readable copy for reject", () => {
    render(<StatusBadge value="reject" />);
    expect(screen.getByText("建议退回人工核查")).toBeInTheDocument();
  });
});
