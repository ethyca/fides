import { describe, expect, it } from "@jest/globals";

import { fold, intersection, isEmpty, isNotEmpty, unique } from "./array";

describe(unique.name, () => {
  it("should remove duplicate strings", () => {
    const refString = "refString";
    const result = unique([
      refString,
      "inlineString",
      "refString",
      "inlineString",
    ]);

    expect(result).toStrictEqual(["refString", "inlineString"]);
  });
});

describe(intersection.name, () => {
  it("should intersect string values", () => {
    const result = intersection(["left", "common"], ["common", "right"]);

    expect(result).toStrictEqual(["common"]);
  });

  it("should intersect number values", () => {
    const result = intersection([0, 10, 5], [0, 6, 8]);

    expect(result).toStrictEqual([0]);
  });

  it("should intersect objects by ref", () => {
    const refObj = { prop: "value" };
    const result = intersection([refObj], [refObj]);

    expect(result).toStrictEqual([{ prop: "value" }]);
  });

  /**
   * Revisit if this should be supported as this becomes complex
   */
  it.skip("should intersect objects by value", () => {
    const result = intersection([{ prop: "value" }], [{ prop: "value" }]);

    expect(result).toStrictEqual([{ prop: "value" }]);
  });
});

describe(fold.name, () => {
  it("add a list of number by folding", () => {
    const sum = (l: number, r: number) => l + r;
    const result = fold([1, 2, 3, 4, 5], sum);

    expect(result).toEqual(15);
  });

  it("should return undefined when empty array is provided", () => {
    const sum = (l: number, r: number) => l + r;
    const result = fold([], sum);

    expect(result).toBeUndefined();
  });

  it("should return initial value if passed array with single value", () => {
    const sum = (l: number, r: number) => l + r;
    const result = fold([5], sum);

    expect(result).toEqual(5);
  });

  it("should fold strings", () => {
    const concat =
      (d = " ") =>
      (l: string, r: string) =>
        l + d + r;
    const result = fold(["build", "a", "sentence"], concat());

    expect(result).toEqual("build a sentence");
  });
});

describe(isEmpty.name, () => {
  it("should return true when provided empty array", () => {
    const result = isEmpty([]);

    expect(result).toBeTruthy();
  });

  it("should return false when provided non-empty array", () => {
    const result = isEmpty([null]);

    expect(result).toBeFalsy();
  });
});

describe(isNotEmpty.name, () => {
  it("should return false when provided empty array", () => {
    const result = isNotEmpty([]);

    expect(result).toBeFalsy();
  });

  it("should return true when provided non-empty array", () => {
    const result = isNotEmpty([null]);

    expect(result).toBeTruthy();
  });
});
