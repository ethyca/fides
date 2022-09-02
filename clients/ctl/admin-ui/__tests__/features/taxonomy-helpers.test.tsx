import { parentKeyFromFidesKey } from "~/features/taxonomy/helpers";

describe("taxonomy helpers", () => {
  describe("parent key from fides key", () => {
    it("should handle nested fides keys", () => {
      const fidesKey = "grandparent.parent.child";
      expect(parentKeyFromFidesKey(fidesKey)).toEqual("grandparent.parent");
    });
    it("should handle empty fides key", () => {
      const fidesKey = "";
      expect(parentKeyFromFidesKey(fidesKey)).toEqual("");
    });
    it("should handle single fides key", () => {
      const fidesKey = "root";
      expect(parentKeyFromFidesKey(fidesKey)).toEqual("");
    });
  });
});
