import { FidesGlobal } from "../../src/fides";
import { gcm } from "../../src/integrations/gcm";

// Mock fidesDebugger global
/* eslint-disable */
// @ts-ignore
globalThis.fidesDebugger = jest.fn();
/* eslint-enable */

/**
 * Mock gtag function
 */
const setupGtag = () => {
  const mockGtag = jest.fn();
  window.gtag = mockGtag;
  return mockGtag;
};

/**
 * Setup Fides with consent
 */
const setupFidesWithConsent = (consent: Record<string, boolean>) => {
  window.Fides = {
    consent,
    initialized: true,
  } as any as FidesGlobal;
};

/**
 * Trigger a Fides consent event
 */
const triggerConsentEvent = (
  eventName: string,
  consent: Record<string, boolean>,
) => {
  window.dispatchEvent(
    new CustomEvent(eventName, {
      detail: { consent },
    }),
  );
};

describe("gcm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    window.gtag = undefined;
    window.Fides = undefined as any;
  });

  describe("Default purpose mapping", () => {
    test("pushes consent to gtag with default mapping", () => {
      const mockGtag = setupGtag();
      setupFidesWithConsent({
        analytics: true,
        advertising: false,
        functional: true,
      });

      gcm();
      triggerConsentEvent("FidesUpdated", {
        analytics: true,
        advertising: false,
        functional: true,
      });

      expect(mockGtag).toHaveBeenCalledWith("consent", "update", {
        analytics_storage: "granted",
        ad_storage: "denied",
        ad_personalization: "denied",
        ad_user_data: "denied",
        functionality_storage: "granted",
        personalization_storage: "granted",
      });
    });

    test("includes data_sales_and_sharing in default mapping", () => {
      const mockGtag = setupGtag();
      setupFidesWithConsent({
        data_sales_and_sharing: true,
      });

      gcm();
      triggerConsentEvent("FidesUpdated", {
        data_sales_and_sharing: true,
      });

      expect(mockGtag).toHaveBeenCalledWith("consent", "update", {
        ad_storage: "granted",
        ad_personalization: "granted",
        ad_user_data: "granted",
      });
    });

    test("includes marketing in default mapping", () => {
      const mockGtag = setupGtag();
      setupFidesWithConsent({
        marketing: true,
      });

      gcm();
      triggerConsentEvent("FidesUpdated", {
        marketing: true,
      });

      expect(mockGtag).toHaveBeenCalledWith("consent", "update", {
        ad_storage: "granted",
        ad_personalization: "granted",
        ad_user_data: "granted",
      });
    });

    test("sets all consent types to denied when consent is false", () => {
      const mockGtag = setupGtag();
      setupFidesWithConsent({
        analytics: false,
        advertising: false,
        functional: false,
        data_sales_and_sharing: false,
        marketing: false,
      });

      gcm();
      triggerConsentEvent("FidesUpdated", {
        analytics: false,
        advertising: false,
        functional: false,
        data_sales_and_sharing: false,
        marketing: false,
      });

      expect(mockGtag).toHaveBeenCalledWith("consent", "update", {
        analytics_storage: "denied",
        ad_storage: "denied",
        ad_personalization: "denied",
        ad_user_data: "denied",
        functionality_storage: "denied",
        personalization_storage: "denied",
      });
    });
  });

  describe("Custom purpose mapping", () => {
    test("pushes consent with custom mapping", () => {
      const mockGtag = setupGtag();
      setupFidesWithConsent({
        performance: true,
        targeting: false,
      });

      gcm({
        purposeMapping: {
          performance: ["analytics_storage"],
          targeting: ["ad_storage", "ad_personalization"],
        },
      });

      triggerConsentEvent("FidesUpdated", {
        performance: true,
        targeting: false,
      });

      expect(mockGtag).toHaveBeenCalledWith("consent", "update", {
        analytics_storage: "granted",
        ad_storage: "denied",
        ad_personalization: "denied",
      });
    });

    test("handles single consent key mapping to multiple Google types", () => {
      const mockGtag = setupGtag();
      setupFidesWithConsent({
        all_advertising: true,
      });

      gcm({
        purposeMapping: {
          all_advertising: ["ad_storage", "ad_personalization", "ad_user_data"],
        },
      });

      triggerConsentEvent("FidesUpdated", {
        all_advertising: true,
      });

      expect(mockGtag).toHaveBeenCalledWith("consent", "update", {
        ad_storage: "granted",
        ad_personalization: "granted",
        ad_user_data: "granted",
      });
    });

    test("handles multiple consent keys mapping to same Google type", () => {
      const mockGtag = setupGtag();
      setupFidesWithConsent({
        analytics: false,
        performance: true,
      });

      // Both map to analytics_storage, last write wins (performance=true)
      gcm({
        purposeMapping: {
          analytics: ["analytics_storage"],
          performance: ["analytics_storage"],
        },
      });

      triggerConsentEvent("FidesUpdated", {
        analytics: false,
        performance: true,
      });

      // Last key processed wins, should be "granted" from performance
      expect(mockGtag).toHaveBeenCalledWith("consent", "update", {
        analytics_storage: "granted",
      });
    });
  });

  describe("Graceful degradation with missing consent keys", () => {
    test("only processes consent keys that exist in Fides consent", () => {
      const mockGtag = setupGtag();
      setupFidesWithConsent({
        analytics: true,
        // functional is missing - should be skipped
      });

      gcm({
        purposeMapping: {
          analytics: ["analytics_storage"],
          functional: ["functionality_storage", "personalization_storage"],
          advertising: ["ad_storage"],
        },
      });

      triggerConsentEvent("FidesUpdated", {
        analytics: true,
      });

      // Should only include analytics_storage (functional and advertising are missing)
      expect(mockGtag).toHaveBeenCalledWith("consent", "update", {
        analytics_storage: "granted",
      });
    });

    test("works when only subset of default mapping keys are present", () => {
      const mockGtag = setupGtag();
      setupFidesWithConsent({
        analytics: true,
        // advertising, functional, data_sales_and_sharing, marketing are missing
      });

      gcm(); // Use default mapping

      triggerConsentEvent("FidesUpdated", {
        analytics: true,
      });

      // Should only include analytics_storage from default mapping
      expect(mockGtag).toHaveBeenCalledWith("consent", "update", {
        analytics_storage: "granted",
      });
    });

    test("does not call gtag when no matching consent keys exist", () => {
      const mockGtag = setupGtag();
      setupFidesWithConsent({
        essential: true, // Not in default mapping
      });

      gcm(); // Use default mapping

      triggerConsentEvent("FidesUpdated", {
        essential: true,
      });

      // Should not call gtag since no keys match
      expect(mockGtag).not.toHaveBeenCalled();
    });
  });

  describe("gtag not loaded", () => {
    test("does nothing when gtag is not loaded", () => {
      setupFidesWithConsent({ analytics: true });

      gcm();

      // Should not throw
      expect(() => {
        triggerConsentEvent("FidesUpdated", { analytics: true });
      }).not.toThrow();
    });
  });

  describe("Event subscription", () => {
    test.each(["FidesReady", "FidesUpdated"])(
      "subscribes to %s event",
      (eventName) => {
        const spy = jest.spyOn(window, "addEventListener");
        gcm();
        expect(spy).toHaveBeenCalledWith(eventName, expect.any(Function));
      },
    );

    test("pushes consent immediately if Fides is already initialized", () => {
      const mockGtag = setupGtag();
      setupFidesWithConsent({
        analytics: true,
      });

      gcm();

      // Should push consent immediately
      expect(mockGtag).toHaveBeenCalledWith("consent", "update", {
        analytics_storage: "granted",
      });
    });
  });

  describe("consent() API", () => {
    test("returns null when gtag is not loaded", () => {
      const integration = gcm();
      const state = integration.consent();

      expect(state).toBeNull();
    });

    test("returns null when gtag is loaded (cannot read gtag state)", () => {
      setupGtag();

      const integration = gcm();
      const state = integration.consent();

      // gtag doesn't provide a read API, so we return null
      expect(state).toBeNull();
    });
  });

  describe("Edge cases", () => {
    test("handles empty consent object", () => {
      const mockGtag = setupGtag();
      setupFidesWithConsent({});

      gcm();
      triggerConsentEvent("FidesUpdated", {});

      // Should not call gtag with empty consent
      expect(mockGtag).not.toHaveBeenCalled();
    });

    test("handles undefined consent values as false", () => {
      const mockGtag = setupGtag();
      setupFidesWithConsent({
        analytics: undefined as any,
      });

      gcm();
      triggerConsentEvent("FidesUpdated", {
        analytics: undefined as any,
      });

      // undefined is falsy, so should be "denied"
      expect(mockGtag).toHaveBeenCalledWith("consent", "update", {
        analytics_storage: "denied",
      });
    });

    test("handles custom mapping with empty arrays", () => {
      const mockGtag = setupGtag();
      // Don't set Fides as initialized to avoid immediate consent push
      window.Fides = {
        consent: {
          analytics: true,
        },
        initialized: false,
      } as any as FidesGlobal;

      gcm({
        purposeMapping: {
          analytics: [],
        },
      });

      // Clear mock to ignore any calls from setup, focus on the event trigger
      mockGtag.mockClear();

      triggerConsentEvent("FidesUpdated", {
        analytics: true,
      });

      // Our listener with empty mapping should not call gtag
      // Other listeners from previous tests may call gtag, so we can't check total count
      // Instead, verify that no call was made with an empty consent object
      // (which is what would happen if empty arrays didn't work correctly)
      const callsWithEmptyConsent = mockGtag.mock.calls.filter(
        (call) =>
          call[0] === "consent" &&
          call[1] === "update" &&
          Object.keys(call[2] || {}).length === 0,
      );

      expect(callsWithEmptyConsent).toHaveLength(0);
    });

    test("handles consent key with falsy but not false values", () => {
      const mockGtag = setupGtag();
      setupFidesWithConsent({
        analytics: null as any,
        advertising: 0 as any,
        functional: "" as any,
      });

      gcm();
      triggerConsentEvent("FidesUpdated", {
        analytics: null as any,
        advertising: 0 as any,
        functional: "" as any,
      });

      // All falsy values should map to "denied"
      expect(mockGtag).toHaveBeenCalledWith("consent", "update", {
        analytics_storage: "denied",
        ad_storage: "denied",
        ad_personalization: "denied",
        ad_user_data: "denied",
        functionality_storage: "denied",
        personalization_storage: "denied",
      });
    });

    test("handles truthy non-boolean values as granted", () => {
      const mockGtag = setupGtag();
      setupFidesWithConsent({
        analytics: 1 as any,
        advertising: "yes" as any,
      });

      gcm();
      triggerConsentEvent("FidesUpdated", {
        analytics: 1 as any,
        advertising: "yes" as any,
      });

      // Truthy values should map to "granted"
      expect(mockGtag).toHaveBeenCalledWith("consent", "update", {
        analytics_storage: "granted",
        ad_storage: "granted",
        ad_personalization: "granted",
        ad_user_data: "granted",
      });
    });

    test("handles mixed granted and denied across all Google types", () => {
      const mockGtag = setupGtag();
      setupFidesWithConsent({
        analytics: true,
        advertising: false,
        functional: true,
        data_sales_and_sharing: false,
        marketing: true,
      });

      gcm();
      triggerConsentEvent("FidesUpdated", {
        analytics: true,
        advertising: false,
        functional: true,
        data_sales_and_sharing: false,
        marketing: true,
      });

      // Note: marketing=true will overwrite data_sales_and_sharing=false for ad_* types
      expect(mockGtag).toHaveBeenCalledWith("consent", "update", {
        analytics_storage: "granted",
        ad_storage: "granted", // marketing=true wins
        ad_personalization: "granted", // marketing=true wins
        ad_user_data: "granted", // marketing=true wins
        functionality_storage: "granted",
        personalization_storage: "granted",
      });
    });
  });

  describe("All Google consent types", () => {
    test("supports all standard Google consent types", () => {
      const mockGtag = setupGtag();
      setupFidesWithConsent({
        all_types: true,
      });

      gcm({
        purposeMapping: {
          all_types: [
            "ad_storage",
            "ad_personalization",
            "ad_user_data",
            "analytics_storage",
            "functionality_storage",
            "personalization_storage",
            "security_storage",
          ],
        },
      });

      triggerConsentEvent("FidesUpdated", {
        all_types: true,
      });

      expect(mockGtag).toHaveBeenCalledWith("consent", "update", {
        ad_storage: "granted",
        ad_personalization: "granted",
        ad_user_data: "granted",
        analytics_storage: "granted",
        functionality_storage: "granted",
        personalization_storage: "granted",
        security_storage: "granted",
      });
    });
  });
});
