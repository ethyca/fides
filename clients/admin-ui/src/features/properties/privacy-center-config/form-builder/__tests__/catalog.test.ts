import { catalog } from "../catalog";

describe("form builder catalog", () => {
  it("defines exactly the supported component types", () => {
    expect(Object.keys(catalog.components).sort()).toEqual([
      "Form",
      "Location",
      "MultiSelect",
      "Select",
      "Text",
    ]);
  });

  it("validates a Text component's props", () => {
    const result = catalog.components.Text.props.safeParse({
      name: "email",
      label: "Email",
      required: true,
    });
    expect(result.success).toBe(true);
  });

  it("rejects a Select with no options", () => {
    const result = catalog.components.Select.props.safeParse({
      name: "reason",
      label: "Reason",
      required: true,
    });
    expect(result.success).toBe(false);
  });

  it("rejects a Text with a non-snake_case name", () => {
    const result = catalog.components.Text.props.safeParse({
      name: "First Name",
      label: "First Name",
      required: true,
    });
    expect(result.success).toBe(false);
  });
});
