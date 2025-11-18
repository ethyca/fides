import { FidesGlobal } from "../../src/fides";
import { aep } from "../../src/integrations/aep";

// Mock fidesDebugger global
(global as any).fidesDebugger = jest.fn();

/**
 * Mock Adobe Web SDK (Alloy)
 */
const setupAlloy = () => {
  const mockAlloy = jest.fn(() => {
    return Promise.resolve();
  });
  window.alloy = mockAlloy;
  return mockAlloy;
};

/**
 * Mock Adobe ECID Opt-In Service
 */
const setupOptIn = () => {
  const mockApprove = jest.fn();
  const mockDeny = jest.fn();
  const mockIsApproved = jest.fn().mockReturnValue(false);

  window.adobe = {
    optIn: {
      Categories: {
        ANALYTICS: "aa",
        TARGET: "target",
        AAM: "aam",
        ADCLOUD: "adcloud",
        CAMPAIGN: "campaign",
        ECID: "ecid",
        LIVEFYRE: "livefyre",
        MEDIAAA: "mediaaa",
      },
      approve: mockApprove,
      deny: mockDeny,
      isApproved: mockIsApproved,
    },
  };

  return { mockApprove, mockDeny, mockIsApproved };
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

describe("aep", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    window.alloy = undefined;
    window.adobe = undefined;
    window.Fides = undefined as any;
  });

  describe("Adobe Web SDK (Alloy)", () => {
    test("pushes consent to alloy with default purpose mapping", () => {
      const mockAlloy = setupAlloy();
      setupFidesWithConsent({
        analytics: true,
        functional: false,
        advertising: true,
      });

      aep();
      triggerConsentEvent("FidesUpdated", {
        analytics: true,
        functional: false,
        advertising: true,
      });

      // Note: "personalize" is in both functional and advertising.
      // With advertising=true, personalize="in" (last write wins)
      expect(mockAlloy).toHaveBeenCalledWith("setConsent", {
        consent: [
          {
            standard: "Adobe",
            version: "2.0",
            value: {
              collect: "in",
              measure: "in",
              personalize: "in", // from advertising=true
              share: "in",
            },
          },
        ],
      });
    });

    test("pushes consent to alloy with custom purpose mapping", () => {
      const mockAlloy = setupAlloy();
      setupFidesWithConsent({
        marketing: true,
        essential: true,
      });

      aep({
        purposeMapping: {
          marketing: ["personalize", "share"],
          essential: ["collect"],
        },
      });

      triggerConsentEvent("FidesUpdated", {
        marketing: true,
        essential: true,
      });

      expect(mockAlloy).toHaveBeenCalledWith("setConsent", {
        consent: [
          {
            standard: "Adobe",
            version: "2.0",
            value: {
              personalize: "in",
              share: "in",
              collect: "in",
            },
          },
        ],
      });
    });

    test("sets purposes to 'out' when consent is denied", () => {
      const mockAlloy = setupAlloy();
      setupFidesWithConsent({
        analytics: false,
        functional: false,
        advertising: false,
      });

      aep();
      triggerConsentEvent("FidesUpdated", {
        analytics: false,
        functional: false,
        advertising: false,
      });

      expect(mockAlloy).toHaveBeenCalledWith("setConsent", {
        consent: [
          {
            standard: "Adobe",
            version: "2.0",
            value: {
              collect: "out",
              measure: "out",
              personalize: "out",
              share: "out",
            },
          },
        ],
      });
    });
  });

  describe("ECID Opt-In Service", () => {
    test("approves categories with default ECID mapping", () => {
      const { mockApprove, mockDeny } = setupOptIn();
      setupFidesWithConsent({
        analytics: true,
        functional: true,
        advertising: false,
      });

      aep();
      triggerConsentEvent("FidesUpdated", {
        analytics: true,
        functional: true,
        advertising: false,
      });

      // analytics -> aa (approved)
      expect(mockApprove).toHaveBeenCalledWith("aa");
      // functional -> target (approved)
      expect(mockApprove).toHaveBeenCalledWith("target");
      // advertising -> aam (denied)
      expect(mockDeny).toHaveBeenCalledWith("aam");
    });

    test("approves categories with custom ECID mapping", () => {
      const { mockApprove, mockDeny } = setupOptIn();
      setupFidesWithConsent({
        marketing: true,
        personalization: false,
      });

      aep({
        ecidMapping: {
          marketing: ["aa", "aam", "adcloud"],
          personalization: ["target", "campaign"],
        },
      });

      triggerConsentEvent("FidesUpdated", {
        marketing: true,
        personalization: false,
      });

      // marketing categories approved
      expect(mockApprove).toHaveBeenCalledWith("aa");
      expect(mockApprove).toHaveBeenCalledWith("aam");
      expect(mockApprove).toHaveBeenCalledWith("adcloud");

      // personalization categories denied
      expect(mockDeny).toHaveBeenCalledWith("target");
      expect(mockDeny).toHaveBeenCalledWith("campaign");
    });

    test("uses OR logic when multiple Fides keys map to same category", () => {
      const { mockApprove } = setupOptIn();
      setupFidesWithConsent({
        analytics: false,
        marketing: true,
      });

      // Both keys map to 'aa', but marketing=true should approve it
      aep({
        ecidMapping: {
          analytics: ["aa"],
          marketing: ["aa", "aam"],
        },
      });

      triggerConsentEvent("FidesUpdated", {
        analytics: false,
        marketing: true,
      });

      // 'aa' should be approved because marketing=true (OR logic)
      expect(mockApprove).toHaveBeenCalledWith("aa");
      expect(mockApprove).toHaveBeenCalledWith("aam");
    });

    test("handles all Adobe ECID categories dynamically", () => {
      const { mockApprove } = setupOptIn();
      setupFidesWithConsent({
        everything: true,
      });

      aep({
        ecidMapping: {
          everything: [
            "aa",
            "target",
            "aam",
            "adcloud",
            "campaign",
            "ecid",
            "livefyre",
            "mediaaa",
          ],
        },
      });

      triggerConsentEvent("FidesUpdated", {
        everything: true,
      });

      // All categories should be approved
      expect(mockApprove).toHaveBeenCalledWith("aa");
      expect(mockApprove).toHaveBeenCalledWith("target");
      expect(mockApprove).toHaveBeenCalledWith("aam");
      expect(mockApprove).toHaveBeenCalledWith("adcloud");
      expect(mockApprove).toHaveBeenCalledWith("campaign");
      expect(mockApprove).toHaveBeenCalledWith("ecid");
      expect(mockApprove).toHaveBeenCalledWith("livefyre");
      expect(mockApprove).toHaveBeenCalledWith("mediaaa");
    });

    test("does not touch unmapped categories", () => {
      const { mockApprove } = setupOptIn();

      // Don't set Fides as initialized to avoid synthetic events
      window.Fides = {
        consent: {
          analytics: true,
        },
        initialized: false, // Not initialized yet
      } as any as FidesGlobal;

      // Only map analytics to 'aa', leave other categories untouched
      aep({
        ecidMapping: {
          analytics: ["aa"],
        },
      });

      // Clear mocks after aep() setup to ignore any initial calls
      mockApprove.mockClear();

      triggerConsentEvent("FidesUpdated", {
        analytics: true,
      });

      // Only 'aa' should be approved
      expect(mockApprove).toHaveBeenCalledWith("aa");
      // Check the actual calls to ensure only 'aa' was in them
      const actualCalls = mockApprove.mock.calls.map((call) => call[0]);
      expect(actualCalls).toContain("aa");
      // All calls should be for 'aa' (no other categories)
      actualCalls.forEach((category) => {
        expect(category).toBe("aa");
      });
    });
  });

  describe("Both Adobe products", () => {
    test("pushes consent to both alloy and optIn when both are loaded", () => {
      const mockAlloy = setupAlloy();
      const { mockApprove } = setupOptIn();
      setupFidesWithConsent({
        analytics: true,
        functional: true,
      });

      aep();
      triggerConsentEvent("FidesUpdated", {
        analytics: true,
        functional: true,
      });

      // Alloy should be called
      expect(mockAlloy).toHaveBeenCalledWith("setConsent", expect.any(Object));

      // OptIn should be called
      expect(mockApprove).toHaveBeenCalledWith("aa");
      expect(mockApprove).toHaveBeenCalledWith("target");
    });
  });

  describe("Adobe not loaded", () => {
    test("does nothing when Adobe is not loaded", () => {
      setupFidesWithConsent({ analytics: true });

      aep();

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
        aep();
        expect(spy).toHaveBeenCalledWith(eventName, expect.any(Function));
      },
    );

    test("pushes consent immediately if Fides is already initialized", () => {
      const mockAlloy = setupAlloy();
      setupFidesWithConsent({
        analytics: true,
      });

      aep();

      // Should push consent immediately
      expect(mockAlloy).toHaveBeenCalledWith("setConsent", expect.any(Object));
    });
  });

  describe("consent() API", () => {
    test("returns state when alloy is loaded", () => {
      setupAlloy();

      const integration = aep();
      const state = integration.consent();

      expect(state.alloy).toEqual({
        configured: true,
        purposes: undefined,
      });
      expect(state.timestamp).toBeDefined();
    });

    test("returns state when optIn is loaded", () => {
      const { mockIsApproved } = setupOptIn();
      mockIsApproved.mockImplementation((category: string) => {
        return category === "aa";
      });

      const integration = aep();
      const state = integration.consent();

      expect(state.ecidOptIn?.configured).toBe(true);
      expect(state.ecidOptIn?.categories).toEqual({
        aa: true,
        target: false,
        aam: false,
        adcloud: false,
        campaign: false,
        ecid: false,
        livefyre: false,
        mediaaa: false,
      });
      expect(state.timestamp).toBeDefined();
    });

    test("returns state when neither Adobe product is loaded", () => {
      const integration = aep();
      const state = integration.consent();

      expect(state.alloy).toEqual({
        configured: false,
      });
      expect(state.ecidOptIn).toEqual({
        configured: false,
      });
      expect(state.timestamp).toBeDefined();
    });

    test("handles optIn errors gracefully in consent() API", () => {
      window.adobe = {
        optIn: {
          Categories: {
            ANALYTICS: "aa",
          },
          approve: jest.fn(),
          deny: jest.fn(),
          isApproved: () => {
            throw new Error("isApproved error");
          },
        },
      };

      const integration = aep();
      const state = integration.consent();

      expect(state.ecidOptIn).toEqual({
        configured: true,
      });
    });
  });

  describe("Edge cases", () => {
    test("handles empty consent object", () => {
      const mockAlloy = setupAlloy();
      setupFidesWithConsent({});

      aep();
      triggerConsentEvent("FidesUpdated", {});

      // Should still call alloy, all purposes will be "out"
      expect(mockAlloy).toHaveBeenCalledWith("setConsent", {
        consent: [
          {
            standard: "Adobe",
            version: "2.0",
            value: {
              collect: "out",
              measure: "out",
              personalize: "out",
              share: "out",
            },
          },
        ],
      });
    });

    test("handles undefined consent values as false", () => {
      const mockAlloy = setupAlloy();
      setupFidesWithConsent({
        analytics: undefined as any,
      });

      aep();
      triggerConsentEvent("FidesUpdated", {
        analytics: undefined as any,
      });

      expect(mockAlloy).toHaveBeenCalledWith("setConsent", {
        consent: [
          {
            standard: "Adobe",
            version: "2.0",
            value: {
              collect: "out",
              measure: "out",
              personalize: "out",
              share: "out",
            },
          },
        ],
      });
    });

    test("handles custom mapping with empty arrays", () => {
      const mockAlloy = setupAlloy();
      setupFidesWithConsent({
        analytics: true,
      });

      aep({
        purposeMapping: {
          analytics: [],
        },
      });

      triggerConsentEvent("FidesUpdated", {
        analytics: true,
      });

      // Should still call alloy, but with empty purposes
      expect(mockAlloy).toHaveBeenCalledWith("setConsent", {
        consent: [
          {
            standard: "Adobe",
            version: "2.0",
            value: {},
          },
        ],
      });
    });
  });
});
