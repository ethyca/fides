import { render, screen } from "@testing-library/react";

import { BulkActionsDropdown } from "./BulkActionsDropdown";

describe("BulkActionsDropdown", () => {
  const mockMenuItems = [
    {
      key: "action1",
      label: "Action 1",
    },
    {
      key: "action2",
      label: "Action 2",
    },
  ];

  it("does not show selected count and disables button when selectedIds is empty", () => {
    render(<BulkActionsDropdown selectedIds={[]} menuItems={mockMenuItems} />);

    // Selected count should not be visible
    expect(screen.queryByTestId("selected-count")).not.toBeInTheDocument();

    // Button should be disabled
    const button = screen.getByTestId("bulk-actions-btn");
    expect(button).toBeDisabled();
  });

  it("shows selected count and enables button when selectedIds has items", () => {
    const selectedIds = ["id1", "id2", "id3"];

    render(
      <BulkActionsDropdown
        selectedIds={selectedIds}
        menuItems={mockMenuItems}
      />,
    );

    // Selected count should be visible with correct count
    const selectedCount = screen.getByTestId("selected-count");
    expect(selectedCount).toBeInTheDocument();
    expect(selectedCount).toHaveTextContent("3 selected");

    // Button should be enabled
    const button = screen.getByTestId("bulk-actions-btn");
    expect(button).not.toBeDisabled();
  });
});
