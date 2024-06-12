import { describe, expect, it } from "@jest/globals";

import { getPII } from "~/features/common/utils";

// TODO: add tests for the other utils functions

describe(getPII.name, () => {
  it("should return the obfuscated string by default", () => {
    const result = getPII("example@example.com");
    expect(result).toEqual("*******************");
  });
  it("should return the obfuscated string when set to false", () => {
    const result = getPII("example@example.com", false);
    expect(result).toEqual("*******************");
  });
  it("should return the original string when set to true", () => {
    const result = getPII("example@example.com", true);
    expect(result).toEqual("example@example.com");
  });
});
