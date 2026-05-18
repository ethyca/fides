import { jsonSpecToPcShape } from "../jsonSpecToPcShape";
import { pcShapeToJsonSpec } from "../pcShapeToJsonSpec";

describe("pcShapeToJsonSpec", () => {
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

    const spec = pcShapeToJsonSpec(pcShape);

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
      contact_method: {
        label: "Contact method",
        field_type: "radio" as const,
        options: ["Email", "Phone"],
        required: true,
      },
    };

    const spec = pcShapeToJsonSpec(pcShape);
    const back = jsonSpecToPcShape(spec);

    expect(back.errors).toEqual([]);
    expect(back.droppedFeatures).toEqual([]);
    expect(back.pcShape.email.label).toBe("Email");
    expect(back.pcShape.reason.field_type).toBe("select");
    expect(back.pcShape.country.field_type).toBe("location");
    expect(back.pcShape.contact_method.field_type).toBe("radio");
  });

  it("uses fieldOrder when provided, interleaving identity and custom fields", () => {
    const pcShape = {
      reason: { label: "Reason", field_type: "text" as const, required: false },
      topics: {
        label: "Topics",
        field_type: "multiselect" as const,
        options: ["A", "B"],
        required: false,
      },
    };
    const identityInputs = {
      email: "required" as const,
      name: "optional" as const,
    };
    const fieldOrder = ["email", "reason", "name", "topics"];

    const spec = pcShapeToJsonSpec(pcShape, identityInputs, fieldOrder);

    expect(spec.elements.form.children).toEqual([
      "f_email",
      "f_reason",
      "f_name",
      "f_topics",
    ]);
    const back = jsonSpecToPcShape(spec);
    expect(back.fieldOrder).toEqual(["email", "reason", "name", "topics"]);
  });

  it("falls back to legacy ordering when fieldOrder is absent", () => {
    const pcShape = {
      reason: { label: "Reason", field_type: "text" as const, required: false },
    };
    const identityInputs = {
      phone: "optional" as const,
      email: "required" as const,
      name: "optional" as const,
    };

    const spec = pcShapeToJsonSpec(pcShape, identityInputs);

    // Canonical legacy order: name → email → phone → customs.
    expect(spec.elements.form.children).toEqual([
      "f_name",
      "f_email",
      "f_phone",
      "f_reason",
    ]);
  });

  it("appends configured fields missing from fieldOrder using legacy fallback", () => {
    const pcShape = {
      reason: { label: "Reason", field_type: "text" as const, required: false },
      topics: {
        label: "Topics",
        field_type: "multiselect" as const,
        options: ["A"],
        required: false,
      },
    };
    const identityInputs = { email: "required" as const };
    const fieldOrder = ["reason", "email"]; // `topics` configured but absent from order

    const spec = pcShapeToJsonSpec(pcShape, identityInputs, fieldOrder);

    expect(spec.elements.form.children).toEqual([
      "f_reason",
      "f_email",
      "f_topics",
    ]);
  });

  it("skips unknown keys in fieldOrder rather than crashing on stale data", () => {
    const pcShape = {
      reason: { label: "Reason", field_type: "text" as const, required: false },
    };
    const identityInputs = { email: "required" as const };
    const fieldOrder = ["email", "ghost_field", "reason"];

    const spec = pcShapeToJsonSpec(pcShape, identityInputs, fieldOrder);

    expect(spec.elements.form.children).toEqual(["f_email", "f_reason"]);
  });

  it("preserves arbitrary order via a synthesize → map round trip", () => {
    const pcShape = {
      reason: { label: "Reason", field_type: "text" as const, required: false },
      topics: {
        label: "Topics",
        field_type: "multiselect" as const,
        options: ["A"],
        required: false,
      },
    };
    const identityInputs = {
      email: "required" as const,
      name: "optional" as const,
      phone: "optional" as const,
    };
    const fieldOrder = ["topics", "email", "phone", "reason", "name"];

    const spec = pcShapeToJsonSpec(pcShape, identityInputs, fieldOrder);
    const back = jsonSpecToPcShape(spec);

    expect(back.fieldOrder).toEqual(fieldOrder);
  });
});
