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

  describe("requireConsent idempotency", () => {
    test("pushes requireConsent exactly once at init, not on subsequent events", () => {
      setupFidesWithConsent({ analytics: true });
      matomo();

      // requireConsent is pushed synchronously at call time, before any event
      // fires. Synthetic event then pushes the grant. Count should be 1.
      const requireCallsAfterInit = getPaq().filter(
        (cmd) => cmd[0] === "requireConsent",
      );
      expect(requireCallsAfterInit).toHaveLength(1);

      triggerConsentEvent("FidesUpdated", { analytics: false });

      const requireCallsAfterEvent = getPaq().filter(
        (cmd) => cmd[0] === "requireConsent",
      );
      expect(requireCallsAfterEvent).toHaveLength(1);
    });

    test("subsequent events push grants/revokes to current window._paq (orphan guard)", () => {
      // Mirrors what matomo.js does at runtime: after processing the queued
      // Array, it swaps window._paq with a wrapper object whose `push`
      // forwards to the live Tracker. Subsequent events must push to the NEW
      // _paq, not to an orphaned pre-swap reference.
      setupFidesWithConsent({ analytics: true });
      matomo();

      const wrapperCalls: unknown[][] = [];
      const wrapper = {
        push: (cmd: unknown[]) => {
          wrapperCalls.push(cmd);
          return 0;
        },
      };
      setPaq(wrapper as unknown as unknown[][]);

      triggerConsentEvent("FidesUpdated", { analytics: false });

      expect(wrapperCalls).toEqual(
        expect.arrayContaining([
          ["forgetConsentGiven"],
          ["forgetCookieConsentGiven"],
        ]),
      );
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

  describe("requireConsent timing", () => {
    test("pushes requireConsent synchronously at call time, before any event fires", () => {
      // Fides is not initialized yet; no synthetic event should fire.
      window.Fides = undefined as any;
      matomo();

      // requireConsent must already be in the queue by the time matomo()
      // returns, so it lands ahead of the site's Matomo tracker snippet.
      expect(getPaq()).toEqual([["requireConsent"]]);
    });

    test("pushes requireConsent regardless of whether consent key is present (OMIT mode)", () => {
      // Even in OMIT mode we push requireConsent up front; the event handler
      // then grants consent to unblock tracking.
      setupFidesWithConsent({ essential: true });
      matomo();

      expect(getPaq()).toEqual(expect.arrayContaining([["requireConsent"]]));
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

    test("pushes setConsentGiven and setCookieConsentGiven when granted with rememberConsent: false", () => {
      setupFidesWithConsent({ analytics: true });
      matomo({ consentMode: "both", rememberConsent: false });

      expect(getPaq()).toEqual(
        expect.arrayContaining([
          ["setConsentGiven"],
          ["setCookieConsentGiven"],
        ]),
      );
      expect(getPaq()).not.toEqual(
        expect.arrayContaining([["rememberConsentGiven"]]),
      );
      expect(getPaq()).not.toEqual(
        expect.arrayContaining([["rememberCookieConsentGiven"]]),
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

    test("grants consent when neither analytics nor performance key is present (OMIT)", () => {
      setupFidesWithConsent({ marketing: true });
      matomo();

      // requireConsent pushed at init, then a grant to unblock tracking.
      expect(getPaq()).toEqual(
        expect.arrayContaining([["requireConsent"], ["rememberConsentGiven"]]),
      );
      // No revoke commands
      expect(getPaq()).not.toEqual(
        expect.arrayContaining([["forgetConsentGiven"]]),
      );
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
    test("OMIT mode: no consent key, Matomo is granted consent to unblock tracking", () => {
      // Simulates OMIT mode where the analytics key is absent. We push
      // requireConsent up front to be safe, then grant on the event so
      // tracking actually flows in jurisdictions where consent isn't required.
      setupFidesWithConsent({});
      matomo();

      expect(getPaq()).toEqual(
        expect.arrayContaining([["requireConsent"], ["rememberConsentGiven"]]),
      );
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
      // No Fides.consent on window → synthetic event does not fire.
      window.Fides = { initialized: false } as any as FidesGlobal;
      matomo();

      // requireConsent pushed synchronously at init; no grant/revoke yet
      // because no synthetic event fired and no real event has been dispatched.
      expect(getPaq()).toEqual([["requireConsent"]]);

      // Now consent arrives via event
      triggerConsentEvent("FidesUpdated", { analytics: false });

      expect(getPaq()).toEqual(
        expect.arrayContaining([["requireConsent"], ["forgetConsentGiven"]]),
      );
    });
  });
});
