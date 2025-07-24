import {
  blockPageScrolling,
  searchForElement,
  stripHtml,
  unblockPageScrolling,
} from "../../src/lib/ui-utils";

describe("ui-utils", () => {
  describe("blockPageScrolling", () => {
    it("should add 'fides-no-scroll' class to body", () => {
      document.body.classList.remove("fides-no-scroll");
      blockPageScrolling();
      expect(document.body.classList.contains("fides-no-scroll")).toBe(true);
    });
  });

  describe("unblockPageScrolling", () => {
    it("should remove 'fides-no-scroll' class from body", () => {
      document.body.classList.add("fides-no-scroll");
      unblockPageScrolling();
      expect(document.body.classList.contains("fides-no-scroll")).toBe(false);
    });
  });

  describe("stripHtml", () => {
    it("should remove HTML tags from a string", () => {
      const htmlString = "<div>Hello <b>World</b></div>";
      const result = stripHtml(htmlString);
      expect(result).toBe("Hello World");
    });

    it("should return an empty string if input is empty", () => {
      const htmlString = "";
      const result = stripHtml(htmlString);
      expect(result).toBe("");
    });

    it("should handle strings without HTML tags", () => {
      const plainString = "Hello World";
      const result = stripHtml(plainString);
      expect(result).toBe("Hello World");
    });
  });

  describe("searchForElement", () => {
    it("should resolve with the element when found", async () => {
      const elementId = "test-element";
      const element = document.createElement("div");
      element.id = elementId;
      document.body.appendChild(element);
      const result = await searchForElement(elementId);
      expect(result).toBe(element);
    });
  });
});
