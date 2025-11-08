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
    adobe_mc_orgid?: string;
  }
}

/**
 * Options for Adobe Experience Platform integration
 */
export interface AEPOptions {
  /**
   * Custom mapping of Fides consent keys to Adobe purposes
   * @default { analytics: ['collect', 'measure'], functional: ['personalize'], advertising: ['share'] }
   */
  purposeMapping?: {
    [fidesKey: string]: string[];
  };

  /**
   * Whether to enable debug logging
   * @default false
   */
  debug?: boolean;
}

/**
 * Structure for AEP diagnostic data
 */
export interface AEPDiagnostics {
  timestamp: string;
  alloy?: {
    configured: boolean;
    consent?: any;
    identity?: any;
    config?: any;
  };
  visitor?: {
    configured: boolean;
    marketingCloudVisitorID?: string;
    analyticsVisitorID?: string;
    audienceManagerLocationHint?: string;
    audienceManagerBlob?: string;
    optIn?: any;
    error?: string;
  };
  optIn?: {
    configured: boolean;
    categories?: {
      aa?: string;
      target?: string;
      aam?: string;
      ecid?: string;
    };
    isApproved?: {
      aa?: boolean;
      target?: boolean;
      aam?: boolean;
      ecid?: boolean;
    };
  };
  cookies?: {
    ecid?: string;
    amcv?: string;
    demdex?: string;
    dextp?: string;
    other?: Record<string, string>;
  };
  launch?: {
    configured: boolean;
    property?: string;
    environment?: string;
    buildDate?: string;
  };
  analytics?: {
    configured: boolean;
    reportSuite?: string;
    trackingServer?: string;
    visitorNamespace?: string;
  };
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
    aa?: boolean;
    target?: boolean;
    aam?: boolean;
    configured: boolean;
  };
  summary: {
    analytics: boolean;
    personalization: boolean;
    advertising: boolean;
  };
}

/**
 * Adobe Experience Platform integration API
 */
export interface AEPIntegration {
  /**
   * Get diagnostic information about Adobe configuration
   */
  dump: () => AEPDiagnostics;

  /**
   * Get current Adobe consent state for the user
   * Shows what Adobe has approved/denied
   */
  consent: () => AEPConsentState;
}

/**
 * Default mapping of Fides consent keys to Adobe purposes
 */
const DEFAULT_PURPOSE_MAPPING = {
  analytics: ["collect", "measure"],
  functional: ["personalize"],
  advertising: ["share", "personalize"],
};

/**
 * Map Fides consent to Adobe ECID categories
 */
const ECID_CATEGORY_MAPPING: Record<string, string> = {
  analytics: "aa",
  functional: "target",
  advertising: "aam",
};

/**
 * Push Fides consent to Adobe products
 */
const pushConsentToAdobe = (
  consent: NoticeConsent,
  options?: AEPOptions,
): void => {
  const purposeMapping = options?.purposeMapping || DEFAULT_PURPOSE_MAPPING;
  const debug = options?.debug || false;

  if (debug) {
    console.log("[Fides Adobe] Pushing consent to Adobe:", consent);
  }

  // Check if Adobe is loaded
  const hasAlloy = typeof window.alloy === "function";
  const hasOptIn = !!window.adobe?.optIn;

  if (!hasAlloy && !hasOptIn) {
    if (debug) {
      console.warn(
        "[Fides Adobe] Adobe not detected. Ensure Adobe Web SDK or ECID is loaded.",
      );
    }
    return;
  }

  // Build Adobe Web SDK consent object (Consent v2)
  if (hasAlloy) {
    const adobePurposes = buildAdobePurposes(consent, purposeMapping);

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

      if (debug) {
        console.log("[Fides Adobe] Sent consent to Adobe Web SDK:", {
          purposes: adobePurposes,
        });
      }
    } catch (error) {
      console.error("[Fides Adobe] Error calling alloy.setConsent:", error);
    }
  }

  // Handle legacy ECID Opt-In Service
  if (hasOptIn) {
    try {
      Object.entries(ECID_CATEGORY_MAPPING).forEach(([fidesKey, ecidCat]) => {
        const hasConsent = consent[fidesKey];

        if (hasConsent) {
          window.adobe!.optIn.approve([ecidCat], true);
        } else {
          window.adobe!.optIn.deny([ecidCat], true);
        }
      });

      // Complete the opt-in process
      window.adobe!.optIn.complete();

      if (debug) {
        console.log("[Fides Adobe] Updated ECID Opt-In Service");
      }
    } catch (error) {
      console.error("[Fides Adobe] Error updating ECID Opt-In:", error);
    }
  }
};

/**
 * Build Adobe purpose consent object from Fides consent
 */
function buildAdobePurposes(
  consent: NoticeConsent,
  purposeMapping: Record<string, string[]>,
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

  return purposes;
}

// ============================================================================
// Diagnostic Functions
// ============================================================================

/**
 * Get ECID from cookies
 */
function getECIDFromCookies(): string | undefined {
  const cookies = document.cookie.split("; ");
  const amcvCookie = cookies.find((c) => c.startsWith("AMCV_"));

  if (!amcvCookie) return undefined;

  // Extract ECID from AMCV cookie (format: AMCV_xxx=...MCMID|<ecid>|...)
  const match = amcvCookie.match(/MCMID\|(\d+)\|/);
  return match ? match[1] : undefined;
}

/**
 * Get all Adobe-related cookies
 */
function getAdobeCookies(): AEPDiagnostics["cookies"] {
  const cookies = document.cookie.split("; ");
  const adobeCookies: Record<string, string> = {};

  cookies.forEach((cookie) => {
    const [name, value] = cookie.split("=");
    if (
      name.startsWith("AMCV_") ||
      name === "demdex" ||
      name === "dextp" ||
      name.startsWith("s_")
    ) {
      adobeCookies[name] = value;
    }
  });

  return {
    ecid: getECIDFromCookies(),
    amcv: cookies.find((c) => c.startsWith("AMCV_"))?.split("=")[1],
    demdex: cookies
      .find((c) => c.startsWith("demdex="))
      ?.split("=")[1],
    dextp: cookies
      .find((c) => c.startsWith("dextp="))
      ?.split("=")[1],
    other: adobeCookies,
  };
}

/**
 * Get Adobe Web SDK (Alloy) diagnostics
 */
function getAlloyDiagnostics(): AEPDiagnostics["alloy"] {
  if (typeof window.alloy !== "function") {
    return { configured: false };
  }

  const diagnostics: AEPDiagnostics["alloy"] = {
    configured: true,
  };

  // Try to get consent state (may not be available in all versions)
  try {
    // Note: alloy doesn't expose consent state directly, would need to track it ourselves
    diagnostics.consent = "unavailable - tracking not implemented";
  } catch (e) {
    // Silently handle
  }

  return diagnostics;
}

/**
 * Get Visitor API (ECID) diagnostics
 */
function getVisitorDiagnostics(): AEPDiagnostics["visitor"] {
  if (!window.Visitor) {
    return { configured: false };
  }

  // Get visitor instance - requires adobe_mc_orgid
  let visitor;
  if (typeof window.Visitor.getInstance === "function" && window.adobe_mc_orgid) {
    try {
      visitor = window.Visitor.getInstance(window.adobe_mc_orgid);
    } catch (error) {
      return {
        configured: false,
        error: error instanceof Error ? error.message : "Failed to get Visitor instance",
      };
    }
  } else {
    return {
      configured: false,
      error: window.adobe_mc_orgid
        ? "Visitor.getInstance not available"
        : "adobe_mc_orgid not set",
    };
  }

  const diagnostics: AEPDiagnostics["visitor"] = {
    configured: true,
  };

  try {
    // Get Marketing Cloud Visitor ID (ECID)
    if (typeof visitor.getMarketingCloudVisitorID === "function") {
      diagnostics.marketingCloudVisitorID = visitor.getMarketingCloudVisitorID();
    }

    // Get Analytics Visitor ID
    if (typeof visitor.getAnalyticsVisitorID === "function") {
      diagnostics.analyticsVisitorID = visitor.getAnalyticsVisitorID();
    }

    // Get Audience Manager Location Hint
    if (typeof visitor.getAudienceManagerLocationHint === "function") {
      diagnostics.audienceManagerLocationHint = visitor.getAudienceManagerLocationHint();
    }

    // Get Audience Manager Blob
    if (typeof visitor.getAudienceManagerBlob === "function") {
      diagnostics.audienceManagerBlob = visitor.getAudienceManagerBlob();
    }

    // Get OptIn state from Visitor API
    if (visitor.optIn) {
      diagnostics.optIn = {
        isApproved: {
          aa: visitor.optIn.isApproved?.(visitor.optIn.Categories?.AA),
          target: visitor.optIn.isApproved?.(visitor.optIn.Categories?.TARGET),
          aam: visitor.optIn.isApproved?.(visitor.optIn.Categories?.AAM),
          ecid: visitor.optIn.isApproved?.(visitor.optIn.Categories?.ECID),
        },
      };
    }
  } catch (e) {
    // Silently handle errors
  }

  return diagnostics;
}

/**
 * Get OptIn Service diagnostics
 */
function getOptInDiagnostics(): AEPDiagnostics["optIn"] {
  if (!window.adobe?.optIn) {
    return { configured: false };
  }

  const { optIn } = window.adobe;
  const diagnostics: AEPDiagnostics["optIn"] = {
    configured: true,
    categories: {},
    isApproved: {},
  };

  try {
    // Get categories
    const categories = ["aa", "target", "aam", "ecid"] as const;

    categories.forEach((cat) => {
      const upperCat = cat.toUpperCase();
      if (optIn.Categories?.[upperCat]) {
        diagnostics.categories![cat] = optIn.Categories[upperCat];

        // Check if approved
        if (typeof optIn.isApproved === "function") {
          diagnostics.isApproved![cat] = optIn.isApproved(
            optIn.Categories[upperCat],
          );
        }
      }
    });
  } catch (e) {
    // Silently handle
  }

  return diagnostics;
}

/**
 * Get Adobe Launch diagnostics
 */
function getLaunchDiagnostics(): AEPDiagnostics["launch"] {
  if (!window._satellite) {
    return { configured: false };
  }

  const diagnostics: AEPDiagnostics["launch"] = {
    configured: true,
  };

  try {
    if (window._satellite.property) {
      diagnostics.property = window._satellite.property.name;
    }
    if (window._satellite.environment) {
      diagnostics.environment = window._satellite.environment.stage;
    }
    if (window._satellite.buildInfo) {
      diagnostics.buildDate = window._satellite.buildInfo.buildDate;
    }
  } catch (e) {
    // Silently handle
  }

  return diagnostics;
}

/**
 * Get Adobe Analytics diagnostics
 */
function getAnalyticsDiagnostics(): AEPDiagnostics["analytics"] {
  if (!window.s) {
    return { configured: false };
  }

  const diagnostics: AEPDiagnostics["analytics"] = {
    configured: true,
  };

  try {
    if (window.s.account) {
      diagnostics.reportSuite = window.s.account;
    }
    if (window.s.trackingServer) {
      diagnostics.trackingServer = window.s.trackingServer;
    }
    if (window.s.visitorNamespace) {
      diagnostics.visitorNamespace = window.s.visitorNamespace;
    }
  } catch (e) {
    // Silently handle
  }

  return diagnostics;
}

/**
 * Get current Adobe consent state
 * Checks both Adobe Web SDK and ECID Opt-In Service
 */
function getAdobeConsentState(): AEPConsentState {
  const state: AEPConsentState = {
    timestamp: new Date().toISOString(),
    summary: {
      analytics: false,
      personalization: false,
      advertising: false,
    },
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
      const aaApproved = optIn.isApproved?.(optIn.Categories?.AA);
      const targetApproved = optIn.isApproved?.(optIn.Categories?.TARGET);
      const aamApproved = optIn.isApproved?.(optIn.Categories?.AAM);

      state.ecidOptIn = {
        configured: true,
        aa: aaApproved,
        target: targetApproved,
        aam: aamApproved,
      };

      // Build summary from ECID state
      state.summary.analytics = !!aaApproved;
      state.summary.personalization = !!targetApproved;
      state.summary.advertising = !!aamApproved;
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
 * - Adobe Web SDK (modern)
 * - ECID Opt-In Service (legacy)
 *
 * @param options - Configuration options
 * @returns Integration API with diagnostic utilities
 *
 * @example
 * ```javascript
 * // Basic usage
 * const aep = Fides.aep();
 *
 * // With custom purpose mapping
 * const aep = Fides.aep({
 *   purposeMapping: {
 *     analytics: ['collect', 'measure'],
 *     marketing: ['personalize', 'share']
 *   }
 * });
 *
 * // Get diagnostics
 * const diagnostics = aep.dump();
 * console.log(diagnostics.visitor.marketingCloudVisitorID);
 * ```
 */
export const aep = (options?: AEPOptions): AEPIntegration => {
  // Subscribe to Fides consent events using shared helper
  subscribeToConsent((consent) => pushConsentToAdobe(consent, options));

  // Return integration API
  return {
    dump: (): AEPDiagnostics => {
      return {
        timestamp: new Date().toISOString(),
        alloy: getAlloyDiagnostics(),
        visitor: getVisitorDiagnostics(),
        optIn: getOptInDiagnostics(),
        cookies: getAdobeCookies(),
        launch: getLaunchDiagnostics(),
        analytics: getAnalyticsDiagnostics(),
      };
    },
    consent: (): AEPConsentState => {
      return getAdobeConsentState();
    },
  };
};
