import { getFileNameFromContentDisposition } from "~/features/common/utils";

describe("common utils", () => {
  describe(getFileNameFromContentDisposition.name, () => {
    it('should return "export" when contentDisposition is null', () => {
      expect(getFileNameFromContentDisposition(null)).toEqual("export");
    });

    it("should return the filename from the contentDisposition header", () => {
      const contentDisposition = "attachment; filename=something-special.csv";
      expect(getFileNameFromContentDisposition(contentDisposition)).toEqual(
        "something-special.csv"
      );
    });
  });
});

export default undefined;
