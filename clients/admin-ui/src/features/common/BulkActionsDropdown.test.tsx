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

  it("disables button when selectedIds is empty", () => {
    render(<BulkActionsDropdown selectedIds={[]} menuItems={mockMenuItems} />);

    // Button should be disabled
    const button = screen.getByTestId("bulk-actions-btn");
    expect(button).toBeDisabled();
  });

  it("enables button when selectedIds has items", () => {
    const selectedIds = ["id1", "id2", "id3"];

    render(
      <BulkActionsDropdown
        selectedIds={selectedIds}
        menuItems={mockMenuItems}
      />,
    );

    // Button should be enabled
    const button = screen.getByTestId("bulk-actions-btn");
    expect(button).not.toBeDisabled();
  });
});
