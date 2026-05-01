import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ActionsTable } from "../ActionsTable";

const sampleAction = {
  policy_key: "default_access_policy",
  title: "Access My Data",
  description: "...",
  icon_path: "/icon.svg",
  custom_privacy_request_fields: { email: { label: "Email", field_type: "text" } },
};

describe("ActionsTable", () => {
  it("renders one row per action and reports field count", () => {
    render(
      <ActionsTable
        propertyId="p1"
        actions={[sampleAction]}
        onEditAction={jest.fn()}
        onAddAction={jest.fn()}
      />,
    );
    expect(screen.getByText("Access My Data")).toBeInTheDocument();
    expect(screen.getByText("1 field")).toBeInTheDocument();
  });

  it("calls onEditAction when 'Edit action' is clicked", async () => {
    const onEdit = jest.fn();
    render(
      <ActionsTable
        propertyId="p1"
        actions={[sampleAction]}
        onEditAction={onEdit}
        onAddAction={jest.fn()}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: /edit action/i }));
    expect(onEdit).toHaveBeenCalledWith(sampleAction);
  });
});
