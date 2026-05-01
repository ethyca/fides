import { render as rtlRender, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FidesUIProvider } from "fidesui";

import { FieldPropertiesPanel } from "../FieldPropertiesPanel";
import type { JsonRenderSpec } from "../mapper";

const render = (ui: React.ReactElement) =>
  rtlRender(<FidesUIProvider>{ui}</FidesUIProvider>);

const noop = () => {};

const specWithText: JsonRenderSpec = {
  root: "form",
  elements: {
    form: { type: "Form", props: {}, children: ["f_email"] },
    f_email: {
      type: "Text",
      props: { name: "email", label: "Email", required: false },
      children: [],
    },
  },
};

const specWithSelect: JsonRenderSpec = {
  root: "form",
  elements: {
    form: { type: "Form", props: {}, children: ["f_color"] },
    f_color: {
      type: "Select",
      props: {
        name: "color",
        label: "Color",
        required: false,
        options: ["Red", "Blue"],
      },
      children: [],
    },
  },
};

describe("FieldPropertiesPanel", () => {
  it("shows the empty state when nothing is selected", () => {
    render(
      <FieldPropertiesPanel
        spec={specWithText}
        selectedElementId={null}
        onUpdateField={noop}
        onRemoveField={noop}
      />,
    );
    expect(
      screen.getByText(/select a field to edit its properties/i),
    ).toBeInTheDocument();
  });

  it("propagates label edits via onUpdateField", async () => {
    const onUpdateField = jest.fn();
    render(
      <FieldPropertiesPanel
        spec={specWithText}
        selectedElementId="f_email"
        onUpdateField={onUpdateField}
        onRemoveField={noop}
      />,
    );
    const labelInput = screen.getByTestId("prop-label");
    await userEvent.type(labelInput, "!");
    // Last call should reflect the new label
    const lastCall = onUpdateField.mock.calls.at(-1);
    expect(lastCall?.[0]).toBe("f_email");
    expect((lastCall?.[1] as { label: string }).label).toBe("Email!");
  });

  it("renders Select-specific fields with options editor", () => {
    render(
      <FieldPropertiesPanel
        spec={specWithSelect}
        selectedElementId="f_color"
        onUpdateField={noop}
        onRemoveField={noop}
      />,
    );
    expect(screen.getByTestId("option-input-0")).toHaveValue("Red");
    expect(screen.getByTestId("option-input-1")).toHaveValue("Blue");
    expect(screen.getByTestId("option-add")).toBeInTheDocument();
  });

  it("confirms before removing the field", async () => {
    const onRemoveField = jest.fn();
    render(
      <FieldPropertiesPanel
        spec={specWithText}
        selectedElementId="f_email"
        onUpdateField={noop}
        onRemoveField={onRemoveField}
      />,
    );
    await userEvent.click(screen.getByTestId("remove-field-button"));

    // Confirmation modal renders in a portal; find the "Remove" button inside it.
    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveTextContent(/remove field/i);
    expect(onRemoveField).not.toHaveBeenCalled();

    const confirmButton = within(dialog).getByRole("button", {
      name: /remove/i,
    });
    await userEvent.click(confirmButton);
    expect(onRemoveField).toHaveBeenCalledWith("f_email");
  });

  it("does not remove the field when confirmation is cancelled", async () => {
    const onRemoveField = jest.fn();
    render(
      <FieldPropertiesPanel
        spec={specWithText}
        selectedElementId="f_email"
        onUpdateField={noop}
        onRemoveField={onRemoveField}
      />,
    );
    await userEvent.click(screen.getByTestId("remove-field-button"));
    const dialog = await screen.findByRole("dialog");
    const cancelButton = within(dialog).getByRole("button", {
      name: /cancel/i,
    });
    await userEvent.click(cancelButton);
    expect(onRemoveField).not.toHaveBeenCalled();
  });
});
