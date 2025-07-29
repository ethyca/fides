import {
  buildArrayQueryParams,
  getFileNameFromContentDisposition,
  getQueryParamsFromArray,
} from "~/features/common/utils";

describe("common utils", () => {
  describe(getFileNameFromContentDisposition.name, () => {
    it('should return "export" when contentDisposition is null', () => {
      expect(getFileNameFromContentDisposition(null)).toEqual("export");
    });

    it("should return the filename from the contentDisposition header", () => {
      const contentDisposition = "attachment; filename=something-special.csv";
      expect(getFileNameFromContentDisposition(contentDisposition)).toEqual(
        "something-special.csv",
      );
    });
  });

  describe(getQueryParamsFromArray.name, () => {
    it("should return undefined when strings is empty", () => {
      expect(getQueryParamsFromArray([], "test")).toBeUndefined();
    });
    it("should return query params from strings", () => {
      const valueList = ["a", "b", "c"];
      const queryParam = "test";
      expect(getQueryParamsFromArray(valueList, queryParam)).toEqual(
        "test=a&test=b&test=c",
      );
    });
  });

  describe(buildArrayQueryParams.name, () => {
    it("should return empty URLSearchParams when no parameters are provided", () => {
      const result = buildArrayQueryParams({});
      expect(result.toString()).toBe("");
    });

    it("should return empty URLSearchParams when all arrays are empty", () => {
      const result = buildArrayQueryParams({
        param1: [],
        param2: [],
      });
      expect(result.toString()).toBe("");
    });

    it("should return empty URLSearchParams when all arrays are undefined", () => {
      const result = buildArrayQueryParams({
        param1: undefined,
        param2: undefined,
      });
      expect(result.toString()).toBe("");
    });

    it("should build URLSearchParams for a single parameter with multiple values", () => {
      const result = buildArrayQueryParams({
        colors: ["red", "blue", "green"],
      });
      expect(result.toString()).toBe("colors=red&colors=blue&colors=green");
    });

    it("should build URLSearchParams for multiple parameters with multiple values", () => {
      const result = buildArrayQueryParams({
        colors: ["red", "blue"],
        sizes: ["small", "large"],
        categories: ["clothing"],
      });

      // Since URLSearchParams order might vary, check each parameter individually
      expect(result.getAll("colors")).toEqual(["red", "blue"]);
      expect(result.getAll("sizes")).toEqual(["small", "large"]);
      expect(result.getAll("categories")).toEqual(["clothing"]);
    });

    it("should handle mixed empty and populated arrays", () => {
      const result = buildArrayQueryParams({
        empty_param: [],
        undefined_param: undefined,
        valid_param: ["value1", "value2"],
      });

      expect(result.getAll("empty_param")).toEqual([]);
      expect(result.getAll("undefined_param")).toEqual([]);
      expect(result.getAll("valid_param")).toEqual(["value1", "value2"]);
      expect(result.toString()).toBe("valid_param=value1&valid_param=value2");
    });

    it("should handle special characters in parameter names and values", () => {
      const result = buildArrayQueryParams({
        "param with spaces": ["value with spaces", "another&value"],
        "param-with-dashes": ["value=with=equals"],
      });

      // Check that values are properly encoded
      const paramWithSpaces = result.getAll("param with spaces");
      expect(paramWithSpaces).toEqual(["value with spaces", "another&value"]);

      const paramWithDashes = result.getAll("param-with-dashes");
      expect(paramWithDashes).toEqual(["value=with=equals"]);
    });

    it("should handle single-value arrays", () => {
      const result = buildArrayQueryParams({
        single_value: ["only_one"],
      });
      expect(result.toString()).toBe("single_value=only_one");
    });
  });
});

export default undefined;
