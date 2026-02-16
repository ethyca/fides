import { TCString } from "@iabtechlabtcf/core";

import { SourcePointProvider } from "../../../src/lib/consent-migration/sourcepoint";
import { ConsentMethod } from "../../../src/lib/consent-types";
import * as cookie from "../../../src/lib/cookie";

(globalThis as any).fidesDebugger = jest.fn();

jest.mock("../../../src/lib/cookie", () => ({
  getCookieByName: jest.fn(),
}));

jest.mock("@iabtechlabtcf/core", () => {
  const actual = jest.requireActual("@iabtechlabtcf/core");
  return {
    ...actual,
    TCString: {
      ...actual.TCString,
      decode: jest.fn(),
    },
  };
});

describe("SourcePointProvider", () => {
  let provider: SourcePointProvider;
  const mockGetCookieByName = cookie.getCookieByName as jest.Mock;
  const mockTCStringDecode = TCString.decode as jest.Mock;

  const createDecodedModel = (opts: {
    purposeConsents?: number[];
    purposeLegitimateInterests?: number[];
  }) => {
    const purposeConsents = new Set(opts.purposeConsents ?? []);
    const purposeLegitimateInterests = new Set(
      opts.purposeLegitimateInterests ?? [],
    );
    return { purposeConsents, purposeLegitimateInterests };
  };

  beforeEach(() => {
    provider = new SourcePointProvider();
    jest.clearAllMocks();
  });

  describe("basic properties", () => {
    it("has correct cookieName", () => {
      expect(provider.cookieName).toBe("euconsent");
    });

    it("has correct migrationMethod", () => {
      expect(provider.migrationMethod).toBe(ConsentMethod.EXTERNAL_PROVIDER);
    });
  });

  describe("getConsentCookie", () => {
    it("calls getCookieByName with euconsent", () => {
      mockGetCookieByName.mockReturnValue("COxABCENOxABCENA");

      const result = provider.getConsentCookie();

      expect(mockGetCookieByName).toHaveBeenCalledWith("euconsent");
      expect(result).toBe("COxABCENOxABCENA");
    });

    it("returns undefined when cookie does not exist", () => {
      mockGetCookieByName.mockReturnValue(undefined);

      const result = provider.getConsentCookie();

      expect(result).toBeUndefined();
    });
  });

  describe("convertToFidesConsent", () => {
    const validMapping = {
      1: ["essential"],
      2: ["analytics_opt_out"],
      3: ["advertising", "marketing"],
    };
    const encodedMapping = encodeURIComponent(JSON.stringify(validMapping));

    it("returns undefined when no mapping is provided", () => {
      mockTCStringDecode.mockReturnValue(
        createDecodedModel({ purposeConsents: [1, 2] }),
      );

      const result = provider.convertToFidesConsent("COxABCENOxABCENA", {});

      expect(result).toBeUndefined();
    });

    it("successfully maps purpose consent to Fides keys", () => {
      mockTCStringDecode.mockReturnValue(
        createDecodedModel({
          purposeConsents: [1, 2],
          purposeLegitimateInterests: [],
        }),
      );

      const result = provider.convertToFidesConsent("COxABCENOxABCENA", {
        sourcepointFidesMapping: encodedMapping,
      });

      expect(result).toEqual({
        essential: true,
        analytics_opt_out: true,
        advertising: false,
        marketing: false,
      });
    });

    it("successfully maps purpose legitimate interest to Fides keys", () => {
      mockTCStringDecode.mockReturnValue(
        createDecodedModel({
          purposeConsents: [],
          purposeLegitimateInterests: [3],
        }),
      );

      const result = provider.convertToFidesConsent("COxABCENOxABCENA", {
        sourcepointFidesMapping: encodedMapping,
      });

      expect(result).toEqual({
        essential: false,
        analytics_opt_out: false,
        advertising: true,
        marketing: true,
      });
    });

    it("treats consent OR legitimate interest as consented", () => {
      mockTCStringDecode.mockReturnValue(
        createDecodedModel({
          purposeConsents: [1],
          purposeLegitimateInterests: [2],
        }),
      );

      const result = provider.convertToFidesConsent("COxABCENOxABCENA", {
        sourcepointFidesMapping: encodedMapping,
      });

      expect(result).toEqual({
        essential: true,
        analytics_opt_out: true,
        advertising: false,
        marketing: false,
      });
    });

    it("returns empty object when no purposes are consented", () => {
      mockTCStringDecode.mockReturnValue(
        createDecodedModel({
          purposeConsents: [],
          purposeLegitimateInterests: [],
        }),
      );

      const result = provider.convertToFidesConsent("COxABCENOxABCENA", {
        sourcepointFidesMapping: encodedMapping,
      });

      expect(result).toEqual({
        essential: false,
        analytics_opt_out: false,
        advertising: false,
        marketing: false,
      });
    });

    it("ignores purpose IDs not in mapping", () => {
      mockTCStringDecode.mockReturnValue(
        createDecodedModel({
          purposeConsents: [1, 99],
          purposeLegitimateInterests: [],
        }),
      );

      const result = provider.convertToFidesConsent("COxABCENOxABCENA", {
        sourcepointFidesMapping: encodedMapping,
      });

      expect(result).toEqual({
        essential: true,
        analytics_opt_out: false,
        advertising: false,
        marketing: false,
      });
    });

    it("returns empty object and does not throw when TC string is invalid", () => {
      mockTCStringDecode.mockImplementation(() => {
        throw new Error("invalid tc string");
      });

      const result = provider.convertToFidesConsent("invalid", {
        sourcepointFidesMapping: encodedMapping,
      });

      expect(result).toEqual({});
    });

    it("returns undefined for invalid mapping JSON", () => {
      mockTCStringDecode.mockReturnValue(
        createDecodedModel({ purposeConsents: [1] }),
      );

      const result = provider.convertToFidesConsent("COxABCENOxABCENA", {
        sourcepointFidesMapping: "invalid-json",
      });

      expect(result).toBeUndefined();
    });

    it("handles mapping with single quotes around JSON", () => {
      const mappingWithQuotes = `'${JSON.stringify(validMapping)}'`;
      const encodedMappingWithQuotes = encodeURIComponent(mappingWithQuotes);
      mockTCStringDecode.mockReturnValue(
        createDecodedModel({ purposeConsents: [1] }),
      );

      const result = provider.convertToFidesConsent("COxABCENOxABCENA", {
        sourcepointFidesMapping: encodedMappingWithQuotes,
      });

      expect(result).toEqual({
        essential: true,
        analytics_opt_out: false,
        advertising: false,
        marketing: false,
      });
    });

    it("does not overwrite already-set Fides keys", () => {
      mockTCStringDecode.mockReturnValue(
        createDecodedModel({ purposeConsents: [1, 2] }),
      );
      const duplicateMapping = {
        1: ["shared_key"],
        2: ["shared_key"],
      };

      const result = provider.convertToFidesConsent("COxABCENOxABCENA", {
        sourcepointFidesMapping: encodeURIComponent(
          JSON.stringify(duplicateMapping),
        ),
      });

      expect(result).toEqual({
        shared_key: true,
      });
    });

    it("logs debug message on successful conversion", () => {
      mockTCStringDecode.mockReturnValue(
        createDecodedModel({ purposeConsents: [1] }),
      );

      provider.convertToFidesConsent("COxABCENOxABCENA", {
        sourcepointFidesMapping: encodedMapping,
      });

      expect((globalThis as any).fidesDebugger).toHaveBeenCalledWith(
        expect.stringContaining(
          "Fides consent built based on SourcePoint (TCF) consent",
        ),
      );
    });

    it("logs debug message on conversion failure", () => {
      provider.convertToFidesConsent("COxABCENOxABCENA", {
        sourcepointFidesMapping: "invalid-json",
      });

      expect((globalThis as any).fidesDebugger).toHaveBeenCalledWith(
        expect.stringContaining(
          "Failed to map SourcePoint consent to Fides consent",
        ),
      );
    });
  });
});
