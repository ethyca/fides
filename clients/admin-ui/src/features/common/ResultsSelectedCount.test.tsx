import { render, screen } from "@testing-library/react";

import { ResultsSelectedCount } from "./ResultsSelectedCount";

describe("ResultsSelectedCount", () => {
  it("does not show selected count when selectedIds is empty", () => {
    render(<ResultsSelectedCount selectedIds={[]} />);

    // Selected count should not be visible
    expect(screen.queryByTestId("selected-count")).not.toBeInTheDocument();
  });

  it("shows selected count when selectedIds has items", () => {
    const selectedIds = ["id1", "id2", "id3"];

    render(<ResultsSelectedCount selectedIds={selectedIds} />);

    // Selected count should be visible with correct count
    const selectedCount = screen.getByTestId("selected-count");
    expect(selectedCount).toBeInTheDocument();
    expect(selectedCount).toHaveTextContent("3 selected");
  });

  it("shows total results when provided", () => {
    render(<ResultsSelectedCount selectedIds={[]} totalResults={42} />);

    // Total results should be visible
    const totalResults = screen.getByTestId("total-results");
    expect(totalResults).toBeInTheDocument();
    expect(totalResults).toHaveTextContent("42 results");
  });

  it("shows both selected count and total results when both are provided", () => {
    const selectedIds = ["id1", "id2"];

    render(
      <ResultsSelectedCount selectedIds={selectedIds} totalResults={100} />,
    );

    // Selected count should be visible
    const selectedCount = screen.getByTestId("selected-count");
    expect(selectedCount).toBeInTheDocument();
    expect(selectedCount).toHaveTextContent("2 selected");

    // Total results should be visible
    const totalResults = screen.getByTestId("total-results");
    expect(totalResults).toBeInTheDocument();
    expect(totalResults).toHaveTextContent("100 results");
  });

  it("does not show anything when no selectedIds and no totalResults", () => {
    render(<ResultsSelectedCount selectedIds={[]} />);

    // Neither should be visible
    expect(screen.queryByTestId("selected-count")).not.toBeInTheDocument();
    expect(screen.queryByTestId("total-results")).not.toBeInTheDocument();
  });
});
