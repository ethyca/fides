/**
 * @jest-environment jsdom
 */

import {
  evaluateCondition,
  resolveApplicableFields,
} from "~/lib/condition-evaluator";
import type {
  Condition,
  ConditionGroup,
  ConditionLeaf,
  CustomConfigField,
} from "~/types/config";

// Helper to create test field records with proper typing
const makeFields = (
  fields: Record<string, Partial<CustomConfigField> & { label: string }>,
) => fields as Record<string, CustomConfigField>;

describe("evaluateCondition", () => {
  describe("eq operator", () => {
    it("returns true when values match", () => {
      const leaf: ConditionLeaf = {
        field_address: "country",
        operator: "eq",
        value: "US",
      };
      expect(evaluateCondition(leaf, { country: "US" })).toBe(true);
    });

    it("returns false when values differ", () => {
      const leaf: ConditionLeaf = {
        field_address: "country",
        operator: "eq",
        value: "US",
      };
      expect(evaluateCondition(leaf, { country: "CA" })).toBe(false);
    });

    it("treats both null-ish as equal", () => {
      const leaf: ConditionLeaf = {
        field_address: "field",
        operator: "eq",
        value: null,
      };
      expect(evaluateCondition(leaf, { field: undefined })).toBe(true);
      expect(evaluateCondition(leaf, {})).toBe(true);
      expect(evaluateCondition(leaf, { field: "" })).toBe(true);
    });

    it("works with boolean values", () => {
      const leaf: ConditionLeaf = {
        field_address: "agreed",
        operator: "eq",
        value: true,
      };
      expect(evaluateCondition(leaf, { agreed: true })).toBe(true);
      expect(evaluateCondition(leaf, { agreed: false })).toBe(false);
    });

    it("works with number values", () => {
      const leaf: ConditionLeaf = {
        field_address: "count",
        operator: "eq",
        value: 5,
      };
      expect(evaluateCondition(leaf, { count: 5 })).toBe(true);
      expect(evaluateCondition(leaf, { count: 3 })).toBe(false);
    });
  });

  describe("neq operator", () => {
    it("returns true when values differ", () => {
      const leaf: ConditionLeaf = {
        field_address: "country",
        operator: "neq",
        value: "US",
      };
      expect(evaluateCondition(leaf, { country: "CA" })).toBe(true);
    });

    it("returns false when values match", () => {
      const leaf: ConditionLeaf = {
        field_address: "country",
        operator: "neq",
        value: "US",
      };
      expect(evaluateCondition(leaf, { country: "US" })).toBe(false);
    });

    it("treats both null-ish as equal (returns false)", () => {
      const leaf: ConditionLeaf = {
        field_address: "field",
        operator: "neq",
        value: null,
      };
      expect(evaluateCondition(leaf, {})).toBe(false);
    });
  });

  describe("exists operator", () => {
    it("returns true when field has a value", () => {
      const leaf: ConditionLeaf = {
        field_address: "name",
        operator: "exists",
      };
      expect(evaluateCondition(leaf, { name: "Alice" })).toBe(true);
    });

    it("returns false for empty string", () => {
      const leaf: ConditionLeaf = {
        field_address: "name",
        operator: "exists",
      };
      expect(evaluateCondition(leaf, { name: "" })).toBe(false);
    });

    it("returns false for null/undefined/missing", () => {
      const leaf: ConditionLeaf = {
        field_address: "name",
        operator: "exists",
      };
      expect(evaluateCondition(leaf, { name: null })).toBe(false);
      expect(evaluateCondition(leaf, { name: undefined })).toBe(false);
      expect(evaluateCondition(leaf, {})).toBe(false);
    });

    it("returns false for empty array", () => {
      const leaf: ConditionLeaf = {
        field_address: "tags",
        operator: "exists",
      };
      expect(evaluateCondition(leaf, { tags: [] })).toBe(false);
    });

    it("returns true for non-empty array", () => {
      const leaf: ConditionLeaf = {
        field_address: "tags",
        operator: "exists",
      };
      expect(evaluateCondition(leaf, { tags: ["a"] })).toBe(true);
    });

    it("returns true for boolean false (it exists)", () => {
      const leaf: ConditionLeaf = {
        field_address: "agreed",
        operator: "exists",
      };
      expect(evaluateCondition(leaf, { agreed: false })).toBe(true);
    });

    it("returns true for zero (it exists)", () => {
      const leaf: ConditionLeaf = {
        field_address: "count",
        operator: "exists",
      };
      expect(evaluateCondition(leaf, { count: 0 })).toBe(true);
    });
  });

  describe("not_exists operator", () => {
    it("returns true for missing field", () => {
      const leaf: ConditionLeaf = {
        field_address: "name",
        operator: "not_exists",
      };
      expect(evaluateCondition(leaf, {})).toBe(true);
    });

    it("returns true for empty string", () => {
      const leaf: ConditionLeaf = {
        field_address: "name",
        operator: "not_exists",
      };
      expect(evaluateCondition(leaf, { name: "" })).toBe(true);
    });

    it("returns false for present value", () => {
      const leaf: ConditionLeaf = {
        field_address: "name",
        operator: "not_exists",
      };
      expect(evaluateCondition(leaf, { name: "Alice" })).toBe(false);
    });
  });

  describe("list_contains operator", () => {
    it("returns true when data array contains expected value", () => {
      const leaf: ConditionLeaf = {
        field_address: "departments",
        operator: "list_contains",
        value: "Engineering",
      };
      expect(
        evaluateCondition(leaf, {
          departments: ["Engineering", "Marketing"],
        }),
      ).toBe(true);
    });

    it("returns false when data array does not contain expected value", () => {
      const leaf: ConditionLeaf = {
        field_address: "departments",
        operator: "list_contains",
        value: "Legal",
      };
      expect(
        evaluateCondition(leaf, {
          departments: ["Engineering", "Marketing"],
        }),
      ).toBe(false);
    });

    it("returns true when expected array contains data value", () => {
      const leaf: ConditionLeaf = {
        field_address: "country",
        operator: "list_contains",
        value: ["US", "CA", "UK"],
      };
      expect(evaluateCondition(leaf, { country: "US" })).toBe(true);
    });

    it("returns false when expected array does not contain data value", () => {
      const leaf: ConditionLeaf = {
        field_address: "country",
        operator: "list_contains",
        value: ["US", "CA", "UK"],
      };
      expect(evaluateCondition(leaf, { country: "DE" })).toBe(false);
    });

    it("returns false for non-array values", () => {
      const leaf: ConditionLeaf = {
        field_address: "name",
        operator: "list_contains",
        value: "Alice",
      };
      expect(evaluateCondition(leaf, { name: "Alice" })).toBe(false);
    });
  });

  describe("ConditionGroup - AND", () => {
    it("returns true when all conditions pass", () => {
      const group: ConditionGroup = {
        logical_operator: "and",
        conditions: [
          { field_address: "country", operator: "eq", value: "US" },
          { field_address: "state", operator: "exists" },
        ],
      };
      expect(evaluateCondition(group, { country: "US", state: "CA" })).toBe(
        true,
      );
    });

    it("returns false when any condition fails", () => {
      const group: ConditionGroup = {
        logical_operator: "and",
        conditions: [
          { field_address: "country", operator: "eq", value: "US" },
          { field_address: "state", operator: "exists" },
        ],
      };
      expect(evaluateCondition(group, { country: "US", state: "" })).toBe(
        false,
      );
    });
  });

  describe("ConditionGroup - OR", () => {
    it("returns true when any condition passes", () => {
      const group: ConditionGroup = {
        logical_operator: "or",
        conditions: [
          { field_address: "country", operator: "eq", value: "US" },
          { field_address: "country", operator: "eq", value: "CA" },
        ],
      };
      expect(evaluateCondition(group, { country: "CA" })).toBe(true);
    });

    it("returns false when all conditions fail", () => {
      const group: ConditionGroup = {
        logical_operator: "or",
        conditions: [
          { field_address: "country", operator: "eq", value: "US" },
          { field_address: "country", operator: "eq", value: "CA" },
        ],
      };
      expect(evaluateCondition(group, { country: "DE" })).toBe(false);
    });
  });

  describe("empty conditions array", () => {
    it("AND with no conditions returns true (vacuous truth)", () => {
      const group: ConditionGroup = { logical_operator: "and", conditions: [] };
      expect(evaluateCondition(group, {})).toBe(true);
    });

    it("OR with no conditions returns false", () => {
      const group: ConditionGroup = { logical_operator: "or", conditions: [] };
      expect(evaluateCondition(group, {})).toBe(false);
    });
  });

  describe("nested groups", () => {
    it("handles nested group conditions", () => {
      const condition: Condition = {
        logical_operator: "and",
        conditions: [
          { field_address: "country", operator: "eq", value: "US" },
          {
            logical_operator: "or",
            conditions: [
              { field_address: "state", operator: "eq", value: "CA" },
              { field_address: "state", operator: "eq", value: "NY" },
            ],
          },
        ],
      };
      expect(evaluateCondition(condition, { country: "US", state: "CA" })).toBe(
        true,
      );
      expect(evaluateCondition(condition, { country: "US", state: "TX" })).toBe(
        false,
      );
      expect(evaluateCondition(condition, { country: "CA", state: "CA" })).toBe(
        false,
      );
    });
  });

  it("returns false on unknown operator", () => {
    const leaf = {
      field_address: "x",
      operator: "unknown_op" as any,
      value: "y",
    };
    expect(evaluateCondition(leaf, { x: "y" })).toBe(false);
  });
});

describe("resolveApplicableFields", () => {
  it("returns an empty set when fields record is empty", () => {
    expect(resolveApplicableFields({}, {})).toEqual(new Set());
  });

  it("returns all fields when none have display_condition", () => {
    const fields = makeFields({
      name: { label: "Name" },
      email: { label: "Email" },
    });
    const result = resolveApplicableFields(fields, { name: "", email: "" });
    expect(result).toEqual(new Set(["name", "email"]));
  });

  it("hides a field when its condition is false", () => {
    const fields = makeFields({
      country: { label: "Country", field_type: "select" },
      state: {
        label: "State",
        field_type: "select",
        display_condition: {
          field_address: "country",
          operator: "eq",
          value: "US",
        },
      },
    });
    const result = resolveApplicableFields(fields, {
      country: "CA",
      state: "",
    });
    expect(result.has("country")).toBe(true);
    expect(result.has("state")).toBe(false);
  });

  it("shows a field when its condition is true", () => {
    const fields = makeFields({
      country: { label: "Country", field_type: "select" },
      state: {
        label: "State",
        field_type: "select",
        display_condition: {
          field_address: "country",
          operator: "eq",
          value: "US",
        },
      },
    });
    const result = resolveApplicableFields(fields, {
      country: "US",
      state: "CA",
    });
    expect(result.has("country")).toBe(true);
    expect(result.has("state")).toBe(true);
  });

  it("handles cascading dependencies (A → B → C)", () => {
    const fields = makeFields({
      toggle: { label: "Toggle" },
      level1: {
        label: "Level 1",
        display_condition: {
          field_address: "toggle",
          operator: "eq",
          value: "on",
        },
      },
      level2: {
        label: "Level 2",
        display_condition: {
          field_address: "level1",
          operator: "exists",
        },
      },
    });

    // toggle=on → level1 visible → level2 visible
    const allVisible = resolveApplicableFields(fields, {
      toggle: "on",
      level1: "something",
      level2: "deep",
    });
    expect(allVisible).toEqual(new Set(["toggle", "level1", "level2"]));

    // toggle=off → level1 hidden → level2 hidden (cascade)
    const cascadeHidden = resolveApplicableFields(fields, {
      toggle: "off",
      level1: "something",
      level2: "deep",
    });
    expect(cascadeHidden).toEqual(new Set(["toggle"]));
  });

  it("handles fields hidden by another hidden field", () => {
    // B depends on A, C depends on B. A is hidden → B is hidden → C is hidden.
    const fields = makeFields({
      a: {
        label: "A",
        display_condition: {
          field_address: "external",
          operator: "exists",
        },
      },
      b: {
        label: "B",
        display_condition: {
          field_address: "a",
          operator: "exists",
        },
      },
    });
    const result = resolveApplicableFields(fields, {
      external: "",
      a: "val",
      b: "val",
    });
    // external is empty → a hidden → b hidden
    expect(result.size).toBe(0);
  });

  it("converges in one pass when there are no dependencies", () => {
    const fields = makeFields({
      a: { label: "A" },
      b: {
        label: "B",
        display_condition: {
          field_address: "a",
          operator: "eq",
          value: "x",
        },
      },
    });
    // Simple case - single dependency
    const result = resolveApplicableFields(fields, { a: "x", b: "y" });
    expect(result).toEqual(new Set(["a", "b"]));
  });
});
