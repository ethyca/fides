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
export type GcmConsentMapping = Record<string, GoogleConsentType[]>;

/**
 * Options for Google Consent Mode integration
 */
export interface GcmOptions {
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
  purposeMapping: GcmConsentMapping;
}

/**
 * Google Consent Mode integration object
 */
export interface GcmIntegration {
  /**
   * Get current Google consent state
   */
  consent: () => Record<GoogleConsentType, GoogleConsentState> | null;
}

/**
 * Default mapping from Fides consent to Google Consent Mode types
 *
 * Includes comprehensive mappings for common Fides notice keys:
 * - analytics: For analytics and measurement
 * - advertising: For advertising and remarketing
 * - functional: For functionality and personalization features
 * - data_sales_and_sharing: For data sales and third-party sharing
 * - marketing: For marketing and advertising purposes
 */
const DEFAULT_CONSENT_MAPPING: GcmConsentMapping = {
  analytics: ["analytics_storage"],
  advertising: ["ad_storage", "ad_personalization", "ad_user_data"],
  functional: ["functionality_storage", "personalization_storage"],
  data_sales_and_sharing: ["ad_storage", "ad_personalization", "ad_user_data"],
  marketing: ["ad_storage", "ad_personalization", "ad_user_data"],
};

/**
 * Build Google Consent Mode object from Fides consent
 *
 * Only processes consent keys that exist in both the mapping AND the Fides consent object.
 * This allows the integration to work even if not all mapped keys are configured in Fides.
 */
const buildGoogleConsent = (
  consent: NoticeConsent,
  mapping: GcmConsentMapping,
): Record<GoogleConsentType, GoogleConsentState> => {
  const googleConsent: Partial<Record<GoogleConsentType, GoogleConsentState>> =
    {};

  // For each Fides consent key in the mapping
  Object.entries(mapping).forEach(([fidesKey, googleTypes]) => {
    // Only process if this consent key exists in the Fides consent object
    // This allows graceful handling when not all keys are configured
    if (fidesKey in consent) {
      const hasConsent = !!consent[fidesKey];
      const consentState: GoogleConsentState = hasConsent
        ? "granted"
        : "denied";

      // Map to all Google consent types for this Fides key
      googleTypes.forEach((googleType) => {
        googleConsent[googleType] = consentState;
      });

      fidesDebugger(
        `[Fides GCM] Mapped ${fidesKey}=${hasConsent} to ${googleTypes.join(", ")}=${consentState}`,
      );
    } else {
      fidesDebugger(
        `[Fides GCM] Skipping ${fidesKey} (not present in Fides consent)`,
      );
    }
  });

  fidesDebugger("[Fides GCM] Built consent object:", googleConsent);

  return googleConsent as Record<GoogleConsentType, GoogleConsentState>;
};

/**
 * Push consent to Google Consent Mode v2
 */
const pushConsentToGtag = (
  consent: NoticeConsent,
  options: GcmOptions,
): void => {
  const { purposeMapping } = options;

  fidesDebugger("[Fides GCM] Pushing consent to gtag:", consent);

  // Check if gtag is available
  if (typeof window.gtag !== "function") {
    fidesDebugger(
      "[Fides GCM] gtag() not found. Ensure Google Tag Manager or gtag.js is loaded.",
    );
    return;
  }

  // Build Google consent object
  const googleConsent = buildGoogleConsent(consent, purposeMapping);

  // Only update if we have consent values to send
  if (Object.keys(googleConsent).length === 0) {
    fidesDebugger(
      "[Fides GCM] No matching consent keys found, skipping gtag update",
    );
    return;
  }

  try {
    // Update consent via gtag
    window.gtag("consent", "update", googleConsent);

    fidesDebugger(
      "[Fides GCM] Successfully updated gtag consent:",
      googleConsent,
    );
  } catch (error) {
    fidesDebugger("[Fides GCM] Error calling gtag():", error);
  }
};

/**
 * Get current Google consent state
 */
const getCurrentGoogleConsent = (
  mapping: GcmConsentMapping,
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
 * The integration will only process consent keys that are present in both
 * the purposeMapping and the Fides consent object, allowing it to work
 * gracefully even if not all mapped keys are configured in Fides.
 *
 * @param options - Configuration options
 * @returns Integration object with diagnostic methods
 *
 * @example
 * ```typescript
 * // Basic usage with default mapping
 * const gcm = Fides.gcm();
 *
 * // With custom purpose mapping
 * const gcm = Fides.gcm({
 *   purposeMapping: {
 *     analytics: ['analytics_storage'],
 *     advertising: ['ad_storage', 'ad_personalization', 'ad_user_data']
 *   }
 * });
 * ```
 */
export const gcm = (options?: Partial<GcmOptions>): GcmIntegration => {
  const finalOptions: GcmOptions = {
    purposeMapping:
      options?.purposeMapping && Object.keys(options.purposeMapping).length > 0
        ? options.purposeMapping
        : DEFAULT_CONSENT_MAPPING,
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
