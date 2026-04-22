/* eslint-disable no-underscore-dangle */
/**
 * Matomo integration for Fides
 *
 * Automatically syncs Fides consent with Matomo's tracking consent
 * and/or cookie consent APIs via _paq.push().
 *
 * @see https://developer.matomo.org/guides/tracking-consent
 */

import { NoticeConsent } from "../lib/consent-types";
import { processExternalConsentValue } from "../lib/shared-consent-utils";
import { subscribeToConsent } from "./integration-utils";

type MatomoConsentMode = "tracking" | "cookie" | "both";

export interface MatomoOptions {
  /**
   * Which Matomo consent mechanism to manage.
   * - "tracking": Controls Matomo's tracking consent (requireConsent / setConsentGiven)
   * - "cookie": Controls Matomo's cookie consent (requireCookieConsent / setCookieConsentGiven)
   * - "both": Controls both tracking and cookie consent together
   */
  consentMode: MatomoConsentMode;

  /**
   * Whether to use rememberConsentGiven() (persists to Matomo's mtm_consent cookie)
   * vs setConsentGiven() (session-only). Defaults true so Matomo can resume tracking
   * on page loads before Fides initializes.
   */
  rememberConsent: boolean;
}

declare global {
  interface Window {
    _paq?: unknown[][];
  }
}

const DEFAULT_OPTIONS: MatomoOptions = {
  consentMode: "tracking",
  rememberConsent: true,
};

const DEFAULT_CONSENT_KEYS = ["analytics", "performance"];

const paqsWithRequireConsent = new WeakSet<unknown[][]>();

const consentModeChecks = (consentMode: MatomoConsentMode) => ({
  isTracking: () => consentMode === "tracking" || consentMode === "both",
  isCookie: () => consentMode === "cookie" || consentMode === "both",
});

/**
 * Find the first consent key present in the Fides consent object.
 * Uses the `in` operator (like GCM) to distinguish "key absent" (non-applicable, OMIT mode)
 * from "key present with falsy value" (user opted out).
 */
const findConsentKey = (consent: NoticeConsent): string | null =>
  DEFAULT_CONSENT_KEYS.find((key) => key in consent) ?? null;

/**
 * Push requireConsent / requireCookieConsent to _paq based on consentMode.
 */
const pushRequireConsent = (
  paq: unknown[][],
  consentMode: MatomoConsentMode,
): void => {
  const mode = consentModeChecks(consentMode);
  if (mode.isTracking()) {
    paq.push(["requireConsent"]);
    fidesDebugger("[Fides Matomo] Pushed requireConsent");
  }
  if (mode.isCookie()) {
    paq.push(["requireCookieConsent"]);
    fidesDebugger("[Fides Matomo] Pushed requireCookieConsent");
  }
};

/**
 * Push the appropriate grant or revoke command to _paq.
 */
const pushConsentUpdate = (
  paq: unknown[][],
  consentMode: MatomoConsentMode,
  rememberConsent: boolean,
  granted: boolean,
): void => {
  if (granted) {
    const mode = consentModeChecks(consentMode);
    if (mode.isTracking()) {
      const command = rememberConsent
        ? "rememberConsentGiven"
        : "setConsentGiven";
      paq.push([command]);
      fidesDebugger(`[Fides Matomo] Pushed ${command}`);
    }
    if (mode.isCookie()) {
      const command = rememberConsent
        ? "rememberCookieConsentGiven"
        : "setCookieConsentGiven";
      paq.push([command]);
      fidesDebugger(`[Fides Matomo] Pushed ${command}`);
    }
  } else {
    // Always revoke both consent types regardless of consentMode to clean up
    // stale consent cookies (e.g. if a site switches from "both" to "cookie",
    // tracking consent must still be revoked). These are safe no-ops in Matomo
    // when consent was never granted.
    paq.push(["forgetConsentGiven"]);
    fidesDebugger("[Fides Matomo] Pushed forgetConsentGiven");
    paq.push(["forgetCookieConsentGiven"]);
    fidesDebugger("[Fides Matomo] Pushed forgetCookieConsentGiven");
  }
};

/**
 * Initialize the Matomo consent integration.
 *
 * Automatically syncs Fides consent with Matomo's tracking consent and/or
 * cookie consent APIs. Matomo is only put into consent-required mode when the
 * relevant consent key (analytics or performance) is present in the Fides
 * consent object, allowing free tracking in jurisdictions where consent is
 * not applicable.
 */
export const matomo = (options?: Partial<MatomoOptions>): void => {
  const opts: MatomoOptions = { ...DEFAULT_OPTIONS, ...options };

  // Ensure _paq exists (Matomo's standard pre-load queue pattern)
  window._paq = window._paq ?? [];
  const paq = window._paq;

  subscribeToConsent((consent) => {
    const key = findConsentKey(consent);

    if (key === null) {
      fidesDebugger(
        "[Fides Matomo] No consent key found in Fides consent, skipping",
      );
      return;
    }

    // On the first event where the consent key is present, put Matomo into
    // consent-required mode. The grant/revoke that follows immediately after
    // ensures there is no tracking gap.
    if (!paqsWithRequireConsent.has(paq)) {
      pushRequireConsent(paq, opts.consentMode);
      paqsWithRequireConsent.add(paq);
    }

    const granted = processExternalConsentValue(consent[key]);
    pushConsentUpdate(paq, opts.consentMode, opts.rememberConsent, granted);
  });
};
