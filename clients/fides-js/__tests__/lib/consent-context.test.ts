import { getConsentContext } from "../../src/lib/consent-context";

// Mock fidesDebugger
(globalThis as any).fidesDebugger = jest.fn();

describe("getConsentContext", () => {
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
    it("returns true when navigator.globalPrivacyControl is true", () => {
      Object.defineProperty(window.navigator, "globalPrivacyControl", {
        value: true,
        writable: true,
        configurable: true,
      });

      const context = getConsentContext();
      expect(context.globalPrivacyControl).toBe(true);
    });

    it("returns false when navigator.globalPrivacyControl is false", () => {
      Object.defineProperty(window.navigator, "globalPrivacyControl", {
        value: false,
        writable: true,
        configurable: true,
      });

      const context = getConsentContext();
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

      const context = getConsentContext();
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

      const context = getConsentContext();
      expect(context.globalPrivacyControl).toBe(false);
    });

    it("returns undefined when GPC is not set", () => {
      const context = getConsentContext();
      expect(context.globalPrivacyControl).toBeUndefined();
    });

    it("allows GPC when TCF is enabled (for custom notices)", () => {
      (window as any).Fides.options.tcfEnabled = true;
      Object.defineProperty(window.navigator, "globalPrivacyControl", {
        value: true,
        writable: true,
        configurable: true,
      });

      const context = getConsentContext();
      expect(context.globalPrivacyControl).toBe(true);
    });

    it("allows GPC query parameter when TCF is enabled", () => {
      (window as any).Fides.options.tcfEnabled = true;
      Object.defineProperty(window, "location", {
        value: {
          href: "https://example.com?globalPrivacyControl=true",
        },
        writable: true,
        configurable: true,
      });

      const context = getConsentContext();
      expect(context.globalPrivacyControl).toBe(true);
    });
  });
});
