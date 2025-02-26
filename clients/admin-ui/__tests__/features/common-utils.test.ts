import {
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
});

export default undefined;
