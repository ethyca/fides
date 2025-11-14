/**
 * Adobe Experience Platform (AEP) Integration
 *
 * Syncs Fides consent to Adobe Experience Platform products:
 * - Adobe Web SDK (Consent v2) - modern
 * - Adobe ECID Opt-In Service (AppMeasurement) - legacy
 */

import { NoticeConsent } from "../lib/consent-types";
import { subscribeToConsent } from "./integration-utils";

declare global {
  interface Window {
    alloy?: any;
    Visitor?: any;
    s?: any;
    adobe?: {
      optIn?: any;
      target?: any;
      analytics?: any;
    };
    _satellite?: any;
  }
}

/**
 * Options for Adobe Experience Platform integration
 */
export interface AEPOptions {
  /**
   * Custom mapping of Fides consent keys to Adobe Web SDK purposes
   * Used for Adobe Web SDK (Alloy) consent API
   * @default { analytics: ['collect', 'measure'], functional: ['personalize'], advertising: ['share'] }
   */
  purposeMapping?: {
    [fidesKey: string]: string[];
  };

  /**
   * Custom mapping of Fides consent keys to Adobe ECID Opt-In categories
   * Used for legacy Adobe ECID Opt-In Service (AppMeasurement)
   * Categories: 'aa' (Analytics), 'target' (Target), 'aam' (Audience Manager),
   * 'adcloud' (AdCloud), 'campaign' (Campaign), 'ecid' (ECID), 'livefyre' (Livefyre), 'mediaaa' (Media Analytics)
   * @default { analytics: ['aa'], functional: ['target'], advertising: ['aam'] }
   */
  ecidMapping?: {
    [fidesKey: string]: string[];
  };

  /**
   * Whether to enable debug logging
   * @default false
   */
  debug?: boolean;
}

/**
 * Adobe consent state for the current user
 */
export interface AEPConsentState {
  timestamp: string;
  alloy?: {
    purposes?: Record<string, "in" | "out">;
    configured: boolean;
  };
  ecidOptIn?: {
    configured: boolean;
    categories?: Record<string, boolean>; // Dynamic: all Adobe categories (aa, target, aam, adcloud, campaign, etc.)
  };
}

/**
 * Adobe Experience Platform integration API
 */
export interface AEPIntegration {
  /**
   * Get current Adobe consent state for the user
   * Shows what Adobe has approved/denied
   */
  consent: () => AEPConsentState;
}

/**
 * Default mapping of Fides consent keys to Adobe purposes
 *
 * Adobe purposes:
 * - collect, measure → Analytics (aa)
 * - personalize → Target (target)
 * - share → Audience Manager (aam)
 *
 * Customize this by passing purposeMapping to Fides.aep()
 */
const DEFAULT_PURPOSE_MAPPING = {
  analytics: ["collect", "measure"],
  functional: ["personalize"],
  advertising: ["share", "personalize"],
};

/**
 * Default mapping of Fides consent keys to Adobe ECID categories
 *
 * Maps to legacy ECID Opt-In Service categories:
 * - analytics → aa (Analytics)
 * - functional → target (Target)
 * - advertising → aam (Audience Manager)
 */
const DEFAULT_ECID_MAPPING = {
  analytics: ["aa"],
  functional: ["target"],
  advertising: ["aam"],
};

/**
 * Build Adobe purpose consent object from Fides consent
 */
function buildAdobePurposes(
  consent: NoticeConsent,
  purposeMapping: Record<string, string[]>,
  debug: boolean = false,
): Record<string, "in" | "out"> {
  const purposes: Record<string, "in" | "out"> = {};

  // Map each Fides consent key to Adobe purposes
  Object.entries(purposeMapping).forEach(([fidesKey, adobePurposes]) => {
    const hasConsent = !!consent[fidesKey];
    const value = hasConsent ? "in" : "out";

    adobePurposes.forEach((purpose) => {
      purposes[purpose] = value;
    });
  });

  if (debug) {
    // eslint-disable-next-line no-console
    console.log("[Fides Adobe] Purpose mapping result:", purposes);
  }

  return purposes;
}

/**
 * Push Fides consent to Adobe products
 */
const pushConsentToAdobe = (
  consent: NoticeConsent,
  options?: AEPOptions,
): void => {
  const purposeMapping =
    options?.purposeMapping && Object.keys(options.purposeMapping).length > 0
      ? options.purposeMapping
      : DEFAULT_PURPOSE_MAPPING;
  const debug = options?.debug || false;

  fidesDebugger("[Fides Adobe] Pushing consent to Adobe:", consent);

  // Check if Adobe is loaded
  const hasAlloy = typeof window.alloy === "function";
  const hasOptIn = !!window.adobe?.optIn;

  if (!hasAlloy && !hasOptIn) {
    if (debug) {
      // eslint-disable-next-line no-console
      console.warn(
        "[Fides Adobe] Adobe not detected. Ensure Adobe Web SDK or ECID is loaded.",
      );
    }
    return;
  }

  // Build Adobe Web SDK consent object (Consent v2)
  if (hasAlloy) {
    const adobePurposes = buildAdobePurposes(consent, purposeMapping, debug);

    try {
      window.alloy("setConsent", {
        consent: [
          {
            standard: "Adobe",
            version: "2.0",
            value: adobePurposes,
          },
        ],
      });

      fidesDebugger("[Fides Adobe] Sent consent to Adobe Web SDK:", {
        purposes: adobePurposes,
      });
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error("[Fides Adobe] Error calling alloy.setConsent:", error);
    }
  }

  // Handle legacy ECID Opt-In Service
  if (hasOptIn) {
    try {
      // Dynamic approvals: support all Adobe categories, not just hardcoded ones
      const ecidApprovals: Record<string, boolean> = {};
      const ecidMapping =
        options?.ecidMapping && Object.keys(options.ecidMapping).length > 0
          ? options.ecidMapping
          : DEFAULT_ECID_MAPPING;

      // Map Fides consent to ECID categories
      Object.entries(ecidMapping).forEach(([fidesKey, ecidCategories]) => {
        const hasConsent = !!consent[fidesKey];

        ecidCategories.forEach((category) => {
          // Use OR logic: if ANY Fides key grants consent to a category, approve it
          ecidApprovals[category] = ecidApprovals[category] || hasConsent;
        });
      });

      fidesDebugger(
        "[Fides Adobe] ECID approvals computed from ecidMapping:",
          ecidApprovals,
      );

      // Dynamically apply approvals/denials for all categories
      const categories = window.adobe?.optIn?.Categories;

      // Get all available category constants (e.g., ANALYTICS -> "aa", TARGET -> "target")
      Object.entries(categories || {}).forEach(([, categoryId]) => {
        if (typeof categoryId === "string") {
          // Check if we have an approval decision for this category
          if (ecidApprovals[categoryId] === true) {
            window.adobe!.optIn.approve(categoryId);
          } else if (ecidApprovals[categoryId] === false) {
            window.adobe!.optIn.deny(categoryId);
          }
          // If undefined, we don't touch it (no mapping provided)
        }
      });

      fidesDebugger(
        "[Fides Adobe] Updated ECID Opt-In Service:",
          ecidApprovals,
      );
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error("[Fides Adobe] Error updating ECID Opt-In:", error);
    }
  }
};

/**
 * Get current Adobe consent state
 * Checks both Adobe Web SDK and ECID Opt-In Service
 */
function getAdobeConsentState(): AEPConsentState {
  const state: AEPConsentState = {
    timestamp: new Date().toISOString(),
  };

  // Check Adobe Web SDK (Alloy) - Note: alloy doesn't expose consent state directly
  // We'd need to track what we sent to it
  if (typeof window.alloy === "function") {
    state.alloy = {
      configured: true,
      // Adobe Web SDK doesn't expose consent state for reading
      // We only know what we set via setConsent()
      purposes: undefined,
    };
  } else {
    state.alloy = {
      configured: false,
    };
  }

  // Check ECID Opt-In Service
  if (window.adobe?.optIn) {
    const { optIn } = window.adobe;

    try {
      // Dynamically check all Adobe categories
      const categories: Record<string, boolean> = {};

      if (optIn.Categories) {
        // Iterate through all available categories (ANALYTICS, TARGET, AAM, ADCLOUD, etc.)
        Object.entries(optIn.Categories).forEach(([, categoryId]) => {
          if (
            typeof categoryId === "string" &&
            typeof optIn.isApproved === "function"
          ) {
            categories[categoryId] = optIn.isApproved(categoryId);
          }
        });
      }

      state.ecidOptIn = {
        configured: true,
        categories,
      };
    } catch (e) {
      state.ecidOptIn = {
        configured: true,
      };
    }
  } else {
    state.ecidOptIn = {
      configured: false,
    };
  }

  return state;
}

// ============================================================================
// Public API
// ============================================================================

/**
 * Initialize Adobe Experience Platform integration.
 *
 * Automatically syncs Fides consent to Adobe products:
 * - Adobe Web SDK (modern Alloy SDK)
 * - ECID Opt-In Service (legacy AppMeasurement)
 *
 * @param options - Configuration options
 * @returns Integration API with diagnostic utilities
 *
 * @example
 * ```javascript
 * // Basic usage with defaults
 * const aep = Fides.aep();
 * // Uses default mappings: analytics->aa, functional->target, advertising->aam
 *
 * // Custom mappings for both systems
 * const aep = Fides.aep({
 *   purposeMapping: {
 *     analytics: ['collect', 'measure'],
 *     marketing: ['personalize', 'share']
 *   },
 *   ecidMapping: {
 *     analytics: ['aa'],
 *     marketing: ['target', 'aam']
 *   }
 * });
 *
 * // Check current consent state
 * const state = aep.consent();
 * console.log(state.ecidOptIn?.categories); // { aa: true, target: false, aam: true, ... }
 * ```
 */
export const aep = (options?: AEPOptions): AEPIntegration => {
  // Subscribe to Fides consent events using shared helper
  subscribeToConsent((consent) => pushConsentToAdobe(consent, options));

  // Return integration API
  return {
    consent: (): AEPConsentState => {
      return getAdobeConsentState();
    },
  };
};
