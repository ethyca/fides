import { encode as base64_encode } from "base-64";
import { CookieAttributes } from "js-cookie";
import * as uuid from "uuid";

import { FidesCookie } from "../../src/lib/consent-types";
import {
  getFidesConsentCookie,
  getOrMakeFidesCookie,
  saveFidesCookie,
} from "../../src/lib/cookie";

// Setup mock date
const MOCK_DATE = "2023-01-01T12:00:00.000Z";
jest.useFakeTimers().setSystemTime(new Date(MOCK_DATE));

// Setup mock uuid
const MOCK_UUID = "fae7e16d-37fd-40ed-b2a8-a020ad90106d";
jest.mock("uuid");
const mockUuid = jest.mocked(uuid);
mockUuid.v4.mockReturnValue(MOCK_UUID);

// Constant to make it clear we're using the default cookie name (no suffix)
const NO_COOKIE_SUFFIX = undefined;

const MOCK_COOKIE_WITH_TCF: FidesCookie = {
  identity: { fides_user_device_id: MOCK_UUID },
  fides_meta: {
    version: "0.9.0",
    createdAt: MOCK_DATE,
    updatedAt: MOCK_DATE,
  },
  consent: {
    data_sales: true,
    analytics: false,
    advertising: true,
  },
  // Include a realistic fides_string with TCF data
  fides_string:
    "CPzHUgAPzHUgAGXABBENCJFsAP_gAEPgAAAALuwMwAKgAYAA5AB8AIIAWABaADQAHoAQwAigBQAC2AGEAQkAjQCOAE6AP0Ag4BmgD4gJPATEAnQBV0C4ALhAXQAvABeYDJgGigOWAgmBGYCNYEcAJFAStAliBMYCgAFEQK9QV-BYOCwoLEwWLBY2Cx4LOwWfBaqC1gLdwW9Bb-C4ILrQXYBdmC7gLugu9A6AAqABgADkAHwAggBYAFoANAAegBDACKAFAALYAYQBCQCNAI4AToA_QCDgGaAPiAmIBOgCrgFwALoAXgAvMBkwDRQHLAQTAjMBGsCOAEigJVgStAmMBQCCvgK_QWABYmCxYLGQWOBZWCzALMwWbBZ0C0EFogWkAtNBagFqYLVgtbBbAFsYLZgtrBbcFwoLiAuLBccFyILlguZBc4Fz4LpAu1BdwF3gAAAA.YAAAAAAAAAAA,2~43.46.61.70.83.89.93.108.117.122.124.135.143.144.147.149.159.192.196.211.228.230.239.259.266.286.291.311.320.322.323.327.367.371.385.394.407.415.424.430.436.445.486.491.494.495.522.523.540.550.560.568.574.576.584.587.591.737.802.803.820.839.864.899.904.922.938.959.979.981.985",
  tcf_consent: {
    system_consent_preferences: {},
    system_legitimate_interests_preferences: {},
  },
};

// Setup mock js-cookie
const mockGetCookie = jest.fn();
const mockSetCookie = jest.fn();
const mockRemoveCookie = jest.fn();

jest.mock("js-cookie", () => ({
  withConverter: jest.fn(() => ({
    get: (name: string) => mockGetCookie(name),
    set: (name: string, value: string, attributes: object) =>
      mockSetCookie(name, value, attributes),
    remove: (name: string, attributes?: CookieAttributes) =>
      mockRemoveCookie(name, attributes),
  })),
}));

describe("Cookie compression", () => {
  beforeAll(() => {
    window.fidesDebugger = () => {};
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("saveFidesCookie with encoding/compression", () => {
    it("saves uncompressed JSON by default or when compression is 'none'", async () => {
      const cookie = await getOrMakeFidesCookie();
      await saveFidesCookie(cookie, { fidesCookieCompression: "none" });

      expect(mockSetCookie).toHaveBeenCalled();
      const cookieValue = mockSetCookie.mock.calls[0][1];
      // Should be valid JSON without gzip prefix
      expect(() => JSON.parse(cookieValue)).not.toThrow();
      expect(cookieValue).not.toMatch(/^gzip:/);
    });

    it("falls back to uncompressed JSON when CompressionStream is unavailable (Node/Jest)", async () => {
      await saveFidesCookie(MOCK_COOKIE_WITH_TCF, {
        fidesCookieCompression: "gzip",
      });

      expect(mockSetCookie).toHaveBeenCalled();
      const cookieValue = mockSetCookie.mock.calls[0][1];

      // In Node/Jest environment, CompressionStream is not available
      // Should fallback to uncompressed JSON without gzip: prefix
      expect(cookieValue).not.toMatch(/^gzip:/);
      expect(() => JSON.parse(cookieValue)).not.toThrow();

      // Verify the cookie data is preserved
      const parsed = JSON.parse(cookieValue);
      expect(parsed.identity.fides_user_device_id).toBe(MOCK_UUID);
      expect(parsed.fides_string).toBe(MOCK_COOKIE_WITH_TCF.fides_string);
    });

    it("respects compression setting regardless of cookie size", async () => {
      // Test with a small cookie to prove compression is not size-dependent
      const smallCookie = await getOrMakeFidesCookie();
      await saveFidesCookie(smallCookie, { fidesCookieCompression: "gzip" });

      expect(mockSetCookie).toHaveBeenCalled();
      const cookieValue = mockSetCookie.mock.calls[0][1];

      // Even with a small cookie, compression setting is respected
      // (falls back to JSON in Node/Jest since CompressionStream is unavailable)
      expect(cookieValue).not.toMatch(/^gzip:/);
      expect(() => JSON.parse(cookieValue)).not.toThrow();

      // Verify the fallback value is correct and matches the original cookie
      const parsed = JSON.parse(cookieValue);
      expect(parsed.identity.fides_user_device_id).toBe(MOCK_UUID);
      expect(parsed.consent).toEqual(smallCookie.consent);
    });

    it("sets a base64 cookie when base64Cookie option is true", async () => {
      const cookie = await getOrMakeFidesCookie();
      await saveFidesCookie(cookie, { base64Cookie: true });
      const expectedCookieString = base64_encode(JSON.stringify(cookie));
      expect(mockSetCookie).toHaveBeenCalledTimes(1);
      const [name, value, attributes] = mockSetCookie.mock.calls[0];
      expect(name).toEqual("fides_consent");
      expect(value).toEqual(expectedCookieString);
      expect(attributes).toHaveProperty("domain", "localhost");
      expect(attributes).toHaveProperty("expires", 365);
    });
  });

  describe("getFidesConsentCookie with decompression", () => {
    it("handles cookies saved with compression option (falls back in Node)", async () => {
      // Save with compression option (will fallback to JSON in Node)
      const originalCookie = await getOrMakeFidesCookie();
      await saveFidesCookie(originalCookie, {
        fidesCookieCompression: "gzip",
      });
      const savedValue = mockSetCookie.mock.calls[0][1];

      // Mock the cookie as existing
      mockGetCookie.mockReturnValue(savedValue);

      // Read back
      const retrievedCookie = await getFidesConsentCookie(NO_COOKIE_SUFFIX);

      expect(retrievedCookie).toBeDefined();
      expect(retrievedCookie?.identity.fides_user_device_id).toBe(MOCK_UUID);
      expect(retrievedCookie?.consent).toEqual(originalCookie.consent);
    });

    it("automatically decodes base-64 encoded cookies", async () => {
      const originalCookie = await getOrMakeFidesCookie();
      const base64Encoded = base64_encode(JSON.stringify(originalCookie));
      mockGetCookie.mockReturnValue(base64Encoded);

      const cookie = await getFidesConsentCookie(NO_COOKIE_SUFFIX);

      expect(cookie).toBeDefined();
      expect(cookie?.identity.fides_user_device_id).toBe(MOCK_UUID);
    });

    it("returns undefined for invalid compressed cookies", async () => {
      mockGetCookie.mockReturnValue("gzip:invalid-compressed-data");

      const cookie = await getFidesConsentCookie(NO_COOKIE_SUFFIX);

      expect(cookie).toBeUndefined();
    });

    it("returns undefined for invalid gzip-prefixed cookies", async () => {
      // Mock a cookie with gzip prefix but invalid compressed data
      mockGetCookie.mockReturnValue("gzip:invalid-base64-data!!!");

      const cookie = await getFidesConsentCookie(NO_COOKIE_SUFFIX);

      // Should return undefined since decompression will fail
      expect(cookie).toBeUndefined();
    });

    it("performs round-trip save/retrieve successfully", async () => {
      // Save with compression option
      await saveFidesCookie(MOCK_COOKIE_WITH_TCF, {
        fidesCookieCompression: "gzip",
      });
      const savedValue = mockSetCookie.mock.calls[0][1];

      // Read back the saved cookie
      mockGetCookie.mockReturnValue(savedValue);
      const retrievedCookie = await getFidesConsentCookie(NO_COOKIE_SUFFIX);

      // Verify all data is preserved (whether compressed or not)
      expect(retrievedCookie).toBeDefined();
      expect(retrievedCookie?.identity).toEqual(MOCK_COOKIE_WITH_TCF.identity);
      expect(retrievedCookie?.consent).toEqual(MOCK_COOKIE_WITH_TCF.consent);
      expect(retrievedCookie?.fides_string).toEqual(
        MOCK_COOKIE_WITH_TCF.fides_string,
      );
      expect(retrievedCookie?.tcf_consent).toEqual(
        MOCK_COOKIE_WITH_TCF.tcf_consent,
      );
    });
  });
});
