/**
 * Google Consent Mode v2 integration for Fides
 *
 * Provides direct integration with Google's Consent Mode v2 API via gtag().
 * Automatically syncs Fides consent with Google's consent types.
 *
 * @see https://developers.google.com/tag-platform/security/guides/consent
 */

import { NoticeConsent } from "../lib/consent-types";
import { subscribeToConsent } from "./integration-utils";

declare global {
  interface Window {
    gtag?: (...args: any[]) => void;
  }
}

/**
 * Google Consent Mode v2 consent types
 */
export type GoogleConsentType =
  | "ad_storage"
  | "ad_personalization"
  | "ad_user_data"
  | "analytics_storage"
  | "functionality_storage"
  | "personalization_storage"
  | "security_storage";

/**
 * Google consent state: 'granted' or 'denied'
 */
export type GoogleConsentState = "granted" | "denied";

/**
 * Mapping from Fides consent keys to Google Consent Mode types
 *
 * @example
 * ```typescript
 * {
 *   performance: ['analytics_storage'],
 *   advertising: ['ad_storage', 'ad_personalization', 'ad_user_data'],
 *   functional: ['functionality_storage', 'personalization_storage']
 * }
 * ```
 */
export type GtagConsentMapping = Record<string, GoogleConsentType[]>;

/**
 * Options for Google Consent Mode integration
 */
export interface GtagConsentOptions {
  /**
   * Mapping from Fides consent keys to Google Consent Mode types
   *
   * @example
   * ```typescript
   * {
   *   performance: ['analytics_storage'],
   *   advertising: ['ad_storage', 'ad_personalization', 'ad_user_data']
   * }
   * ```
   */
  purposeMapping: GtagConsentMapping;

  /**
   * Enable debug logging
   * @default false
   */
  debug?: boolean;
}

/**
 * Google Consent Mode integration object
 */
export interface GtagConsentIntegration {
  /**
   * Get current Google consent state
   */
  consent: () => Record<GoogleConsentType, GoogleConsentState> | null;
}

/**
 * Default mapping from Fides consent to Google Consent Mode types
 */
const DEFAULT_CONSENT_MAPPING: GtagConsentMapping = {
  analytics: ["analytics_storage"],
  advertising: ["ad_storage", "ad_personalization", "ad_user_data"],
  functional: ["functionality_storage", "personalization_storage"],
};

/**
 * Build Google Consent Mode object from Fides consent
 */
const buildGoogleConsent = (
  consent: NoticeConsent,
  mapping: GtagConsentMapping,
  debug = false,
): Record<GoogleConsentType, GoogleConsentState> => {
  const googleConsent: Partial<Record<GoogleConsentType, GoogleConsentState>> =
    {};

  // For each Fides consent key in the mapping
  Object.entries(mapping).forEach(([fidesKey, googleTypes]) => {
    const hasConsent = !!consent[fidesKey];
    const consentState: GoogleConsentState = hasConsent ? "granted" : "denied";

    // Map to all Google consent types for this Fides key
    googleTypes.forEach((googleType) => {
      googleConsent[googleType] = consentState;
    });
  });

  if (debug) {
    console.log("[Fides Google Consent] Built consent object:", googleConsent);
  }

  return googleConsent as Record<GoogleConsentType, GoogleConsentState>;
};

/**
 * Push consent to Google Consent Mode v2
 */
const pushConsentToGtag = (
  consent: NoticeConsent,
  options: GtagConsentOptions,
): void => {
  const { purposeMapping, debug = false } = options;

  if (debug) {
    console.log("[Fides Google Consent] Pushing consent to gtag:", consent);
  }

  // Check if gtag is available
  if (typeof window.gtag !== "function") {
    if (debug) {
      console.warn(
        "[Fides Google Consent] gtag() not found. Ensure Google Tag Manager or gtag.js is loaded.",
      );
    }
    return;
  }

  // Build Google consent object
  const googleConsent = buildGoogleConsent(consent, purposeMapping, debug);

  try {
    // Update consent via gtag
    window.gtag("consent", "update", googleConsent);

    if (debug) {
      console.log(
        "[Fides Google Consent] Successfully updated gtag consent:",
        googleConsent,
      );
    }
  } catch (error) {
    console.error("[Fides Google Consent] Error calling gtag():", error);
  }
};

/**
 * Get current Google consent state
 */
const getCurrentGoogleConsent = (
  mapping: GtagConsentMapping,
): Record<GoogleConsentType, GoogleConsentState> | null => {
  // Google doesn't provide a public API to read consent state
  // We can only check if gtag exists
  if (typeof window.gtag !== "function") {
    return null;
  }

  // Return all possible consent types based on mapping
  const allTypes = new Set<GoogleConsentType>();
  Object.values(mapping).forEach((types) => {
    types.forEach((type) => allTypes.add(type));
  });

  // We can't read actual state from gtag, so return null
  // Users should rely on Fides consent as source of truth
  return null;
};

/**
 * Initialize Google Consent Mode v2 integration
 *
 * Automatically syncs Fides consent with Google's Consent Mode v2 API.
 *
 * @param options - Configuration options
 * @returns Integration object with diagnostic methods
 *
 * @example
 * ```typescript
 * // Basic usage with default mapping
 * const gtag = Fides.gtagConsent({
 *   purposeMapping: {
 *     analytics: ['analytics_storage'],
 *     advertising: ['ad_storage', 'ad_personalization', 'ad_user_data']
 *   }
 * });
 *
 * // With debug logging
 * const gtag = Fides.gtagConsent({
 *   purposeMapping: { ... },
 *   debug: true
 * });
 * ```
 */
export const gtagConsent = (
  options?: Partial<GtagConsentOptions>,
): GtagConsentIntegration => {
  const finalOptions: GtagConsentOptions = {
    purposeMapping: options?.purposeMapping || DEFAULT_CONSENT_MAPPING,
    debug: options?.debug || false,
  };

  // Subscribe to Fides consent events
  subscribeToConsent((consent) => {
    pushConsentToGtag(consent, finalOptions);
  });

  // Return integration object
  return {
    consent: () => getCurrentGoogleConsent(finalOptions.purposeMapping),
  };
};

