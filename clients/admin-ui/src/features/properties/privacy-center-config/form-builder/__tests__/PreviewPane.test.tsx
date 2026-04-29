import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { PreviewPane } from "../PreviewPane";

describe("PreviewPane", () => {
  it("renders 'no fields yet' empty state for null spec", () => {
    render(<PreviewPane spec={null} onFieldClick={() => {}} />);
    expect(screen.getByText(/start by chatting/i)).toBeInTheDocument();
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

    render(<PreviewPane spec={spec as any} onFieldClick={onFieldClick} />);
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

    render(<PreviewPane spec={spec as any} onFieldClick={() => {}} />);
    expect(screen.getByText("Country")).toBeInTheDocument();
    expect(screen.getByText("State")).toBeInTheDocument();
  });
});
