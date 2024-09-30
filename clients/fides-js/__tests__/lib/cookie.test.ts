import { encode as base64_encode } from "base-64";
import { CookieAttributes } from "js-cookie";
import * as uuid from "uuid";

import type { ConsentContext } from "../../src/lib/consent-context";
import {
  Cookies as CookiesType,
  FidesCookie,
  FidesJSMeta,
  LegacyConsentConfig,
  NoticeConsent,
  PrivacyExperience,
  PrivacyNoticeWithPreference,
  SaveConsentPreference,
  UserConsentPreference,
} from "../../src/lib/consent-types";
import {
  getOrMakeFidesCookie,
  isNewFidesCookie,
  makeConsentDefaultsLegacy,
  makeFidesCookie,
  removeCookiesFromBrowser,
  saveFidesCookie,
  transformTcfPreferencesToCookieKeys,
  updateCookieFromNoticePreferences,
  updateExperienceFromCookieConsentNotices,
} from "../../src/lib/cookie";
import { TcfOtherConsent, TcfSavePreferences } from "../../src/lib/tcf/types";

// Setup mock date
const MOCK_DATE = "2023-01-01T12:00:00.000Z";
jest.useFakeTimers().setSystemTime(new Date(MOCK_DATE));

// Setup mock uuid
const MOCK_UUID = "fae7e16d-37fd-40ed-b2a8-a020ad90106d";
jest.mock("uuid");
const mockUuid = jest.mocked(uuid);
mockUuid.v4.mockReturnValue(MOCK_UUID);

// Setup mock js-cookie
const mockGetCookie = jest.fn((): string | undefined => "mockGetCookie return");
const mockSetCookie = jest.fn(
  /* eslint-disable-next-line @typescript-eslint/no-unused-vars */
  (name: string, value: string, attributes: object) => {
    // Simulate that browsers will not write cookies to known top-level public domains like "com" or "co.uk"
    if (
      ["com", "ca", "org", "uk", "co.uk", "in", "co.in", "jp", "co.jp"].indexOf(
        (attributes as { domain: string }).domain,
      ) > -1
    ) {
      return undefined;
    }
    return `mock setCookie return (value=${value})`;
  },
);
const mockRemoveCookie = jest.fn(
  /* eslint-disable-next-line @typescript-eslint/no-unused-vars */
  (name: string, attributes?: CookieAttributes) => undefined,
);

jest.mock("js-cookie", () => ({
  withConverter: jest.fn(() => ({
    get: () => mockGetCookie(),
    set: (name: string, value: string, attributes: object) =>
      mockSetCookie(name, value, attributes),
    remove: (name: string, attributes?: CookieAttributes) =>
      mockRemoveCookie(name, attributes),
  })),
}));

describe("makeFidesCookie", () => {
  it("generates a v0.9.0 cookie with uuid", () => {
    const cookie: FidesCookie = makeFidesCookie();
    expect(cookie).toEqual({
      consent: {},
      fides_meta: {
        createdAt: MOCK_DATE,
        updatedAt: "",
        version: "0.9.0",
      },
      identity: {
        fides_user_device_id: MOCK_UUID,
      },
      tcf_consent: {},
    });
  });

  it("accepts default consent preferences", () => {
    const defaults: NoticeConsent = {
      essential: true,
      performance: false,
      data_sales: true,
      secrets: false,
    };
    const cookie: FidesCookie = makeFidesCookie(defaults);
    expect(cookie.consent).toEqual(defaults);
  });
});

describe("getOrMakeFidesCookie", () => {
  describe("when no saved cookie exists", () => {
    beforeEach(() => {
      mockGetCookie.mockReturnValue(undefined);
    });
    it("makes and returns a default cookie", () => {
      const cookie: FidesCookie = getOrMakeFidesCookie();
      expect(cookie.consent).toEqual({});
      expect(cookie.fides_meta.consentMethod).toEqual(undefined);
      expect(cookie.fides_meta.createdAt).toEqual(MOCK_DATE);
      expect(cookie.fides_meta.updatedAt).toEqual("");
      expect(cookie.identity.fides_user_device_id).toEqual(MOCK_UUID);
    });
  });

  describe("when a saved cookie exists", () => {
    const CREATED_DATE = "2022-12-24T12:00:00.000Z";
    const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
    const SAVED_UUID = "8a46c3ee-d6c3-4518-9b6c-074528b7bfd0";
    const SAVED_CONSENT = { data_sales: false, performance: true };

    describe("in v0.9.0 format", () => {
      const V090_COOKIE_OBJECT: FidesCookie = {
        consent: SAVED_CONSENT,
        identity: { fides_user_device_id: SAVED_UUID },
        fides_meta: {
          createdAt: CREATED_DATE,
          updatedAt: UPDATED_DATE,
          version: "0.9.0",
        },
        tcf_consent: {},
      };

      it("returns the saved cookie", () => {
        mockGetCookie.mockReturnValue(JSON.stringify(V090_COOKIE_OBJECT));
        const cookie: FidesCookie = getOrMakeFidesCookie();
        expect(cookie.consent).toEqual(SAVED_CONSENT);
        expect(cookie.fides_meta.consentMethod).toEqual(undefined);
        expect(cookie.fides_meta.createdAt).toEqual(CREATED_DATE);
        expect(cookie.fides_meta.updatedAt).toEqual(UPDATED_DATE);
        expect(cookie.identity.fides_user_device_id).toEqual(SAVED_UUID);
        expect(cookie.tcf_consent).toEqual({});
      });

      it("returns the saved cookie including optional fides_meta details like consentMethod", () => {
        // extend the cookie object with some extra details on fides_meta
        const extendedFidesMeta: FidesJSMeta = {
          ...V090_COOKIE_OBJECT.fides_meta,
          ...{ consentMethod: "accept", otherMetadata: "foo" },
        };
        const cookieObject = {
          ...V090_COOKIE_OBJECT,
          ...{ fides_meta: extendedFidesMeta },
        };
        mockGetCookie.mockReturnValue(JSON.stringify(cookieObject));
        const cookie: FidesCookie = getOrMakeFidesCookie();
        expect(cookie.consent).toEqual(SAVED_CONSENT);
        expect(cookie.fides_meta.consentMethod).toEqual("accept");
        expect(cookie.fides_meta.otherMetadata).toEqual("foo");
        expect(cookie.fides_meta.createdAt).toEqual(CREATED_DATE);
        expect(cookie.fides_meta.updatedAt).toEqual(UPDATED_DATE);
        expect(cookie.identity.fides_user_device_id).toEqual(SAVED_UUID);
        expect(cookie.tcf_consent).toEqual({});
      });
    });

    describe("in legacy format", () => {
      // Legacy cookie only contains the consent preferences
      const V0_COOKIE = JSON.stringify(SAVED_CONSENT);
      beforeEach(() => mockGetCookie.mockReturnValue(V0_COOKIE));

      it("returns the saved cookie and converts to new 0.9.0 format", () => {
        const cookie: FidesCookie = getOrMakeFidesCookie();
        expect(cookie.consent).toEqual(SAVED_CONSENT);
        expect(cookie.fides_meta.consentMethod).toEqual(undefined);
        expect(cookie.fides_meta.createdAt).toEqual(MOCK_DATE);
        expect(cookie.identity.fides_user_device_id).toEqual(MOCK_UUID);
        expect(cookie.tcf_consent).toEqual({});
      });
    });
    describe("in base64 format", () => {
      const V090_COOKIE_OBJECT: FidesCookie = {
        consent: SAVED_CONSENT,
        identity: { fides_user_device_id: SAVED_UUID },
        fides_meta: {
          createdAt: CREATED_DATE,
          updatedAt: UPDATED_DATE,
          version: "0.9.0",
        },
        tcf_consent: {},
      };
      // mock base64 cookie
      mockGetCookie.mockReturnValue(
        base64_encode(JSON.stringify(V090_COOKIE_OBJECT)),
      );

      it("returns the saved cookie and decodes from base64", () => {
        const cookie: FidesCookie = getOrMakeFidesCookie();
        expect(cookie.consent).toEqual(SAVED_CONSENT);
        expect(cookie.fides_meta.consentMethod).toEqual(undefined);
        expect(cookie.fides_meta.createdAt).toEqual(MOCK_DATE);
        expect(cookie.identity.fides_user_device_id).toEqual(MOCK_UUID);
        expect(cookie.tcf_consent).toEqual({});
      });
    });
  });
});

describe("saveFidesCookie", () => {
  beforeEach(() =>
    mockGetCookie.mockReturnValue(
      JSON.stringify({ fides_meta: { updatedAt: MOCK_DATE } }),
    ),
  );
  afterEach(() => mockSetCookie.mockClear());

  it("updates the updatedAt date", () => {
    const cookie: FidesCookie = getOrMakeFidesCookie();
    expect(cookie.fides_meta.updatedAt).toEqual("");
    saveFidesCookie(cookie, false);
    expect(cookie.fides_meta.updatedAt).toEqual(MOCK_DATE);
  });

  it("saves optional fides_meta details like consentMethod", () => {
    const cookie: FidesCookie = getOrMakeFidesCookie();
    cookie.fides_meta.consentMethod = "dismiss";
    saveFidesCookie(cookie, false);
    expect(mockSetCookie.mock.calls).toHaveLength(1);
    expect(mockSetCookie.mock.calls[0][0]).toEqual("fides_consent"); // name
    const cookieValue = mockSetCookie.mock.calls[0][1];
    const cookieParsed = JSON.parse(cookieValue);
    expect(cookieParsed.fides_meta).toHaveProperty("consentMethod");
    expect(cookieParsed.fides_meta.consentMethod).toEqual("dismiss");
  });

  it("sets a cookie on the root domain with 1 year expiry date", () => {
    const cookie: FidesCookie = getOrMakeFidesCookie();
    saveFidesCookie(cookie, false);
    const expectedCookieString = JSON.stringify(cookie);
    expect(mockSetCookie.mock.calls).toHaveLength(1);
    const [name, value, attributes] = mockSetCookie.mock.calls[0];
    expect(name).toEqual("fides_consent");
    expect(value).toEqual(expectedCookieString);
    expect(attributes).toHaveProperty("domain", "localhost");
    expect(attributes).toHaveProperty("expires", 365);
  });

  it("sets a base64 cookie", () => {
    const cookie: FidesCookie = getOrMakeFidesCookie();
    saveFidesCookie(cookie, true);
    const expectedCookieString = base64_encode(JSON.stringify(cookie));
    expect(mockSetCookie.mock.calls).toHaveLength(1);
    const [name, value, attributes] = mockSetCookie.mock.calls[0];
    expect(name).toEqual("fides_consent");
    expect(value).toEqual(expectedCookieString);
    expect(attributes).toHaveProperty("domain", "localhost");
    expect(attributes).toHaveProperty("expires", 365);
  });

  it.each([
    { url: "https://example.com", expected: "example.com" },
    { url: "https://www.another.com", expected: "another.com" },
    { url: "https://privacy.bigco.ca", expected: "bigco.ca" },
    { url: "https://privacy.subdomain.example.org", expected: "example.org" },
    {
      url: "https://privacy.subdomain.example.co.uk",
      expected: "example.co.uk",
    },
    {
      url: "https://example.co.in",
      expected: "example.co.in",
    },
    {
      url: "https://example.co.jp",
      expected: "example.co.jp",
    },
  ])(
    "calculates the root domain from the hostname ($url)",
    ({ url, expected }) => {
      const mockUrl = new URL(url);
      Object.defineProperty(window, "location", {
        value: mockUrl,
        writable: true,
      });
      const cookie: FidesCookie = getOrMakeFidesCookie();
      saveFidesCookie(cookie);
      const numCalls = expected.split(".").length;
      expect(mockSetCookie.mock.calls).toHaveLength(numCalls);
      expect(mockSetCookie.mock.calls[numCalls - 1][2]).toHaveProperty(
        "domain",
        expected,
      );
    },
  );
});

describe("makeConsentDefaultsLegacy", () => {
  const config: LegacyConsentConfig = {
    options: [
      {
        cookieKeys: ["default_undefined"],
        fidesDataUseKey: "provide.service",
      },
      {
        cookieKeys: ["default_true"],
        default: true,
        fidesDataUseKey: "functional.service.improve",
      },
      {
        cookieKeys: ["default_false"],
        default: false,
        fidesDataUseKey: "personalize.system",
      },
      {
        cookieKeys: ["default_true_with_gpc_false"],
        default: { value: true, globalPrivacyControl: false },
        fidesDataUseKey: "advertising.third_party",
      },
      {
        cookieKeys: ["default_false_with_gpc_true"],
        default: { value: false, globalPrivacyControl: true },
        fidesDataUseKey: "third_party_sharing.payment_processing",
      },
    ],
  };

  describe("when global privacy control is not present", () => {
    const context: ConsentContext = {};

    it("returns the default consent values by key", () => {
      expect(makeConsentDefaultsLegacy(config, context, false)).toEqual({
        default_true: true,
        default_false: false,
        default_true_with_gpc_false: true,
        default_false_with_gpc_true: false,
      });
    });
  });

  describe("when global privacy control is set", () => {
    const context: ConsentContext = {
      globalPrivacyControl: true,
    };

    it("returns the default consent values by key", () => {
      expect(makeConsentDefaultsLegacy(config, context, false)).toEqual({
        default_true: true,
        default_false: false,
        default_true_with_gpc_false: false,
        default_false_with_gpc_true: true,
      });
    });
  });
});

describe("isNewFidesCookie", () => {
  it("returns true for new cookies", () => {
    const newCookie: FidesCookie = getOrMakeFidesCookie();
    expect(isNewFidesCookie(newCookie)).toBeTruthy();
  });

  describe("when a saved cookie exists", () => {
    const CONSENT_METHOD = "accept";
    const CREATED_DATE = "2022-12-24T12:00:00.000Z";
    const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
    const SAVED_UUID = "8a46c3ee-d6c3-4518-9b6c-074528b7bfd0";
    const SAVED_CONSENT = { data_sales: false, performance: true };
    const V090_COOKIE_OBJECT: FidesCookie = {
      consent: SAVED_CONSENT,
      identity: { fides_user_device_id: SAVED_UUID },
      fides_meta: {
        consentMethod: CONSENT_METHOD,
        createdAt: CREATED_DATE,
        updatedAt: UPDATED_DATE,
        version: "0.9.0",
      },
      tcf_consent: {},
    };
    const V090_COOKIE = JSON.stringify(V090_COOKIE_OBJECT);
    beforeEach(() => mockGetCookie.mockReturnValue(V090_COOKIE));

    it("returns false for saved cookies", () => {
      const savedCookie: FidesCookie = getOrMakeFidesCookie();
      expect(savedCookie.fides_meta.createdAt).toEqual(CREATED_DATE);
      expect(savedCookie.fides_meta.updatedAt).toEqual(UPDATED_DATE);
      expect(isNewFidesCookie(savedCookie)).toBeFalsy();
    });
  });
});

describe("removeCookiesFromBrowser", () => {
  afterEach(() => mockRemoveCookie.mockClear());

  it.each([
    { cookies: [], expectedAttributes: [] },
    {
      cookies: [{ name: "_ga123" }],
      expectedAttributes: [
        undefined,
        { domain: ".example.co.jp" },
        { domain: undefined },
      ],
    },
    {
      cookies: [{ name: "_ga123" }, { name: "shopify" }],
      expectedAttributes: [
        undefined,
        { domain: ".example.co.jp" },
        { domain: undefined },
        undefined,
        { domain: ".example.co.jp" },
        { domain: undefined },
      ],
    },
  ])(
    "should remove a list of cookies",
    ({
      cookies,
      expectedAttributes,
    }: {
      cookies: CookiesType[];
      expectedAttributes: Array<CookieAttributes | undefined>;
    }) => {
      removeCookiesFromBrowser(cookies);
      expect(mockRemoveCookie.mock.calls).toHaveLength(cookies.length * 3);
      cookies.forEach((cookie, cookieIdx) => {
        const calls = mockRemoveCookie.mock.calls.slice(
          cookieIdx * 3,
          (cookieIdx + 1) * 3,
        );
        calls.forEach((call, callIdx) => {
          const [name, attributes] = call;
          expect(name).toEqual(cookie.name);
          expect(attributes).toEqual(expectedAttributes[callIdx]);
        });
      });
    },
  );
});

describe("transformTcfPreferencesToCookieKeys", () => {
  it("can handle empty preferences", () => {
    const preferences: TcfSavePreferences = { purpose_consent_preferences: [] };
    const expected: TcfOtherConsent = {
      system_consent_preferences: {},
      system_legitimate_interests_preferences: {},
    };
    expect(transformTcfPreferencesToCookieKeys(preferences)).toEqual(expected);
  });

  it("can transform", () => {
    const preferences: TcfSavePreferences = {
      purpose_consent_preferences: [
        { id: 1, preference: UserConsentPreference.OPT_IN },
      ],
      purpose_legitimate_interests_preferences: [
        { id: 1, preference: UserConsentPreference.OPT_OUT },
      ],
      special_feature_preferences: [
        { id: 1, preference: UserConsentPreference.OPT_IN },
        { id: 2, preference: UserConsentPreference.OPT_OUT },
      ],
      vendor_consent_preferences: [
        { id: "1111", preference: UserConsentPreference.OPT_OUT },
      ],
      vendor_legitimate_interests_preferences: [
        { id: "1111", preference: UserConsentPreference.OPT_IN },
      ],
      system_consent_preferences: [
        { id: "ctl_test_system", preference: UserConsentPreference.OPT_IN },
      ],
      system_legitimate_interests_preferences: [
        { id: "ctl_test_system", preference: UserConsentPreference.OPT_IN },
      ],
    };
    const expected: TcfOtherConsent = {
      system_consent_preferences: { ctl_test_system: true },
      system_legitimate_interests_preferences: { ctl_test_system: true },
    };
    expect(transformTcfPreferencesToCookieKeys(preferences)).toEqual(expected);
  });
});

describe("updateExperienceFromCookieConsent", () => {
  const baseCookie = makeFidesCookie();

  // Notice test data
  const notices = [
    { notice_key: "one" },
    { notice_key: "two" },
    { notice_key: "three" },
  ] as PrivacyExperience["privacy_notices"];
  const experienceWithNotices = {
    privacy_notices: notices,
  } as PrivacyExperience;

  describe("notices", () => {
    it("can handle an empty cookie", () => {
      const cookie = { ...baseCookie, consent: {} };
      const updatedExperience = updateExperienceFromCookieConsentNotices({
        experience: experienceWithNotices,
        cookie,
      });
      expect(updatedExperience.privacy_notices).toEqual([
        { notice_key: "one", current_preference: undefined },
        { notice_key: "two", current_preference: undefined },
        { notice_key: "three", current_preference: undefined },
      ]);
    });

    it("can handle updating preferences", () => {
      const cookie = { ...baseCookie, consent: { one: true, two: false } };
      const updatedExperience = updateExperienceFromCookieConsentNotices({
        experience: experienceWithNotices,
        cookie,
      });
      expect(updatedExperience.privacy_notices).toEqual([
        { notice_key: "one", current_preference: UserConsentPreference.OPT_IN },
        {
          notice_key: "two",
          current_preference: UserConsentPreference.OPT_OUT,
        },
        { notice_key: "three", current_preference: undefined },
      ]);
    });

    it("can handle when cookie has values not in the experience", () => {
      const cookie = {
        ...baseCookie,
        consent: { one: true, two: false, fake: true },
      };
      const updatedExperience = updateExperienceFromCookieConsentNotices({
        experience: experienceWithNotices,
        cookie,
      });
      expect(updatedExperience.privacy_notices).toEqual([
        { notice_key: "one", current_preference: UserConsentPreference.OPT_IN },
        {
          notice_key: "two",
          current_preference: UserConsentPreference.OPT_OUT,
        },
        { notice_key: "three", current_preference: undefined },
      ]);
    });
  });
});

describe("updateCookieFromNoticePreferences", () => {
  it("can receive an updated cookie obj based on notice preferences", async () => {
    const cookie = makeFidesCookie();
    const notices = [
      { notice_key: "one", current_preference: UserConsentPreference.OPT_IN },
      { notice_key: "two", current_preference: UserConsentPreference.OPT_OUT },
    ] as PrivacyNoticeWithPreference[];
    const preferences = notices.map(
      (n) =>
        new SaveConsentPreference(
          n,
          n.current_preference ?? UserConsentPreference.OPT_OUT,
          `pri_notice-history-mock-${n.notice_key}`,
        ),
    );
    const updatedCookie = await updateCookieFromNoticePreferences(
      cookie,
      preferences,
    );
    expect(updatedCookie.consent).toEqual({ one: true, two: false });
  });
});
