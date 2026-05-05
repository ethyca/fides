import type { JsonRenderSpec } from "../mapper";
import { mapSpecToPcShape } from "../mapper";

describe("Radio mapping (legacy PC shape)", () => {
  it("emits field_type=radio for Radio components", () => {
    const spec: JsonRenderSpec = {
      root: "form",
      elements: {
        form: { type: "Form", props: {}, children: ["f_role"] },
        f_role: {
          type: "Radio",
          props: {
            name: "user_type",
            label: "User type",
            required: true,
            options: ["Employee", "External"],
          },
          children: [],
        },
      },
    };
    const { pcShape, errors } = mapSpecToPcShape(spec);
    expect(errors).toEqual([]);
    expect(pcShape.user_type).toEqual({
      label: "User type",
      required: true,
      field_type: "radio",
      options: ["Employee", "External"],
    });
  });
});
