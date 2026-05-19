import { jsonSpecToPcShape } from "../jsonSpecToPcShape";

const buildSpec = (elements: Record<string, any>, children: string[]) => ({
  root: "form",
  elements: {
    form: { type: "Form", props: {}, children },
    ...elements,
  },
});

describe("jsonSpecToPcShape", () => {
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

    const result = jsonSpecToPcShape(spec);

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

    const result = jsonSpecToPcShape(spec);

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

    const result = jsonSpecToPcShape(spec);

    expect(result.errors).toContainEqual(
      expect.objectContaining({ kind: "duplicate_name", name: "email" }),
    );
  });

  it("records dropped features for `watch` and $-expressions, and for malformed `visible` entries", () => {
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
          // unsupported $state path → mapper can't translate it, so it's dropped
          visible: [{ $state: "/somewhere/else", eq: "US" }],
        },
        c: {
          type: "Text",
          props: {
            name: "computed",
            // eslint-disable-next-line no-template-curly-in-string
            label: { $template: "Hello ${/x}" },
            required: false,
          },
          children: [],
          watch: { "/form/country": { action: "loadStates" } },
        },
      },
      ["a", "b", "c"],
    );

    const result = jsonSpecToPcShape(spec);

    const kinds = result.droppedFeatures.map((d) => d.kind).sort();
    expect(kinds).toContain("visible");
    expect(kinds).toContain("watch");
    expect(kinds).toContain("expression");
  });

  it("passes `placeholder` through to the legacy shape", () => {
    const spec = buildSpec(
      {
        f1: {
          type: "Text",
          props: {
            name: "country",
            label: "Country",
            required: false,
            placeholder: "e.g. US",
          },
          children: [],
        },
        f2: {
          type: "Select",
          props: {
            name: "reason",
            label: "Reason",
            required: false,
            placeholder: "Pick one",
            options: ["A", "B"],
          },
          children: [],
        },
        f3: {
          type: "Text",
          props: { name: "notes", label: "Notes", required: false },
          children: [],
        },
      },
      ["f1", "f2", "f3"],
    );

    const result = jsonSpecToPcShape(spec);

    expect(result.errors).toEqual([]);
    expect(result.pcShape.country.placeholder).toBe("e.g. US");
    expect(result.pcShape.reason.placeholder).toBe("Pick one");
    expect(result.pcShape.notes.placeholder).toBeUndefined();
  });

  it("emits fieldOrder reflecting children order across identity and custom fields", () => {
    const spec = buildSpec(
      {
        f_email: { type: "Email", props: { required: true }, children: [] },
        f_reason: {
          type: "Text",
          props: { name: "reason", label: "Reason", required: false },
          children: [],
        },
        f_name: { type: "Name", props: { required: false }, children: [] },
        f_topics: {
          type: "MultiSelect",
          props: {
            name: "topics",
            label: "Topics",
            required: false,
            options: ["A", "B"],
          },
          children: [],
        },
      },
      ["f_email", "f_reason", "f_name", "f_topics"],
    );

    const result = jsonSpecToPcShape(spec);

    expect(result.errors).toEqual([]);
    expect(result.fieldOrder).toEqual(["email", "reason", "name", "topics"]);
    expect(result.identityInputs).toEqual({
      email: "required",
      name: "optional",
    });
    expect(Object.keys(result.pcShape)).toEqual(["reason", "topics"]);
  });

  it("returns an empty fieldOrder when the spec has no children", () => {
    const spec = buildSpec({}, []);
    const result = jsonSpecToPcShape(spec);
    expect(result.fieldOrder).toEqual([]);
  });

  it("excludes unknown components from fieldOrder while reporting them as dropped", () => {
    const spec = buildSpec(
      {
        ok: {
          type: "Text",
          props: { name: "notes", label: "Notes", required: false },
          children: [],
        },
        weird: {
          type: "Mystery",
          props: {},
          children: [],
        },
      },
      ["ok", "weird"],
    );

    const result = jsonSpecToPcShape(spec);

    expect(result.fieldOrder).toEqual(["notes"]);
    expect(result.droppedFeatures.map((d) => d.kind)).toContain(
      "unknown_component",
    );
  });

  it("translates json-render `visible` into legacy `visible_when` and does not drop it", () => {
    const spec = buildSpec(
      {
        a: {
          type: "Text",
          props: { name: "country", label: "Country", required: true },
          children: [],
        },
        b: {
          type: "Text",
          props: { name: "state", label: "State", required: false },
          children: [],
          visible: [
            { $state: "/form/country", eq: "US" },
            { $state: "/form/country", set: true },
          ],
        },
      },
      ["a", "b"],
    );

    const result = jsonSpecToPcShape(spec);

    expect(result.droppedFeatures).toEqual([]);
    expect(result.pcShape.state.visible_when).toEqual([
      { source_field: "country", operator: "eq", value: "US" },
      { source_field: "country", operator: "set" },
    ]);
  });
});
