import * as uuid from "uuid";

import { CookieAttributes } from "typescript-cookie/dist/types";
import {
  CookieKeyConsent,
  FidesCookie,
  getOrMakeFidesCookie,
  isNewFidesCookie,
  makeConsentDefaultsLegacy,
  makeFidesCookie,
  removeCookiesFromBrowser,
  saveFidesCookie,
} from "../../src/lib/cookie";
import type { ConsentContext } from "../../src/lib/consent-context";
import { Cookies, LegacyConsentConfig } from "../../src/lib/consent-types";

// Setup mock date
const MOCK_DATE = "2023-01-01T12:00:00.000Z";
jest.useFakeTimers().setSystemTime(new Date(MOCK_DATE));

// Setup mock uuid
const MOCK_UUID = "fae7e16d-37fd-40ed-b2a8-a020ad90106d";
jest.mock("uuid");
const mockUuid = jest.mocked(uuid);
mockUuid.v4.mockReturnValue(MOCK_UUID);

// Setup mock typescript-cookie
// NOTE: the default module mocking just *doesn't* work for typescript-cookie
// for some mysterious reason (see note in jest.config.js), so we define a
// minimal mock implementation here
const mockGetCookie = jest.fn((): string | undefined => "mockGetCookie return");
const mockSetCookie = jest.fn(
  /* eslint-disable-next-line @typescript-eslint/no-unused-vars */
  (name: string, value: string, attributes: object, encoding: object) =>
    `mock setCookie return (value=${value})`
);
const mockRemoveCookie = jest.fn(
  /* eslint-disable-next-line @typescript-eslint/no-unused-vars */
  (name: string, attributes?: CookieAttributes) => undefined
);
jest.mock("typescript-cookie", () => ({
  getCookie: () => mockGetCookie(),
  setCookie: (
    name: string,
    value: string,
    attributes: object,
    encoding: object
  ) => mockSetCookie(name, value, attributes, encoding),
  removeCookie: (name: string, attributes?: CookieAttributes) =>
    mockRemoveCookie(name, attributes),
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
    });
  });

  it("accepts default consent preferences", () => {
    const defaults: CookieKeyConsent = {
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
    beforeEach(() => mockGetCookie.mockReturnValue(undefined));
    it("makes and returns a default cookie", () => {
      const cookie: FidesCookie = getOrMakeFidesCookie();
      expect(cookie.consent).toEqual({});
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
      const V090_COOKIE = JSON.stringify({
        consent: SAVED_CONSENT,
        identity: { fides_user_device_id: SAVED_UUID },
        fides_meta: {
          createdAt: CREATED_DATE,
          updatedAt: UPDATED_DATE,
          version: "0.9.0",
        },
      });
      beforeEach(() => mockGetCookie.mockReturnValue(V090_COOKIE));

      it("returns the saved cookie", () => {
        const cookie: FidesCookie = getOrMakeFidesCookie();
        expect(cookie.consent).toEqual(SAVED_CONSENT);
        expect(cookie.fides_meta.createdAt).toEqual(CREATED_DATE);
        expect(cookie.fides_meta.updatedAt).toEqual(UPDATED_DATE);
        expect(cookie.identity.fides_user_device_id).toEqual(SAVED_UUID);
      });
    });

    describe("in legacy format", () => {
      // Legacy cookie only contains the consent preferences
      const V0_COOKIE = JSON.stringify(SAVED_CONSENT);
      beforeEach(() => mockGetCookie.mockReturnValue(V0_COOKIE));

      it("returns the saved cookie and converts to new 0.9.0 format", () => {
        const cookie: FidesCookie = getOrMakeFidesCookie();
        expect(cookie.consent).toEqual(SAVED_CONSENT);
        expect(cookie.fides_meta.createdAt).toEqual(MOCK_DATE);
        expect(cookie.identity.fides_user_device_id).toEqual(MOCK_UUID);
      });
    });
  });
});

describe("saveFidesCookie", () => {
  afterEach(() => mockSetCookie.mockClear());

  it("updates the updatedAt date", () => {
    const cookie: FidesCookie = getOrMakeFidesCookie();
    expect(cookie.fides_meta.updatedAt).toEqual("");
    saveFidesCookie(cookie);
    expect(cookie.fides_meta.updatedAt).toEqual(MOCK_DATE);
  });

  it("sets a cookie on the root domain with 1 year expiry date", () => {
    const cookie: FidesCookie = getOrMakeFidesCookie();
    saveFidesCookie(cookie);
    const expectedCookieString = JSON.stringify(cookie);
    // NOTE: signature of the setCookie fn is: setCookie(name, value, attributes, encoding)
    expect(mockSetCookie.mock.calls).toHaveLength(1);
    expect(mockSetCookie.mock.calls[0][0]).toEqual("fides_consent"); // name
    expect(mockSetCookie.mock.calls[0][1]).toEqual(expectedCookieString); // value
    expect(mockSetCookie.mock.calls[0][2]).toHaveProperty(
      "domain",
      "localhost"
    ); // attributes
    expect(mockSetCookie.mock.calls[0][2]).toHaveProperty("expires", 365); // attributes
  });

  it.each([
    { url: "https://example.com", expected: "example.com" },
    { url: "https://www.another.com", expected: "another.com" },
    { url: "https://privacy.bigco.ca", expected: "bigco.ca" },
    { url: "https://privacy.subdomain.example.org", expected: "example.org" },
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
      expect(mockSetCookie.mock.calls).toHaveLength(1);
      expect(mockSetCookie.mock.calls[0][2]).toHaveProperty("domain", expected);
    }
  );

  // DEFER: known issue https://github.com/ethyca/fides/issues/2072
  it.skip.each([
    {
      url: "https://privacy.subdomain.example.co.uk",
      expected: "example.co.uk",
    },
  ])("it handles second-level domains ($url)", ({ url, expected }) => {
    const mockUrl = new URL(url);
    Object.defineProperty(window, "location", {
      value: mockUrl,
      writable: true,
    });
    const cookie: FidesCookie = getOrMakeFidesCookie();
    saveFidesCookie(cookie);
    expect(mockSetCookie.mock.calls).toHaveLength(1);
    expect(mockSetCookie.mock.calls[0][2]).toHaveProperty("domain", expected);
  });
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
        fidesDataUseKey: "improve.system",
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
    const CREATED_DATE = "2022-12-24T12:00:00.000Z";
    const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
    const SAVED_UUID = "8a46c3ee-d6c3-4518-9b6c-074528b7bfd0";
    const SAVED_CONSENT = { data_sales: false, performance: true };
    const V090_COOKIE = JSON.stringify({
      consent: SAVED_CONSENT,
      identity: { fides_user_device_id: SAVED_UUID },
      fides_meta: {
        createdAt: CREATED_DATE,
        updatedAt: UPDATED_DATE,
        version: "0.9.0",
      },
    });
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
    { cookies: [{ name: "_ga123" }], expectedAttributes: [{ path: "/" }] },
    {
      cookies: [{ name: "_ga123", path: "" }],
      expectedAttributes: [{ path: "" }],
    },
    {
      cookies: [{ name: "_ga123", path: "/subpage" }],
      expectedAttributes: [{ path: "/subpage" }],
    },
    {
      cookies: [{ name: "_ga123" }, { name: "shopify" }],
      expectedAttributes: [{ path: "/" }, { path: "/" }],
    },
  ])(
    "should remove a list of cookies",
    ({
      cookies,
      expectedAttributes,
    }: {
      cookies: Cookies[];
      expectedAttributes: CookieAttributes[];
    }) => {
      removeCookiesFromBrowser(cookies);
      expect(mockRemoveCookie.mock.calls).toHaveLength(cookies.length);
      cookies.forEach((cookie, idx) => {
        const [name, attributes] = mockRemoveCookie.mock.calls[idx];
        expect(name).toEqual(cookie.name);
        expect(attributes).toEqual(expectedAttributes[idx]);
      });
    }
  );
});
