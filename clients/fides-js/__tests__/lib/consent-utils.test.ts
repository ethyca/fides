import {
  decodeNoticeConsentString,
  encodeNoticeConsentString,
  getWindowObjFromPath,
  isPrivacyExperience,
  parseFidesDisabledNotices,
} from "~/lib/consent-utils";

import mockExperienceJSON from "../__fixtures__/mock_experience.json";

describe("isPrivacyExperience", () => {
  it.each([
    { label: "undefined", obj: undefined, expected: false },
    { label: "a number", obj: 7, expected: false },
    { label: "an object", obj: { foo: "bar" }, expected: false },
    { label: "a string", obj: "foo", expected: false },
    { label: "an empty object", obj: {}, expected: true },
    {
      label: "an object with 'id'",
      obj: { id: "123456", foo: "bar" },
      expected: true,
    },
    {
      label: "a full 'experience' object",
      obj: mockExperienceJSON,
      expected: true,
    },
  ])("returns $expected when input is $label", ({ obj, expected }) => {
    expect(isPrivacyExperience(obj as any)).toBe(expected);
  });
});

describe("getWindowObjFromPath", () => {
  let windowSpy: any;

  beforeEach(() => {
    windowSpy = jest.spyOn(window, "window", "get");
  });

  afterEach(() => {
    windowSpy.mockRestore();
  });
  const windowMock1 = {
    fides_overrides: {
      hello: "something",
    },
  };
  const windowMock2 = {
    overrides: {
      fides: {
        hello: "something-else",
      },
    },
  };
  it.each([
    {
      label: "path does not exist",
      path: ["window", "nonexistent-path"],
      window: windowMock1,
      expected: undefined,
    },
    {
      label: "nested path does not exist",
      path: ["window", "nonexistent-path", "nested"],
      window: windowMock1,
      expected: undefined,
    },
    {
      label: "path is one level deep",
      path: ["window", "fides_overrides"],
      window: windowMock1,
      expected: { hello: "something" },
    },
    {
      label: "path is two levels deep",
      path: ["window", "overrides", "fides"],
      window: windowMock2,
      expected: { hello: "something-else" },
    },
  ])(
    "returns $expected when path is $path and window is $window",
    ({ path, window, expected }) => {
      windowSpy.mockImplementation(() => window);
      expect(getWindowObjFromPath(path as any)).toStrictEqual(expected);
    },
  );
});

describe("parseFidesDisabledNotices", () => {
  it.each([
    {
      label: "undefined input",
      value: undefined,
      expected: [],
    },
    {
      label: "empty string",
      value: "",
      expected: [],
    },
    {
      label: "single notice",
      value: "data_sales_and_sharing",
      expected: ["data_sales_and_sharing"],
    },
    {
      label: "multiple notices",
      value: "data_sales_and_sharing,targeted_advertising,analytics_cookies",
      expected: [
        "data_sales_and_sharing",
        "targeted_advertising",
        "analytics_cookies",
      ],
    },
    {
      label: "notices with whitespace",
      value:
        " data_sales_and_sharing , targeted_advertising , analytics_cookies ",
      expected: [
        "data_sales_and_sharing",
        "targeted_advertising",
        "analytics_cookies",
      ],
    },
    {
      label: "notices with empty values",
      value: "data_sales_and_sharing,,analytics_cookies,",
      expected: ["data_sales_and_sharing", "analytics_cookies"],
    },
  ])("returns $expected when input is $label", ({ value, expected }) => {
    expect(parseFidesDisabledNotices(value)).toStrictEqual(expected);
  });
});

describe("encodeNoticeConsentString", () => {
  it.each<{
    label: string;
    input: { [noticeKey: string]: boolean };
    expected: string;
  }>([
    {
      label: "empty object",
      input: {} as { [noticeKey: string]: boolean },
      expected: "e30=", // base64 encoded '{}'
    },
    {
      label: "single notice key",
      input: { notice1: true },
      expected: "eyJub3RpY2UxIjp0cnVlfQ==",
    },
    {
      label: "multiple notice keys",
      input: { notice1: true, notice2: false },
      expected: "eyJub3RpY2UxIjp0cnVlLCJub3RpY2UyIjpmYWxzZX0=",
    },
  ])("correctly encodes $label", ({ input, expected }) => {
    expect(encodeNoticeConsentString(input)).toBe(expected);
  });

  it("throws error when input cannot be encoded", () => {
    const circularRef: any = {};
    circularRef.self = circularRef;

    expect(() => encodeNoticeConsentString(circularRef)).toThrow(
      "Failed to encode Notice Consent string:",
    );
  });
});

describe("decodeNoticeConsentString", () => {
  it.each<{
    label: string;
    input: string;
    expected: { [noticeKey: string]: boolean };
  }>([
    {
      label: "empty string",
      input: "",
      expected: {},
    },
    {
      label: "encoded empty object",
      input: "e30=",
      expected: {},
    },
    {
      label: "single notice key",
      input: "eyJub3RpY2UxIjp0cnVlfQ==",
      expected: { notice1: true },
    },
    {
      label: "multiple notice keys",
      input: "eyJub3RpY2UxIjp0cnVlLCJub3RpY2UyIjpmYWxzZX0=",
      expected: { notice1: true, notice2: false },
    },
    {
      label: "numeric values 1 and 0",
      input: btoa(JSON.stringify({ notice1: 1, notice2: 0 })),
      expected: { notice1: true, notice2: false },
    },
    {
      label: "mixed boolean and numeric values",
      input: btoa(
        JSON.stringify({
          notice1: true,
          notice2: 0,
          notice3: 1,
          notice4: false,
        }),
      ),
      expected: {
        notice1: true,
        notice2: false,
        notice3: true,
        notice4: false,
      },
    },
  ])("correctly decodes $label", ({ input, expected }) => {
    expect(decodeNoticeConsentString(input)).toEqual(expected);
  });

  it("throws error when input is invalid base64", () => {
    expect(() => decodeNoticeConsentString("invalid-base64!")).toThrow(
      "Failed to decode Notice Consent string:",
    );
  });

  it("throws error when decoded content is invalid JSON", () => {
    const invalidBase64 = btoa("invalid json");
    expect(() => decodeNoticeConsentString(invalidBase64)).toThrow(
      "Failed to decode Notice Consent string:",
    );
  });
});
