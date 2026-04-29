import { mapSpecToPcShape } from "../mapper";

const buildSpec = (elements: Record<string, any>, children: string[]) => ({
  root: "form",
  elements: {
    form: { type: "Form", props: {}, children },
    ...elements,
  },
});

describe("mapSpecToPcShape", () => {
  it("maps a Text field", () => {
    const spec = buildSpec(
      {
        f1: {
          type: "Text",
          props: { name: "notes", label: "Notes", required: false },
          children: [],
        },
      },
      ["f1"],
    );

    const result = mapSpecToPcShape(spec);

    expect(result.errors).toEqual([]);
    expect(result.droppedFeatures).toEqual([]);
    expect(result.pcShape).toEqual({
      notes: { label: "Notes", field_type: "text", required: false },
    });
  });

  it("maps Select / MultiSelect / Location field types", () => {
    const spec = buildSpec(
      {
        s: {
          type: "Select",
          props: {
            name: "reason",
            label: "Reason",
            required: true,
            options: ["A", "B"],
          },
          children: [],
        },
        m: {
          type: "MultiSelect",
          props: {
            name: "topics",
            label: "Topics",
            required: false,
            options: ["X", "Y"],
          },
          children: [],
        },
        l: {
          type: "Location",
          props: {
            name: "country",
            label: "Country",
            required: true,
          },
          children: [],
        },
      },
      ["s", "m", "l"],
    );

    const result = mapSpecToPcShape(spec);

    expect(result.errors).toEqual([]);
    expect(result.pcShape.reason.field_type).toBe("select");
    expect(result.pcShape.topics.field_type).toBe("multiselect");
    expect(result.pcShape.country.field_type).toBe("location");
  });

  it("flags duplicate names as a validation error", () => {
    const spec = buildSpec(
      {
        a: {
          type: "Text",
          props: { name: "email", label: "Email", required: true },
          children: [],
        },
        b: {
          type: "Text",
          props: { name: "email", label: "Email 2", required: false },
          children: [],
        },
      },
      ["a", "b"],
    );

    const result = mapSpecToPcShape(spec);

    expect(result.errors).toContainEqual(
      expect.objectContaining({ kind: "duplicate_name", name: "email" }),
    );
  });

  it("records dropped features for `visible`, `watch`, and $-expressions", () => {
    const spec = buildSpec(
      {
        a: {
          type: "Text",
          props: { name: "country", label: "Country", required: true },
          children: [],
        },
        b: {
          type: "Text",
          props: {
            name: "state",
            label: "State",
            required: false,
          },
          children: [],
          visible: [{ $state: "/form/country", eq: "US" }],
        },
        c: {
          type: "Text",
          props: {
            name: "computed",
            label: { $template: "Hello ${/x}" },
            required: false,
          },
          children: [],
          watch: { "/form/country": { action: "loadStates" } },
        },
      },
      ["a", "b", "c"],
    );

    const result = mapSpecToPcShape(spec);

    const kinds = result.droppedFeatures.map((d) => d.kind).sort();
    expect(kinds).toContain("visible");
    expect(kinds).toContain("watch");
    expect(kinds).toContain("expression");
  });
});
