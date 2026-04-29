import { JSONUIProvider, Renderer } from "@json-render/react";
import { render, screen } from "@testing-library/react";

import { registry } from "../registry";

describe("registry", () => {
  it("renders Text/Select/MultiSelect/Location fields", () => {
    const spec = {
      root: "form",
      elements: {
        form: { type: "Form", props: {}, children: ["t", "s", "m", "l"] },
        t: {
          type: "Text",
          props: { name: "email", label: "Email", required: true },
          children: [],
        },
        s: {
          type: "Select",
          props: {
            name: "reason",
            label: "Reason",
            options: ["A", "B"],
            required: false,
          },
          children: [],
        },
        m: {
          type: "MultiSelect",
          props: {
            name: "topics",
            label: "Topics",
            options: ["X", "Y"],
            required: false,
          },
          children: [],
        },
        l: {
          type: "Location",
          props: { name: "country", label: "Country", required: true },
          children: [],
        },
      },
    };

    render(
      <JSONUIProvider registry={registry}>
        <Renderer spec={spec as any} registry={registry} />
      </JSONUIProvider>,
    );

    expect(screen.getByText("Email")).toBeInTheDocument();
    expect(screen.getByText("Reason")).toBeInTheDocument();
    expect(screen.getByText("Topics")).toBeInTheDocument();
    expect(screen.getByText("Country")).toBeInTheDocument();
  });
});
