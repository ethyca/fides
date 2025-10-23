import { describe, expect, it } from "@jest/globals";

import {
  createSelectedMap,
  getBrandIconUrl,
  getKeysFromMap,
  getOptionsFromMap,
  getPII,
  nFormatter,
  truncateUrl,
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

describe(getBrandIconUrl.name, () => {
  it("should return the icon URL", () => {
    const result = getBrandIconUrl("example.com");
    expect(result).toEqual(
      "https://cdn.brandfetch.io/example.com/icon/theme/light/fallback/404/h/24/w/24?c=1idbRjELpikqQ1PLiqb",
    );
  });
  it("should return the icon URL with a custom size", () => {
    const result = getBrandIconUrl("example.com", 56);
    expect(result).toEqual(
      "https://cdn.brandfetch.io/example.com/icon/theme/light/fallback/404/h/56/w/56?c=1idbRjELpikqQ1PLiqb",
    );
  });
});

describe(truncateUrl.name, () => {
  it("should return the URL as-is when within limit", () => {
    const result = truncateUrl("https://example.com/short", 50);
    expect(result).toEqual("example.com/short");
  });

  it("should remove protocol and www. subdomain", () => {
    const result = truncateUrl("https://www.example.com/path/to/page", 20);
    expect(result).toEqual("example.com/.../page");
  });

  it("should preserve non-www subdomains", () => {
    const result = truncateUrl("https://api.example.com/path/to/page", 20);
    expect(result).toEqual("api.example.com/.../page");
  });

  it("should truncate to domain/.../last-segment format when exceeding limit", () => {
    const result = truncateUrl(
      "https://example.com/very/long/path/to/page",
      30,
    );
    expect(result).toEqual("example.com/.../page");
  });

  it("should handle URLs without protocol", () => {
    const result = truncateUrl("example.com/path/to/page", 20);
    expect(result).toEqual("example.com/.../page");
  });

  it("should handle URLs with query strings when within limit", () => {
    const result = truncateUrl("https://example.com/search?q=test", 50);
    expect(result).toEqual("example.com/search?q=test");
  });

  it("should not guarantee staying within limit with long segments", () => {
    const result = truncateUrl(
      "https://example.com/path/very-long-segment-name-that-exceeds-limit",
      20,
    );
    expect(result).toEqual(
      "example.com/.../very-long-segment-name-that-exceeds-limit",
    );
    expect(result.length).toBeGreaterThan(20);
  });

  it("should return the original string for invalid URLs", () => {
    const consoleErrorSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});

    const invalidUrl = "not a valid url at all!!!";
    const result = truncateUrl(invalidUrl, 30);

    expect(result).toEqual(invalidUrl);
    expect(consoleErrorSpy).toHaveBeenCalled();

    consoleErrorSpy.mockRestore();
  });
});

describe(nFormatter.name, () => {
  it("should return the formatted number", () => {
    const tests = [
      { num: 0, digits: 1, result: "0" },
      { num: 12, digits: 1, result: "12" },
      { num: 1234, digits: 1, result: "1.2K" },
      { num: 1234, result: "1K" },
      { num: 100000000, digits: 1, result: "100M" },
      { num: 299792458, digits: 1, result: "299.8M" },
      { num: 759878, digits: 1, result: "759.9K" },
      { num: 759878, digits: 2, result: "759.88K" },
      { num: 759878, digits: 0, result: "760K" },
      { num: 123, digits: 1, result: "123" },
      { num: 123.456, digits: 1, result: "123.5" },
      { num: 123.456, digits: 2, result: "123.46" },
      { num: 123.456, digits: 4, result: "123.456" },
    ];
    tests.forEach((test) => {
      const result = nFormatter(test.num, test.digits);
      expect(result).toEqual(test.result);
    });
  });
});
