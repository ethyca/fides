import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { PreviewPane } from "../PreviewPane";

const noop = () => {};

describe("PreviewPane", () => {
  it("renders empty-state and Add field button for a null spec", () => {
    render(
      <PreviewPane
        spec={null}
        onFieldClick={noop}
        onAddField={noop}
        onReorderFields={noop}
      />,
    );
    expect(screen.getByText(/no fields yet/i)).toBeInTheDocument();
    expect(screen.getByTestId("add-field-button")).toBeInTheDocument();
  });

  it("calls onFieldClick when a field is clicked", async () => {
    const onFieldClick = jest.fn();
    const spec = {
      root: "form",
      elements: {
        form: { type: "Form", props: {}, children: ["f"] },
        f: {
          type: "Text",
          props: { name: "email", label: "Email", required: true },
          children: [],
        },
      },
    };

    render(
      <PreviewPane
        spec={spec as any}
        onFieldClick={onFieldClick}
        onAddField={noop}
        onReorderFields={noop}
      />,
    );
    await userEvent.click(screen.getByText("Email"));

    expect(onFieldClick).toHaveBeenCalledWith("f");
  });

  it("renders fields unconditionally even when they have visibility conditions", () => {
    const spec = {
      root: "form",
      elements: {
        form: { type: "Form", props: {}, children: ["f_country", "f_state"] },
        f_country: {
          type: "Text",
          props: { name: "country", label: "Country", required: true },
          children: [],
        },
        f_state: {
          type: "Text",
          props: { name: "state", label: "State", required: false },
          children: [],
          visible: [{ $state: "/form/country", eq: "US" }],
        },
      },
    };

    render(
      <PreviewPane
        spec={spec as any}
        onFieldClick={noop}
        onAddField={noop}
        onReorderFields={noop}
      />,
    );
    expect(screen.getByText("Country")).toBeInTheDocument();
    expect(screen.getByText("State")).toBeInTheDocument();
  });

  it("calls onAddField with the chosen type from the dropdown", async () => {
    const onAddField = jest.fn();
    render(
      <PreviewPane
        spec={null}
        onFieldClick={noop}
        onAddField={onAddField}
        onReorderFields={noop}
      />,
    );
    await userEvent.click(screen.getByTestId("add-field-button"));
    await userEvent.click(await screen.findByText(/text input/i));
    expect(onAddField).toHaveBeenCalledWith("Text");
  });
});
