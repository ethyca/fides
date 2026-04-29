import { mapSpecToPcShape } from "../mapper";
import { synthesizeSpecFromPcShape } from "../synthesize";

describe("synthesizeSpecFromPcShape", () => {
  it("creates a Form-rooted spec with one element per field", () => {
    const pcShape = {
      email: { label: "Email", field_type: "text" as const, required: true },
      reason: {
        label: "Reason",
        field_type: "select" as const,
        options: ["A", "B"],
        required: false,
      },
    };

    const spec = synthesizeSpecFromPcShape(pcShape);

    expect(spec.root).toBe("form");
    expect(spec.elements.form.type).toBe("Form");
    expect(spec.elements.form.children).toHaveLength(2);
  });

  it("round-trips: synthesize then map → original PC shape", () => {
    const pcShape = {
      email: { label: "Email", field_type: "text" as const, required: true },
      reason: {
        label: "Reason",
        field_type: "select" as const,
        options: ["A", "B"],
        required: false,
      },
      country: {
        label: "Country",
        field_type: "location" as const,
        required: true,
      },
    };

    const spec = synthesizeSpecFromPcShape(pcShape);
    const back = mapSpecToPcShape(spec);

    expect(back.errors).toEqual([]);
    expect(back.droppedFeatures).toEqual([]);
    expect(back.pcShape.email.label).toBe("Email");
    expect(back.pcShape.reason.field_type).toBe("select");
    expect(back.pcShape.country.field_type).toBe("location");
  });
});
