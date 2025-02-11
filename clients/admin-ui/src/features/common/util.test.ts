import { describe, expect, it } from "@jest/globals";

import {
  createSelectedMap,
  getKeysFromMap,
  getOptionsFromMap,
  getPII,
  getWebsiteIconUrl,
} from "~/features/common/utils";

// TODO: add tests for the other utils functions

const MOCK_MAP = new Map([
  ["key1", "value1"],
  ["key2", "value2"],
]);

describe(getPII.name, () => {
  const MOCK_EMAIL = "example@example.com";
  const EXPECTED_OBFUSCATED_EMAIL = "*******************";
  it("should return the obfuscated string by default", () => {
    const result = getPII(MOCK_EMAIL);
    expect(result).toEqual(EXPECTED_OBFUSCATED_EMAIL);
  });
  it("should return the obfuscated string when set to false", () => {
    const result = getPII(MOCK_EMAIL, false);
    expect(result).toEqual(EXPECTED_OBFUSCATED_EMAIL);
  });
  it("should return the original string when set to true", () => {
    const result = getPII(MOCK_EMAIL, true);
    expect(result).toEqual(MOCK_EMAIL);
  });
});

describe(createSelectedMap.name, () => {
  it("should return a map with the selected key set to true", () => {
    const selectedKeys = ["key1"];
    const result = createSelectedMap(MOCK_MAP, selectedKeys);
    expect(result).toEqual(
      new Map([
        ["value1", true],
        ["value2", false],
      ]),
    );
  });
  it("should return a map with all keys set to false when no selected keys are provided", () => {
    const result = createSelectedMap(MOCK_MAP, undefined);
    expect(result).toEqual(
      new Map([
        ["value1", false],
        ["value2", false],
      ]),
    );
  });
});

describe(getKeysFromMap.name, () => {
  it("should return the keys that match the values", () => {
    const values = ["value1"];
    const result = getKeysFromMap(MOCK_MAP, values);
    expect(result).toEqual(["key1"]);
  });
  it("should return an empty array when no values match", () => {
    const values = ["value3"];
    const result = getKeysFromMap(MOCK_MAP, values);
    expect(result).toEqual([]);
  });
  it("should return an empty array when no values are provided", () => {
    const result = getKeysFromMap(MOCK_MAP, undefined);
    expect(result).toEqual([]);
  });
});

describe(getOptionsFromMap.name, () => {
  it("should return an array of options", () => {
    const result = getOptionsFromMap(MOCK_MAP);
    expect(result).toEqual([
      { label: "value1", value: "key1" },
      { label: "value2", value: "key2" },
    ]);
  });
  it("should return an empty array when the map is empty", () => {
    const EMPTY_MOCK_MAP = new Map();
    const result = getOptionsFromMap(EMPTY_MOCK_MAP);
    expect(result).toEqual([]);
  });
});

describe(getWebsiteIconUrl.name, () => {
  it("should return the icon URL", () => {
    const result = getWebsiteIconUrl("example.com");
    expect(result).toEqual(
      "https://cdn.brandfetch.io/example.com/icon/theme/light/fallback/404/h/24/w/24?c=1idbRjELpikqQ1PLiqb",
    );
  });
  it("should return the icon URL with a custom size", () => {
    const result = getWebsiteIconUrl("example.com", 56);
    expect(result).toEqual(
      "https://cdn.brandfetch.io/example.com/icon/theme/light/fallback/404/h/56/w/56?c=1idbRjELpikqQ1PLiqb",
    );
  });
});
