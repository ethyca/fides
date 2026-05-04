import { rowsToVisible, visibleToRows } from "../VisibilityEditor";

describe("VisibilityEditor serialization", () => {
  describe("rowsToVisible", () => {
    it("returns undefined when no populated rows", () => {
      expect(rowsToVisible([])).toBeUndefined();
      expect(
        rowsToVisible([{ fieldName: "", operator: "eq", value: "" }]),
      ).toBeUndefined();
    });

    it("serializes an equals condition", () => {
      expect(
        rowsToVisible([{ fieldName: "country", operator: "eq", value: "US" }]),
      ).toEqual([{ $state: "/form/country", eq: "US" }]);
    });

    it("serializes is-set / is-empty without a value", () => {
      expect(
        rowsToVisible([{ fieldName: "email", operator: "set", value: "" }]),
      ).toEqual([{ $state: "/form/email", set: true }]);
      expect(
        rowsToVisible([{ fieldName: "email", operator: "empty", value: "" }]),
      ).toEqual([{ $state: "/form/email", empty: true }]);
    });

    it("emits multiple rows as an implicit AND array", () => {
      expect(
        rowsToVisible([
          { fieldName: "country", operator: "eq", value: "US" },
          { fieldName: "consent", operator: "eq", value: "yes" },
        ]),
      ).toEqual([
        { $state: "/form/country", eq: "US" },
        { $state: "/form/consent", eq: "yes" },
      ]);
    });
  });

  describe("visibleToRows", () => {
    it("returns [] for non-array input", () => {
      expect(visibleToRows(undefined)).toEqual([]);
      expect(visibleToRows({ $and: [] })).toEqual([]);
    });

    it("rehydrates an equals condition", () => {
      expect(visibleToRows([{ $state: "/form/country", eq: "US" }])).toEqual([
        { fieldName: "country", operator: "eq", value: "US" },
      ]);
    });

    it("rehydrates is-set / is-empty with empty value strings", () => {
      expect(visibleToRows([{ $state: "/form/x", set: true }])).toEqual([
        { fieldName: "x", operator: "set", value: "" },
      ]);
      expect(visibleToRows([{ $state: "/form/x", empty: true }])).toEqual([
        { fieldName: "x", operator: "empty", value: "" },
      ]);
    });

    it("strips the /form/ prefix from the state path", () => {
      expect(
        visibleToRows([{ $state: "/form/nested.field", eq: "x" }]),
      ).toEqual([{ fieldName: "nested.field", operator: "eq", value: "x" }]);
    });

    it("round-trips through rowsToVisible without loss for string conditions", () => {
      const rows = [
        { fieldName: "country", operator: "eq" as const, value: "US" },
        { fieldName: "consent", operator: "ne" as const, value: "no" },
      ];
      const round = visibleToRows(rowsToVisible(rows));
      expect(round).toEqual(rows);
    });
  });
});
