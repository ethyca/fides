import { detectDrift } from "../drift";

describe("detectDrift", () => {
  it("returns false when the rich spec maps to the saved PC shape", () => {
    const richSpec = {
      root: "form",
      elements: {
        form: { type: "Form", props: {}, children: ["f_email"] },
        f_email: {
          type: "Text",
          props: { name: "email", label: "Email", required: true },
          children: [],
        },
      },
    };
    const savedPc = {
      email: {
        label: "Email",
        field_type: "text" as const,
        required: true,
      },
    };

    expect(detectDrift(richSpec, savedPc)).toBe(false);
  });

  it("returns true when fields differ", () => {
    const richSpec = {
      root: "form",
      elements: {
        form: { type: "Form", props: {}, children: ["f_email"] },
        f_email: {
          type: "Text",
          props: { name: "email", label: "Email", required: true },
          children: [],
        },
      },
    };
    const savedPc = {
      email: {
        label: "Email",
        field_type: "text" as const,
        required: false,
      },
    };

    expect(detectDrift(richSpec, savedPc)).toBe(true);
  });
});
