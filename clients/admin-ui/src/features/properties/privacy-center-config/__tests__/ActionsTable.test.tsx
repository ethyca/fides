import { render as rtlRender, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FidesUIProvider } from "fidesui";

import { ActionsTable } from "../ActionsTable";

jest.mock("~/features/policies/policy.slice", () => ({
  useGetPoliciesQuery: () => ({ data: { items: [] } }),
}));

const render = (ui: React.ReactElement) =>
  rtlRender(<FidesUIProvider>{ui}</FidesUIProvider>);

const sampleAction = {
  policy_key: "default_access_policy",
  title: "Access My Data",
  description: "...",
  icon_path: "/icon.svg",
  custom_privacy_request_fields: {
    email: { label: "Email", field_type: "text" },
  },
};

describe("ActionsTable", () => {
  it("renders one row per action and reports field count", () => {
    render(
      <ActionsTable
        propertyId="p1"
        actions={[sampleAction]}
        onEditAction={jest.fn()}
        onAddAction={jest.fn()}
        onDeleteAction={jest.fn()}
      />,
    );
    expect(screen.getByText("Access My Data")).toBeInTheDocument();
    expect(screen.getByText("1 field")).toBeInTheDocument();
  });

  it("shows 'Edit form' link when propertyId is set", () => {
    render(
      <ActionsTable
        propertyId="p1"
        actions={[sampleAction]}
        onEditAction={jest.fn()}
        onAddAction={jest.fn()}
        onDeleteAction={jest.fn()}
      />,
    );
    expect(
      screen.getByRole("button", { name: /edit form/i }),
    ).toBeInTheDocument();
  });

  it("hides 'Edit form' link when propertyId is empty", () => {
    render(
      <ActionsTable
        propertyId=""
        actions={[sampleAction]}
        onEditAction={jest.fn()}
        onAddAction={jest.fn()}
        onDeleteAction={jest.fn()}
      />,
    );
    expect(
      screen.queryByRole("button", { name: /edit form/i }),
    ).not.toBeInTheDocument();
  });

  it("calls onEditAction when 'Edit action' is clicked", async () => {
    const onEdit = jest.fn();
    render(
      <ActionsTable
        propertyId="p1"
        actions={[sampleAction]}
        onEditAction={onEdit}
        onAddAction={jest.fn()}
        onDeleteAction={jest.fn()}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: /edit action/i }));
    expect(onEdit).toHaveBeenCalledWith(sampleAction);
  });
});
