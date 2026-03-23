import {
  addNestedField,
  getFieldsAtPath,
  removeFieldAtPath,
  updateFieldAtPath,
} from "~/features/test-datasets/dataset-field-helpers";

import { DatasetField } from "~/types/api";

const makeField = (
  name: string,
  children?: DatasetField[],
): DatasetField => ({
  name,
  ...(children ? { fields: children } : {}),
});

describe("dataset-field-helpers", () => {
  describe("updateFieldAtPath", () => {
    it("updates a top-level field", () => {
      const fields = [makeField("a"), makeField("b")];
      const result = updateFieldAtPath(fields, ["b"], {
        description: "updated",
      });
      expect(result[0]).toEqual(fields[0]);
      expect(result[1]).toEqual({ name: "b", description: "updated" });
    });

    it("updates a nested field", () => {
      const fields = [makeField("a", [makeField("b", [makeField("c")])])];
      const result = updateFieldAtPath(fields, ["a", "b", "c"], {
        description: "deep",
      });
      expect(result[0].fields![0].fields![0]).toEqual({
        name: "c",
        description: "deep",
      });
    });

    it("leaves non-matching fields untouched", () => {
      const fields = [makeField("a"), makeField("b")];
      const result = updateFieldAtPath(fields, ["a"], {
        description: "only a",
      });
      expect(result[1]).toBe(fields[1]);
    });

    it("handles missing path gracefully", () => {
      const fields = [makeField("a")];
      const result = updateFieldAtPath(fields, ["nonexistent"], {
        description: "x",
      });
      expect(result).toEqual(fields);
    });
  });

  describe("getFieldsAtPath", () => {
    it("returns children of a top-level field", () => {
      const child1 = makeField("c1");
      const child2 = makeField("c2");
      const fields = [makeField("parent", [child1, child2])];
      const result = getFieldsAtPath(fields, ["parent"]);
      expect(result).toEqual([child1, child2]);
    });

    it("returns children of a nested field", () => {
      const leaf = makeField("leaf");
      const fields = [makeField("a", [makeField("b", [leaf])])];
      const result = getFieldsAtPath(fields, ["a", "b"]);
      expect(result).toEqual([leaf]);
    });

    it("returns empty array for missing path", () => {
      const fields = [makeField("a")];
      expect(getFieldsAtPath(fields, ["missing"])).toEqual([]);
    });

    it("returns empty array for field with no children", () => {
      const fields = [makeField("a")];
      expect(getFieldsAtPath(fields, ["a"])).toEqual([]);
    });
  });

  describe("addNestedField", () => {
    it("adds a child to a top-level field", () => {
      const fields = [makeField("parent", [makeField("existing")])];
      const newField = makeField("new_child");
      const result = addNestedField(fields, ["parent"], newField);
      expect(result[0].fields).toHaveLength(2);
      expect(result[0].fields![1]).toEqual(newField);
    });

    it("adds a child to a deeply nested field", () => {
      const fields = [makeField("a", [makeField("b", [])])];
      const newField = makeField("c");
      const result = addNestedField(fields, ["a", "b"], newField);
      expect(result[0].fields![0].fields).toEqual([newField]);
    });

    it("creates fields array if parent has none", () => {
      const fields = [makeField("parent")];
      const newField = makeField("child");
      const result = addNestedField(fields, ["parent"], newField);
      expect(result[0].fields).toEqual([newField]);
    });

    it("does not modify non-matching siblings", () => {
      const sibling = makeField("sibling");
      const fields = [sibling, makeField("target", [])];
      const newField = makeField("child");
      const result = addNestedField(fields, ["target"], newField);
      expect(result[0]).toBe(sibling);
    });
  });

  describe("removeFieldAtPath", () => {
    it("removes a top-level field", () => {
      const fields = [makeField("a"), makeField("b"), makeField("c")];
      const result = removeFieldAtPath(fields, ["b"]);
      expect(result).toHaveLength(2);
      expect(result.map((f) => f.name)).toEqual(["a", "c"]);
    });

    it("removes a nested field", () => {
      const fields = [
        makeField("a", [makeField("b"), makeField("c")]),
      ];
      const result = removeFieldAtPath(fields, ["a", "b"]);
      expect(result[0].fields).toHaveLength(1);
      expect(result[0].fields![0].name).toBe("c");
    });

    it("removes a deeply nested field", () => {
      const fields = [
        makeField("a", [makeField("b", [makeField("c"), makeField("d")])]),
      ];
      const result = removeFieldAtPath(fields, ["a", "b", "c"]);
      expect(result[0].fields![0].fields).toHaveLength(1);
      expect(result[0].fields![0].fields![0].name).toBe("d");
    });

    it("returns unchanged array if field not found", () => {
      const fields = [makeField("a")];
      const result = removeFieldAtPath(fields, ["nonexistent"]);
      expect(result).toEqual(fields);
    });
  });
});
