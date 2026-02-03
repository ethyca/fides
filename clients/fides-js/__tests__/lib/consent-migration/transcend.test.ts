import { TranscendProvider } from "../../../src/lib/consent-migration/transcend";
import { ConsentMethod } from "../../../src/lib/consent-types";
import * as cookie from "../../../src/lib/cookie";

// Mock fidesDebugger
(globalThis as any).fidesDebugger = jest.fn();

// Mock getCookieByName
jest.mock("../../../src/lib/cookie", () => ({
  getCookieByName: jest.fn(),
}));

describe("TranscendProvider", () => {
  let provider: TranscendProvider;
  const mockGetCookieByName = cookie.getCookieByName as jest.Mock;

  beforeEach(() => {
    provider = new TranscendProvider();
    jest.clearAllMocks();
  });

  describe("basic properties", () => {
    it("has correct cookieName", () => {
      expect(provider.cookieName).toBe("tcm");
    });

    it("has correct migrationMethod", () => {
      expect(provider.migrationMethod).toBe(ConsentMethod.EXTERNAL_PROVIDER);
    });
  });

  describe("getConsentCookie", () => {
    it("calls getCookieByName with correct cookie name", () => {
      mockGetCookieByName.mockReturnValue("mock-cookie-value");

      const result = provider.getConsentCookie();

      expect(mockGetCookieByName).toHaveBeenCalledWith("tcm");
      expect(result).toBe("mock-cookie-value");
    });

    it("returns undefined when cookie does not exist", () => {
      mockGetCookieByName.mockReturnValue(undefined);

      const result = provider.getConsentCookie();

      expect(result).toBeUndefined();
    });
  });

  describe("convertToFidesConsent", () => {
    const validMapping = {
      Analytics: ["analytics_opt_out"],
      SaleOfInfo: ["data_sales"],
      Advertising: ["advertising", "marketing"],
    };

    const encodedMapping = encodeURIComponent(JSON.stringify(validMapping));

    it("returns undefined when no mapping is provided", () => {
      const cookieValue = JSON.stringify({
        purposes: { Analytics: true },
      });

      const result = provider.convertToFidesConsent(cookieValue, {});

      expect(result).toBeUndefined();
    });

    it("successfully maps boolean true consent values", () => {
      const cookieValue = JSON.stringify({
        purposes: {
          Analytics: true,
          SaleOfInfo: false,
          Advertising: true,
        },
        timestamp: "2026-01-29T00:55:33.595Z",
        confirmed: true,
      });

      const result = provider.convertToFidesConsent(cookieValue, {
        transcendFidesMapping: encodedMapping,
      });

      expect(result).toEqual({
        analytics_opt_out: true,
        data_sales: false,
        advertising: true,
        marketing: true,
      });
    });

    it("successfully maps boolean false consent values", () => {
      const cookieValue = JSON.stringify({
        purposes: {
          Analytics: false,
          SaleOfInfo: false,
          Advertising: false,
        },
      });

      const result = provider.convertToFidesConsent(cookieValue, {
        transcendFidesMapping: encodedMapping,
      });

      expect(result).toEqual({
        analytics_opt_out: false,
        data_sales: false,
        advertising: false,
        marketing: false,
      });
    });

    it('handles "Auto" string value as truthy', () => {
      const cookieValue = JSON.stringify({
        purposes: {
          NoConsentNeeded: "Auto",
        },
      });

      const mappingWithAuto = {
        NoConsentNeeded: ["essential"],
      };

      const result = provider.convertToFidesConsent(cookieValue, {
        transcendFidesMapping: encodeURIComponent(
          JSON.stringify(mappingWithAuto),
        ),
      });

      expect(result).toEqual({
        essential: true,
      });
    });

    it("handles multiple Fides keys per Transcend purpose", () => {
      const cookieValue = JSON.stringify({
        purposes: {
          Advertising: true,
        },
      });

      const result = provider.convertToFidesConsent(cookieValue, {
        transcendFidesMapping: encodedMapping,
      });

      expect(result).toEqual({
        advertising: true,
        marketing: true,
      });
    });

    it("skips purposes not in the mapping", () => {
      const cookieValue = JSON.stringify({
        purposes: {
          Analytics: true,
          UnmappedPurpose: true,
          SaleOfInfo: false,
        },
      });

      const result = provider.convertToFidesConsent(cookieValue, {
        transcendFidesMapping: encodedMapping,
      });

      expect(result).toEqual({
        analytics_opt_out: true,
        data_sales: false,
      });
      expect(result).not.toHaveProperty("UnmappedPurpose");
    });

    it("returns empty object for invalid cookie JSON", () => {
      const invalidCookieValue = "not-valid-json";

      const result = provider.convertToFidesConsent(invalidCookieValue, {
        transcendFidesMapping: encodedMapping,
      });

      expect(result).toEqual({});
    });

    it("returns empty object when purposes object is missing", () => {
      const cookieValue = JSON.stringify({
        timestamp: "2026-01-29T00:55:33.595Z",
        confirmed: true,
      });

      const result = provider.convertToFidesConsent(cookieValue, {
        transcendFidesMapping: encodedMapping,
      });

      expect(result).toEqual({});
    });

    it("returns empty object when purposes is not an object", () => {
      const cookieValue = JSON.stringify({
        purposes: "not-an-object",
      });

      const result = provider.convertToFidesConsent(cookieValue, {
        transcendFidesMapping: encodedMapping,
      });

      expect(result).toEqual({});
    });

    it("returns undefined for invalid mapping JSON", () => {
      const cookieValue = JSON.stringify({
        purposes: { Analytics: true },
      });

      const result = provider.convertToFidesConsent(cookieValue, {
        transcendFidesMapping: "invalid-json",
      });

      expect(result).toBeUndefined();
    });

    it("handles mapping with single quotes around JSON", () => {
      const mappingWithQuotes = `'${JSON.stringify(validMapping)}'`;
      const encodedMappingWithQuotes = encodeURIComponent(mappingWithQuotes);

      const cookieValue = JSON.stringify({
        purposes: {
          Analytics: true,
        },
      });

      const result = provider.convertToFidesConsent(cookieValue, {
        transcendFidesMapping: encodedMappingWithQuotes,
      });

      expect(result).toEqual({
        analytics_opt_out: true,
      });
    });

    it("does not overwrite already-set Fides keys", () => {
      const cookieValue = JSON.stringify({
        purposes: {
          Analytics: true,
        },
      });

      // This mapping has the same Fides key mapped to multiple purposes
      const duplicateMapping = {
        Analytics: ["shared_key"],
        SaleOfInfo: ["shared_key"],
      };

      const result = provider.convertToFidesConsent(cookieValue, {
        transcendFidesMapping: encodeURIComponent(
          JSON.stringify(duplicateMapping),
        ),
      });

      // Only the first occurrence should be set
      expect(result).toEqual({
        shared_key: true,
      });
    });

    it("handles real-world Transcend cookie example", () => {
      const realWorldCookie = JSON.stringify({
        purposes: {
          NoConsentNeeded: "Auto",
          SaleOfInfo: true,
          Analytics: false,
          Functional: false,
          Advertising: false,
        },
        timestamp: "2026-01-29T00:55:33.595Z",
        confirmed: true,
        prompted: true,
        updated: true,
      });

      const realWorldMapping = {
        NoConsentNeeded: ["essential"],
        SaleOfInfo: ["data_sales"],
        Analytics: ["analytics"],
        Functional: ["functional"],
        Advertising: ["advertising"],
      };

      const result = provider.convertToFidesConsent(realWorldCookie, {
        transcendFidesMapping: encodeURIComponent(
          JSON.stringify(realWorldMapping),
        ),
      });

      expect(result).toEqual({
        essential: true,
        data_sales: true,
        analytics: false,
        functional: false,
        advertising: false,
      });
    });

    it("logs debug message on successful conversion", () => {
      const cookieValue = JSON.stringify({
        purposes: { Analytics: true },
      });

      provider.convertToFidesConsent(cookieValue, {
        transcendFidesMapping: encodedMapping,
      });

      expect((globalThis as any).fidesDebugger).toHaveBeenCalledWith(
        expect.stringContaining(
          "Fides consent built based on Transcend consent",
        ),
      );
    });

    it("logs debug message on conversion failure", () => {
      const cookieValue = JSON.stringify({
        purposes: { Analytics: true },
      });

      provider.convertToFidesConsent(cookieValue, {
        transcendFidesMapping: "invalid-json",
      });

      expect((globalThis as any).fidesDebugger).toHaveBeenCalledWith(
        expect.stringContaining(
          "Failed to map Transcend consent to Fides consent",
        ),
      );
    });
  });
});
