import { FidesGlobal } from "../../src/fides";
import { matomo } from "../../src/integrations/matomo";

// Mock fidesDebugger global
/* eslint-disable */
// @ts-ignore
globalThis.fidesDebugger = jest.fn();
/* eslint-enable */

// Helpers to avoid eslint no-underscore-dangle errors with window._paq
const PAQ = "_paq" as const;
const getPaq = (): unknown[][] => (window as any)[PAQ];
const setPaq = (value: unknown[][]) => {
  (window as any)[PAQ] = value;
};
const deletePaq = () => {
  delete (window as any)[PAQ];
};

/**
 * Setup Fides with consent
 */
const setupFidesWithConsent = (consent: Record<string, boolean | string>) => {
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
  consent: Record<string, boolean | string>,
) => {
  window.dispatchEvent(
    new CustomEvent(eventName, {
      detail: { consent },
    }),
  );
};

describe("matomo", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    setPaq([]);
  });

  afterEach(() => {
    deletePaq();
    window.Fides = undefined as any;
  });

  // NOTE: This test must run before other matomo() calls to avoid leaked event
  // listeners from prior tests (subscribeToConsent listeners cannot be removed).
  describe("requireConsent idempotency", () => {
    test("does not push requireConsent again on subsequent events", () => {
      setupFidesWithConsent({ analytics: true });
      matomo();

      // Synthetic event fired synchronously; record state
      const lengthAfterInit = getPaq().length;

      // Dispatch another event
      triggerConsentEvent("FidesUpdated", { analytics: false });

      // Only this matomo() instance's handler should have fired.
      // Commands after init should NOT include another requireConsent.
      const newCommands = getPaq().slice(lengthAfterInit);
      const requireCalls = newCommands.filter(
        (cmd) => cmd[0] === "requireConsent",
      );
      expect(requireCalls).toHaveLength(0);
    });
  });

  describe("_paq initialization", () => {
    test("creates _paq if it does not exist", () => {
      deletePaq();
      matomo();
      expect(Array.isArray(getPaq())).toBe(true);
    });

    test("reuses existing _paq", () => {
      const existing: unknown[][] = [["existingCommand"]];
      setPaq(existing);
      matomo();
      expect(getPaq()).toBe(existing);
    });
  });

  describe("Conditional requireConsent", () => {
    test("pushes requireConsent on first event when consent key is present", () => {
      setupFidesWithConsent({ analytics: true });
      matomo();

      expect(getPaq()).toEqual(expect.arrayContaining([["requireConsent"]]));
    });

    test("does NOT push requireConsent when consent key is absent (OMIT mode)", () => {
      setupFidesWithConsent({ essential: true });
      matomo();

      expect(getPaq()).not.toEqual(
        expect.arrayContaining([["requireConsent"]]),
      );
    });
  });

  describe("Tracking consent mode", () => {
    test("pushes rememberConsentGiven when granted (default rememberConsent: true)", () => {
      setupFidesWithConsent({ analytics: true });
      matomo({ consentMode: "tracking" });

      expect(getPaq()).toEqual(
        expect.arrayContaining([["requireConsent"], ["rememberConsentGiven"]]),
      );
    });

    test("pushes setConsentGiven when granted with rememberConsent: false", () => {
      setupFidesWithConsent({ analytics: true });
      matomo({ consentMode: "tracking", rememberConsent: false });

      expect(getPaq()).toEqual(expect.arrayContaining([["setConsentGiven"]]));
      expect(getPaq()).not.toEqual(
        expect.arrayContaining([["rememberConsentGiven"]]),
      );
    });

    test("pushes forgetConsentGiven when revoked", () => {
      setupFidesWithConsent({ analytics: false });
      matomo({ consentMode: "tracking" });

      expect(getPaq()).toEqual(
        expect.arrayContaining([["requireConsent"], ["forgetConsentGiven"]]),
      );
    });
  });

  describe("Cookie consent mode", () => {
    test("pushes requireCookieConsent and rememberCookieConsentGiven when granted", () => {
      setupFidesWithConsent({ analytics: true });
      matomo({ consentMode: "cookie" });

      expect(getPaq()).toEqual(
        expect.arrayContaining([
          ["requireCookieConsent"],
          ["rememberCookieConsentGiven"],
        ]),
      );
      expect(getPaq()).not.toEqual(
        expect.arrayContaining([["requireConsent"]]),
      );
    });

    test("pushes setCookieConsentGiven when granted with rememberConsent: false", () => {
      setupFidesWithConsent({ analytics: true });
      matomo({ consentMode: "cookie", rememberConsent: false });

      expect(getPaq()).toEqual(
        expect.arrayContaining([["setCookieConsentGiven"]]),
      );
    });

    test("pushes forgetCookieConsentGiven when revoked", () => {
      setupFidesWithConsent({ analytics: false });
      matomo({ consentMode: "cookie" });

      expect(getPaq()).toEqual(
        expect.arrayContaining([["forgetCookieConsentGiven"]]),
      );
    });
  });

  describe("Both consent mode", () => {
    test("pushes both require commands on init", () => {
      setupFidesWithConsent({ analytics: true });
      matomo({ consentMode: "both" });

      expect(getPaq()).toEqual(
        expect.arrayContaining([["requireConsent"], ["requireCookieConsent"]]),
      );
    });

    test("pushes both grant commands when consent is granted", () => {
      setupFidesWithConsent({ analytics: true });
      matomo({ consentMode: "both" });

      expect(getPaq()).toEqual(
        expect.arrayContaining([
          ["rememberConsentGiven"],
          ["rememberCookieConsentGiven"],
        ]),
      );
    });

    test("pushes both revoke commands when consent is revoked", () => {
      setupFidesWithConsent({ analytics: false });
      matomo({ consentMode: "both" });

      expect(getPaq()).toEqual(
        expect.arrayContaining([
          ["forgetConsentGiven"],
          ["forgetCookieConsentGiven"],
        ]),
      );
    });
  });

  describe("Consent key resolution", () => {
    test("uses analytics key when present", () => {
      setupFidesWithConsent({ analytics: true, performance: false });
      matomo();

      // analytics=true should result in grant, not revoke
      expect(getPaq()).toEqual(
        expect.arrayContaining([["rememberConsentGiven"]]),
      );
      expect(getPaq()).not.toEqual(
        expect.arrayContaining([["forgetConsentGiven"]]),
      );
    });

    test("falls back to performance key when analytics is absent", () => {
      setupFidesWithConsent({ performance: true });
      matomo();

      expect(getPaq()).toEqual(
        expect.arrayContaining([["requireConsent"], ["rememberConsentGiven"]]),
      );
    });

    test("takes no action when neither key is present", () => {
      setupFidesWithConsent({ marketing: true });
      matomo();

      expect(getPaq()).toEqual([]);
    });
  });

  describe("Consent value normalization", () => {
    test("handles string opt_in", () => {
      setupFidesWithConsent({ analytics: "opt_in" });
      matomo();

      expect(getPaq()).toEqual(
        expect.arrayContaining([["rememberConsentGiven"]]),
      );
    });

    test("handles string opt_out", () => {
      setupFidesWithConsent({ analytics: "opt_out" });
      matomo();

      expect(getPaq()).toEqual(
        expect.arrayContaining([["forgetConsentGiven"]]),
      );
    });

    test("handles string acknowledge as granted", () => {
      setupFidesWithConsent({ analytics: "acknowledge" });
      matomo();

      expect(getPaq()).toEqual(
        expect.arrayContaining([["rememberConsentGiven"]]),
      );
    });
  });

  describe("Non-applicable flag modes", () => {
    test("OMIT mode: no consent key, Matomo tracks freely", () => {
      // Simulates OMIT mode where the analytics key is absent
      setupFidesWithConsent({});
      matomo();

      // No requireConsent, no grant, no revoke
      expect(getPaq()).toEqual([]);
    });

    test("INCLUDE mode with boolean: key present as true, consent granted", () => {
      // Simulates INCLUDE mode where non-applicable key is set to true
      setupFidesWithConsent({ analytics: true });
      matomo();

      expect(getPaq()).toEqual(
        expect.arrayContaining([["requireConsent"], ["rememberConsentGiven"]]),
      );
    });
  });

  describe("Event subscription", () => {
    test.each(["FidesReady", "FidesUpdated"])(
      "subscribes to %s event",
      (eventName) => {
        const spy = jest.spyOn(window, "addEventListener");
        matomo();
        expect(spy).toHaveBeenCalledWith(eventName, expect.any(Function));
      },
    );

    test("pushes consent immediately if Fides is already initialized (synthetic event)", () => {
      setupFidesWithConsent({ analytics: true });
      matomo();

      expect(getPaq()).toEqual(
        expect.arrayContaining([["rememberConsentGiven"]]),
      );
    });

    test("responds to FidesUpdated events", () => {
      window.Fides = { consent: {}, initialized: false } as any as FidesGlobal;
      matomo();

      // Initially no commands (no consent key)
      expect(getPaq()).toEqual([]);

      // Now consent arrives via event
      triggerConsentEvent("FidesUpdated", { analytics: false });

      expect(getPaq()).toEqual(
        expect.arrayContaining([["requireConsent"], ["forgetConsentGiven"]]),
      );
    });
  });
});
