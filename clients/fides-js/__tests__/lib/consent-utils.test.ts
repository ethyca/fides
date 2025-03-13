import {
  getWindowObjFromPath,
  isPrivacyExperience,
  parseFidesDisabledNotices,
} from "../../src/lib/consent-utils";
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
