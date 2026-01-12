import {
  getAutomatedConsentContext,
  getGpcContext,
} from "../../src/lib/consent-context";
import { readConsentFromAnyProvider } from "../../src/lib/consent-migration";
import { ConsentMethod, FidesInitOptions } from "../../src/lib/consent-types";
import { decodeFidesString } from "../../src/lib/fides-string";
import mockFidesInitOptions from "../__fixtures__/mock_fides_init_options.json";

// Mock dependencies
jest.mock("../../src/lib/consent-migration", () => ({
  registerDefaultProviders: jest.fn(),
  readConsentFromAnyProvider: jest
    .fn()
    .mockReturnValue({ consent: null, method: null }),
}));

jest.mock("../../src/lib/fides-string", () => ({
  decodeFidesString: jest.fn().mockReturnValue({ nc: null }),
}));

// Mock fidesDebugger
(globalThis as any).fidesDebugger = jest.fn();

describe("getGpcContext", () => {
  beforeEach(() => {
    // Reset window.Fides before each test
    (window as any).Fides = {
      options: {},
    };

    // Reset navigator.globalPrivacyControl
    Object.defineProperty(window.navigator, "globalPrivacyControl", {
      value: undefined,
      writable: true,
      configurable: true,
    });

    // Reset URL
    Object.defineProperty(window, "location", {
      value: {
        href: "https://example.com",
      },
      writable: true,
      configurable: true,
    });
  });

  describe("globalPrivacyControl", () => {
    it("returns undefined when navigator.globalPrivacyControl is not defined", () => {
      Object.defineProperty(window.navigator, "globalPrivacyControl", {
        value: undefined,
        writable: true,
        configurable: true,
      });
      const context = getGpcContext();
      expect(context.globalPrivacyControl).toBeUndefined();
    });

    it("returns true when navigator.globalPrivacyControl is true", () => {
      Object.defineProperty(window.navigator, "globalPrivacyControl", {
        value: true,
        writable: true,
        configurable: true,
      });

      const context = getGpcContext();
      expect(context.globalPrivacyControl).toBe(true);
    });

    it("returns false when navigator.globalPrivacyControl is false", () => {
      Object.defineProperty(window.navigator, "globalPrivacyControl", {
        value: false,
        writable: true,
        configurable: true,
      });

      const context = getGpcContext();
      expect(context.globalPrivacyControl).toBe(false);
    });

    it("returns true when GPC query parameter is 'true'", () => {
      Object.defineProperty(window, "location", {
        value: {
          href: "https://example.com?globalPrivacyControl=true",
        },
        writable: true,
        configurable: true,
      });

      const context = getGpcContext();
      expect(context.globalPrivacyControl).toBe(true);
    });

    it("returns false when GPC query parameter is 'false'", () => {
      Object.defineProperty(window, "location", {
        value: {
          href: "https://example.com?globalPrivacyControl=false",
        },
        writable: true,
        configurable: true,
      });

      const context = getGpcContext();
      expect(context.globalPrivacyControl).toBe(false);
    });

    it("returns undefined when GPC is not set", () => {
      const context = getGpcContext();
      expect(context.globalPrivacyControl).toBeUndefined();
    });

    it("allows GPC when TCF is enabled (for custom notices)", () => {
      (window as any).Fides.options.tcfEnabled = true;
      // Add mock custom privacy notices to enable GPC in TCF
      (window as any).Fides.experience = {
        privacy_notices: [
          {
            id: "custom-notice-1",
            notice_key: "custom_analytics",
            has_gpc_flag: true,
          },
        ],
      };
      Object.defineProperty(window.navigator, "globalPrivacyControl", {
        value: true,
        writable: true,
        configurable: true,
      });

      const context = getGpcContext();
      expect(context.globalPrivacyControl).toBe(true);
    });

    it("allows GPC query parameter when TCF is enabled", () => {
      (window as any).Fides.options.tcfEnabled = true;
      // Add mock custom privacy notices to enable GPC in TCF
      (window as any).Fides.experience = {
        privacy_notices: [
          {
            id: "custom-notice-1",
            notice_key: "custom_analytics",
            has_gpc_flag: true,
          },
        ],
      };
      Object.defineProperty(window, "location", {
        value: {
          href: "https://example.com?globalPrivacyControl=true",
        },
        writable: true,
        configurable: true,
      });

      const context = getGpcContext();
      expect(context.globalPrivacyControl).toBe(true);
    });
  });
});

describe("getAutomatedConsentContext", () => {
  const mockOptions: FidesInitOptions =
    mockFidesInitOptions as FidesInitOptions;

  beforeEach(() => {
    jest.clearAllMocks();

    // Reset window.Fides before each test
    (window as any).Fides = {
      options: {},
    };

    // Reset navigator.globalPrivacyControl
    Object.defineProperty(window.navigator, "globalPrivacyControl", {
      value: undefined,
      writable: true,
      configurable: true,
    });

    // Reset URL
    Object.defineProperty(window, "location", {
      value: {
        href: "https://example.com",
      },
      writable: true,
      configurable: true,
    });

    // Reset mocks to default behavior
    (readConsentFromAnyProvider as jest.Mock).mockReturnValue({
      consent: null,
      method: null,
    });

    (decodeFidesString as jest.Mock).mockReturnValue({ nc: null });
  });

  it("returns GPC status from navigator", () => {
    Object.defineProperty(window.navigator, "globalPrivacyControl", {
      value: true,
      writable: true,
      configurable: true,
    });

    const context = getAutomatedConsentContext(mockOptions, {});

    expect(context.globalPrivacyControl).toBe(true);
    expect(context.migratedConsent).toBeUndefined();
    expect(context.migrationMethod).toBeUndefined();
    expect(context.noticeConsentString).toBeUndefined();
  });

  it("returns migrated consent from OneTrust", () => {
    const mockMigratedConsent = {
      analytics: false,
      marketing: true,
    };

    (readConsentFromAnyProvider as jest.Mock).mockReturnValue({
      consent: mockMigratedConsent,
      method: ConsentMethod.EXTERNAL_PROVIDER,
    });

    const context = getAutomatedConsentContext(mockOptions, {});

    expect(context.migratedConsent).toEqual(mockMigratedConsent);
    expect(context.migrationMethod).toBe(ConsentMethod.EXTERNAL_PROVIDER);
  });

  it("returns notice consent string from fidesString", () => {
    const mockNoticeConsentString = "analytics:false,marketing:true";
    (decodeFidesString as jest.Mock).mockReturnValue({
      nc: mockNoticeConsentString,
    });

    const optionsWithFidesString: FidesInitOptions = {
      ...mockOptions,
      fidesString: "mock-fides-string",
    };

    const context = getAutomatedConsentContext(optionsWithFidesString, {});

    expect(context.noticeConsentString).toBe(mockNoticeConsentString);
  });

  it("returns all automated consent sources", () => {
    Object.defineProperty(window.navigator, "globalPrivacyControl", {
      value: true,
      writable: true,
      configurable: true,
    });

    const mockMigratedConsent = {
      analytics: false,
    };

    (readConsentFromAnyProvider as jest.Mock).mockReturnValue({
      consent: mockMigratedConsent,
      method: ConsentMethod.EXTERNAL_PROVIDER,
    });

    const mockNoticeConsentString = "marketing:true";
    (decodeFidesString as jest.Mock).mockReturnValue({
      nc: mockNoticeConsentString,
    });

    const optionsWithFidesString: FidesInitOptions = {
      ...mockOptions,
      fidesString: "mock-fides-string",
    };

    const context = getAutomatedConsentContext(optionsWithFidesString, {});

    expect(context.globalPrivacyControl).toBe(true);
    expect(context.migratedConsent).toEqual(mockMigratedConsent);
    expect(context.migrationMethod).toBe(ConsentMethod.EXTERNAL_PROVIDER);
    expect(context.noticeConsentString).toBe(mockNoticeConsentString);
  });

  it("returns empty context when no automated consent sources exist", () => {
    const context = getAutomatedConsentContext(mockOptions, {});

    expect(context.globalPrivacyControl).toBeUndefined();
    expect(context.migratedConsent).toBeUndefined();
    expect(context.migrationMethod).toBeUndefined();
    expect(context.noticeConsentString).toBeUndefined();
  });
});
