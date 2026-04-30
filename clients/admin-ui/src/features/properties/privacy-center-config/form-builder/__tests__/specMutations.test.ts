import {
  addField,
  emptySpec,
  removeField,
  reorderFields,
  updateField,
} from "../specMutations";

describe("specMutations", () => {
  describe("addField", () => {
    it("appends a new field with auto-generated unique name", () => {
      const start = emptySpec();
      const { spec, elementId } = addField(start, "Text");

      expect(elementId).toBe("f_text_field_1");
      expect(spec.elements[elementId].type).toBe("Text");
      expect(spec.elements[elementId].props.name).toBe("text_field_1");
      expect(spec.elements.form.children).toEqual([elementId]);
    });

    it("avoids name collisions when adding the same type repeatedly", () => {
      const a = addField(emptySpec(), "Text").spec;
      const b = addField(a, "Text").spec;
      const c = addField(b, "Text").spec;

      expect(c.elements.form.children).toEqual([
        "f_text_field_1",
        "f_text_field_2",
        "f_text_field_3",
      ]);
    });

    it("seeds Select with an options array", () => {
      const { spec, elementId } = addField(emptySpec(), "Select");
      expect(spec.elements[elementId].props.options).toEqual(["Option 1"]);
    });

    it("creates an empty form when given a null spec", () => {
      const { spec } = addField(null, "Text");
      expect(spec.root).toBe("form");
      expect(spec.elements.form.type).toBe("Form");
    });
  });

  describe("updateField", () => {
    it("replaces the props of the target element", () => {
      const start = addField(emptySpec(), "Text").spec;
      const elementId = start.elements.form.children[0];
      const next = updateField(start, elementId, {
        name: "email",
        label: "Email",
        required: true,
      });
      expect(next.elements[elementId].props).toEqual({
        name: "email",
        label: "Email",
        required: true,
      });
    });

    it("returns the spec unchanged for an unknown element id", () => {
      const start = addField(emptySpec(), "Text").spec;
      const next = updateField(start, "nonexistent", { name: "x" });
      expect(next).toEqual(start);
    });
  });

  describe("removeField", () => {
    it("drops the element and its child reference", () => {
      const a = addField(emptySpec(), "Text").spec;
      const b = addField(a, "Select").spec;
      const firstId = b.elements.form.children[0];
      const next = removeField(b, firstId);
      expect(next.elements[firstId]).toBeUndefined();
      expect(next.elements.form.children).not.toContain(firstId);
      expect(next.elements.form.children).toHaveLength(1);
    });

    it("returns the spec unchanged for an unknown element id", () => {
      const start = addField(emptySpec(), "Text").spec;
      expect(removeField(start, "nope")).toEqual(start);
    });
  });

  describe("reorderFields", () => {
    it("rewrites the form's children list to the given order", () => {
      const a = addField(emptySpec(), "Text").spec;
      const b = addField(a, "Select").spec;
      const c = addField(b, "MultiSelect").spec;
      const [first, second, third] = c.elements.form.children;
      const next = reorderFields(c, [third, first, second]);
      expect(next.elements.form.children).toEqual([third, first, second]);
    });
  });
});
