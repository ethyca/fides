import {
  ComponentType,
  ConsentMechanism,
  ConsentMethod,
  FidesCookie,
  NoticeConsent,
  PrivacyExperience,
} from "~/lib/consent-types";
import {
  decodeNoticeConsentString,
  encodeNoticeConsentString,
  getWindowObjFromPath,
  isPrivacyExperience,
  parseFidesDisabledNotices,
  shouldResurfaceBanner,
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

describe("shouldResurfaceBanner", () => {
  const mockExperience: PrivacyExperience = {
    id: "123",
    privacy_notices: [
      {
        notice_key: "notice1",
        name: "Test Notice",
        consent_mechanism: ConsentMechanism.OPT_OUT,
      },
    ],
    experience_config: {
      component: ComponentType.BANNER_AND_MODAL,
    },
  } as PrivacyExperience;

  const mockTCFExperience: PrivacyExperience = {
    ...mockExperience,
    experience_config: {
      component: ComponentType.TCF_OVERLAY,
    },
    meta: {
      version_hash: "v1",
    },
  } as PrivacyExperience;

  const mockCookie: FidesCookie = {
    consent: {},
    fides_meta: {
      consentMethod: ConsentMethod.ACCEPT,
    },
    tcf_version_hash: "v1",
    identity: {},
    tcf_consent: {},
  } as FidesCookie;

  const mockSavedConsent: NoticeConsent = {
    notice1: true,
  };

  it.each([
    {
      label: "returns false when banner is disabled",
      experience: mockExperience,
      cookie: mockCookie,
      savedConsent: mockSavedConsent,
      options: { fidesDisableBanner: true },
      expected: false,
    },
    {
      label: "returns false when there's no experience",
      experience: undefined,
      cookie: mockCookie,
      savedConsent: mockSavedConsent,
      options: {},
      expected: false,
    },
    {
      label: "returns true for TCF when version hash doesn't match",
      experience: { ...mockTCFExperience, meta: { version_hash: "v2" } },
      cookie: mockCookie,
      savedConsent: mockSavedConsent,
      options: {},
      expected: true,
    },
    {
      label: "returns false for TCF when version hash matches",
      experience: mockTCFExperience,
      cookie: mockCookie,
      savedConsent: mockSavedConsent,
      options: {},
      expected: false,
    },
    {
      label: "returns false for modal component",
      experience: {
        ...mockExperience,
        experience_config: { component: ComponentType.MODAL },
      },
      cookie: mockCookie,
      savedConsent: mockSavedConsent,
      options: {},
      expected: false,
    },
    {
      label: "returns false for headless component",
      experience: {
        ...mockExperience,
        experience_config: { component: ComponentType.HEADLESS },
      },
      cookie: mockCookie,
      savedConsent: mockSavedConsent,
      options: {},
      expected: false,
    },
    {
      label: "returns false when there are no notices",
      experience: { ...mockExperience, privacy_notices: [] },
      cookie: mockCookie,
      savedConsent: mockSavedConsent,
      options: {},
      expected: false,
    },
    {
      label: "returns true when there's no prior consent",
      experience: mockExperience,
      cookie: mockCookie,
      savedConsent: undefined,
      options: {},
      expected: true,
    },
    {
      label: "returns false when consent is overridden",
      experience: mockExperience,
      cookie: mockCookie,
      savedConsent: mockSavedConsent,
      options: { fidesConsentOverride: ConsentMethod.ACCEPT },
      expected: false,
    },
    {
      label: "returns true when consent method is GPC",
      experience: mockExperience,
      cookie: {
        ...mockCookie,
        fides_meta: { consentMethod: ConsentMethod.GPC },
      },
      savedConsent: mockSavedConsent,
      options: {},
      expected: true,
    },
    {
      label: "returns true when consent method is DISMISS",
      experience: mockExperience,
      cookie: {
        ...mockCookie,
        fides_meta: { consentMethod: ConsentMethod.DISMISS },
      },
      savedConsent: mockSavedConsent,
      options: {},
      expected: true,
    },
    {
      label: "returns true when notice consent is missing",
      experience: mockExperience,
      cookie: mockCookie,
      savedConsent: { notice2: true },
      options: {},
      expected: true,
    },
    {
      label: "returns false when all notices have consent",
      experience: mockExperience,
      cookie: mockCookie,
      savedConsent: { notice1: true },
      options: {},
      expected: false,
    },
  ])("$label", ({ experience, cookie, savedConsent, options, expected }) => {
    expect(
      shouldResurfaceBanner(
        experience as any,
        cookie as any,
        savedConsent as any,
        options as any,
      ),
    ).toBe(expected);
  });
});
