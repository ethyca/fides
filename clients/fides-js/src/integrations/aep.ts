/**
 * Adobe Experience Platform (AEP) Integration
 *
 * Syncs Fides consent to Adobe Experience Platform products:
 * - Adobe Web SDK (Consent v2) - modern
 * - Adobe ECID Opt-In Service (AppMeasurement) - legacy
 */

import { NoticeConsent } from "../lib/consent-types";
import { OneTrustProvider } from "../lib/consent-migration/onetrust";
import { subscribeToConsent } from "./integration-utils";

/**
 * Standard OneTrust category to Fides notice mapping
 * Used for reading OneTrust consent during migration
 */
const DEFAULT_ONETRUST_TO_FIDES_MAPPING: Record<string, string> = {
  C0001: "essential",
  C0002: "performance",
  C0003: "functional",
  C0004: "advertising",
};

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
  fides?: {
    configured: boolean;
    consentKeys?: string[];
    currentConsent?: Record<string, boolean>;
    suggestedMapping?: Record<string, string[]>;
  };
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
  oneTrust?: {
    detected: boolean;
    activeGroups?: string[];
    categoriesConsent?: Record<string, boolean>;
    rawCookieString?: string;
    rawCookieValue?: string;
    parseError?: string;
    adobeIntegration?: {
      detected: boolean;
      mapping?: Record<string, string[]>;
    };
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
 * Suggestion result from analyzing OneTrust environment
 */
export interface AEPSuggestion {
  success: boolean;
  error?: string;
  oneTrustCategories: string[];
  suggestedFidesNotices: {
    name: string;
    description: string;
    adobePurposes: string[];
    oneTrustCategory: string;
  }[];
  purposeMapping: Record<string, string[]>;
  fidesHasMatchingKeys: boolean;
  matchedKeys: string[];
  missingKeys: string[];
  recommendedAction: string;
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
      // Build ECID mapping from purposeMapping
      // Map Fides keys → Adobe purposes → ECID categories
      const ecidApprovals: { aa: boolean; target: boolean; aam: boolean } = {
        aa: false,
        target: false,
        aam: false,
      };

      // Check each Fides consent key in the mapping
      Object.entries(purposeMapping).forEach(([fidesKey, adobePurposes]) => {
        const hasConsent = !!consent[fidesKey];

        adobePurposes.forEach((purpose) => {
          // Map Adobe purposes to ECID categories
          if (purpose === "collect" || purpose === "measure") {
            ecidApprovals.aa = ecidApprovals.aa || hasConsent;
          }
          if (purpose === "personalize") {
            ecidApprovals.target = ecidApprovals.target || hasConsent;
          }
          if (purpose === "share") {
            ecidApprovals.aam = ecidApprovals.aam || hasConsent;
          }
        });
      });

      // Apply approvals/denials
      if (ecidApprovals.aa) {
        window.adobe!.optIn.approve(["aa"], true);
      } else {
        window.adobe!.optIn.deny(["aa"], true);
      }

      if (ecidApprovals.target) {
        window.adobe!.optIn.approve(["target"], true);
      } else {
        window.adobe!.optIn.deny(["target"], true);
      }

      if (ecidApprovals.aam) {
        window.adobe!.optIn.approve(["aam"], true);
      } else {
        window.adobe!.optIn.deny(["aam"], true);
      }

      // Complete the opt-in process
      window.adobe!.optIn.complete();

      if (debug) {
        console.log("[Fides Adobe] Updated ECID Opt-In Service:", ecidApprovals);
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
  debug: boolean = false,
): Record<string, "in" | "out"> {
  const purposes: Record<string, "in" | "out"> = {};
  const matchedKeys: string[] = [];
  const unmatchedKeys: string[] = [];

  // Map each Fides consent key to Adobe purposes
  Object.entries(purposeMapping).forEach(([fidesKey, adobePurposes]) => {
    const hasConsent = !!consent[fidesKey];
    const value = hasConsent ? "in" : "out";

    if (consent[fidesKey] !== undefined) {
      matchedKeys.push(fidesKey);
    }

    adobePurposes.forEach((purpose) => {
      purposes[purpose] = value;
    });
  });

  // Check for Fides consent keys that aren't in the mapping
  Object.keys(consent).forEach((key) => {
    if (!purposeMapping[key]) {
      unmatchedKeys.push(key);
    }
  });

  if (debug) {
    console.log("[Fides Adobe] Purpose mapping:", {
      fidesConsentKeys: Object.keys(consent),
      mappingKeys: Object.keys(purposeMapping),
      matchedKeys,
      unmatchedKeys: unmatchedKeys.length > 0 ? unmatchedKeys : "none",
      resultingPurposes: purposes,
    });

    if (unmatchedKeys.length > 0) {
      console.warn(
        `[Fides Adobe] Found ${unmatchedKeys.length} consent key(s) not in purposeMapping:`,
        unmatchedKeys,
        "\nTo map these keys, pass a custom purposeMapping option to Fides.aep()",
      );
    }
  }

  return purposes;
}

// ============================================================================
// Diagnostic Functions
// ============================================================================

/**
 * Suggest Adobe purpose mapping based on Fides consent key names
 */
function suggestPurposeMapping(
  consentKeys: string[],
): Record<string, string[]> {
  const suggestions: Record<string, string[]> = {};

  consentKeys.forEach((key) => {
    const lowerKey = key.toLowerCase();

    // Analytics-related keys
    if (
      lowerKey.includes("analytic") ||
      lowerKey.includes("measurement") ||
      lowerKey.includes("performance")
    ) {
      suggestions[key] = ["collect", "measure"];
    }
    // Marketing/Advertising keys
    else if (
      lowerKey.includes("marketing") ||
      lowerKey.includes("advertising") ||
      lowerKey.includes("ad_")
    ) {
      suggestions[key] = ["personalize", "share"];
    }
    // Data sales/sharing keys
    else if (
      lowerKey.includes("sale") ||
      lowerKey.includes("sharing") ||
      lowerKey.includes("third_party")
    ) {
      suggestions[key] = ["share"];
    }
    // Personalization/Functional keys
    else if (
      lowerKey.includes("personali") ||
      lowerKey.includes("functional") ||
      lowerKey.includes("preference")
    ) {
      suggestions[key] = ["personalize"];
    }
    // Essential/Required keys - typically not mapped
    else if (
      lowerKey.includes("essential") ||
      lowerKey.includes("necessary") ||
      lowerKey.includes("required")
    ) {
      // Skip essential cookies - they're always allowed
    }
    // Default fallback for unknown keys
    else {
      suggestions[key] = ["collect"]; // Conservative default
    }
  });

  return suggestions;
}

/**
 * Get Fides consent diagnostics
 */
export function getFidesDiagnostics(): AEPDiagnostics["fides"] {
  const diagnostics: AEPDiagnostics["fides"] = {
    configured: false,
  };

  if (window.Fides && window.Fides.consent) {
    const consentKeys = Object.keys(window.Fides.consent);
    diagnostics.configured = true;
    diagnostics.consentKeys = consentKeys;

    // Convert consent values to boolean for diagnostics
    const currentConsent: Record<string, boolean> = {};
    Object.entries(window.Fides.consent).forEach(([key, value]) => {
      // Handle both boolean and UserConsentPreference types
      currentConsent[key] = !!value && value !== "opt_out";
    });
    diagnostics.currentConsent = currentConsent;
    diagnostics.suggestedMapping = suggestPurposeMapping(consentKeys);
  }

  return diagnostics;
}

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
export function getAdobeCookies(): AEPDiagnostics["cookies"] {
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
export function getAlloyDiagnostics(): AEPDiagnostics["alloy"] {
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
export function getVisitorDiagnostics(): AEPDiagnostics["visitor"] {
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
export function getOptInDiagnostics(): AEPDiagnostics["optIn"] {
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
export function getLaunchDiagnostics(): AEPDiagnostics["launch"] {
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
export function getAnalyticsDiagnostics(): AEPDiagnostics["analytics"] {
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
 * Get OneTrust diagnostics including Adobe integration
 */
export function getOneTrustDiagnostics(): AEPDiagnostics["oneTrust"] {
  const diagnostics: AEPDiagnostics["oneTrust"] = {
    detected: false,
  };

  // Check for OptanonConsent cookie
  const cookies = document.cookie.split("; ");
  const otCookie = cookies.find((c) => c.startsWith("OptanonConsent="));

  if (!otCookie) {
    return diagnostics;
  }

  diagnostics.detected = true;
  diagnostics.rawCookieString = otCookie.substring(0, 300); // Full cookie string for debugging

  try {
    // Parse OptanonConsent cookie
    // Format: "OptanonConsent=value" where value may contain '=' characters
    const firstEquals = otCookie.indexOf("=");
    const cookieValue = decodeURIComponent(otCookie.substring(firstEquals + 1));
    diagnostics.rawCookieValue = cookieValue.substring(0, 200); // Decoded value

    // Parse cookie as key-value pairs (format: key1=value1&key2=value2)
    const params: Record<string, string> = {};
    cookieValue.split("&").forEach((pair) => {
      const [key, value] = pair.split("=");
      if (key && value !== undefined) {
        params[key] = value;
      }
    });

    // Get active groups (e.g., "C0001,C0002,C0003")
    const groups = params.groups;
    if (!groups) {
      const availableKeys = Object.keys(params).join(", ");
      diagnostics.parseError = `No 'groups' parameter found. Available keys: [${availableKeys}]`;
    } else {
      const activeGroups: string[] = [];
      const categoriesConsent: Record<string, boolean> = {};

      // Parse groups format: "C0001:1,C0002:0,C0003:1,C0004:1"
      groups.split(",").forEach((group) => {
        const [category, status] = group.split(":");
        if (!category || !status) {
          diagnostics.parseError = `Invalid group format: "${group}"`;
          return;
        }
        const isActive = status === "1";
        if (isActive) {
          activeGroups.push(category);
        }
        categoriesConsent[category] = isActive;
      });

      if (Object.keys(categoriesConsent).length > 0) {
        diagnostics.activeGroups = activeGroups;
        diagnostics.categoriesConsent = categoriesConsent;
      }
    }
  } catch (e) {
    diagnostics.parseError = `Failed to parse OptanonConsent: ${e instanceof Error ? e.message : String(e)}`;
  }

  // Check for OneTrust's Adobe integration
  // OneTrust typically stores Adobe mappings in window.OneTrust or similar
  diagnostics.adobeIntegration = {
    detected: false,
  };

  // Standard OneTrust → Adobe category mappings
  // Based on OneTrust's Adobe Experience Cloud integration
  const standardOTtoAdobeMapping: Record<string, string[]> = {
    C0001: [], // Strictly Necessary - not mapped (always on)
    C0002: ["collect", "measure"], // Performance/Analytics → Adobe Analytics
    C0003: ["personalize"], // Functional → Adobe Target
    C0004: ["personalize", "share"], // Targeting/Advertising → Target + AAM
  };

  if (diagnostics.activeGroups && diagnostics.activeGroups.length > 0) {
    diagnostics.adobeIntegration.detected = true;
    diagnostics.adobeIntegration.mapping = standardOTtoAdobeMapping;
  }

  return diagnostics;
}

/**
 * Generate suggestion for Fides notice configuration based on OneTrust
 * ONLY works if OneTrust is actually present. No fallbacks.
 */
export function generateAEPSuggestion(): AEPSuggestion {
  const otDiagnostics = getOneTrustDiagnostics();
  const fidesDiagnostics = getFidesDiagnostics();

  // Must have OneTrust detected
  if (!otDiagnostics || !otDiagnostics.detected) {
    return {
      success: false,
      error:
        "❌ OneTrust not detected. suggest() requires OptanonConsent cookie to analyze categories. Either load OneTrust on this page or use Fides.aep() with a manual purposeMapping.",
      oneTrustCategories: [],
      suggestedFidesNotices: [],
      purposeMapping: {},
      fidesHasMatchingKeys: false,
      matchedKeys: [],
      missingKeys: [],
      recommendedAction:
        "Load OneTrust on this page or manually configure Fides.aep({ purposeMapping: {...} })",
    };
  }

  // OneTrust detected but failed to parse categories
  if (!otDiagnostics.categoriesConsent) {
    const parseError = otDiagnostics.parseError || "Unknown parse error";
    const rawCookie = otDiagnostics.rawCookieValue
      ? `\nCookie value (first 200 chars): ${otDiagnostics.rawCookieValue}`
      : "";

    return {
      success: false,
      error: `❌ OneTrust detected but failed to parse categories.\nError: ${parseError}${rawCookie}\n\nRun aep.dump().oneTrust to see full diagnostic data.`,
      oneTrustCategories: [],
      suggestedFidesNotices: [],
      purposeMapping: {},
      fidesHasMatchingKeys: false,
      matchedKeys: [],
      missingKeys: [],
      recommendedAction: `Fix OptanonConsent cookie format or use Fides.aep({ purposeMapping: {...} }) manually`,
    };
  }

  // Standard OneTrust → Adobe mappings (but we'll use whatever categories they actually have)
  const standardOTtoAdobeMapping: Record<string, string[]> = {
    C0001: [], // Strictly Necessary - not mapped
    C0002: ["collect", "measure"], // Performance/Analytics
    C0003: ["personalize"], // Functional
    C0004: ["personalize", "share"], // Advertising
  };

  // Standard category descriptions
  const categoryDescriptions: Record<string, string> = {
    C0001: "Strictly Necessary / Required Cookies",
    C0002: "Performance Cookies / Analytics",
    C0003: "Functional Cookies / Personalization",
    C0004: "Targeting Cookies / Advertising",
  };

  // Get ACTUAL categories from OneTrust (not assumptions)
  const actualCategories = Object.keys(otDiagnostics.categoriesConsent);

  if (actualCategories.length === 0) {
    return {
      success: false,
      error:
        "❌ OneTrust cookie found but no categories parsed. Check OptanonConsent cookie format.",
      oneTrustCategories: [],
      suggestedFidesNotices: [],
      purposeMapping: {},
      fidesHasMatchingKeys: false,
      matchedKeys: [],
      missingKeys: [],
      recommendedAction:
        "Verify OptanonConsent cookie contains category data (groups parameter)",
    };
  }

  // Map each actual category to Fides notice
  const suggestedNotices = actualCategories.map((category) => {
    // Convert category to suggested Fides notice name
    // C0001 → essential, C0002 → performance, etc.
    const categoryNum = category.match(/C(\d+)/)?.[1];
    const noticeNames: Record<string, string> = {
      "0001": "essential",
      "0002": "performance",
      "0003": "functional",
      "0004": "advertising",
    };
    const suggestedName =
      noticeNames[categoryNum || ""] || category.toLowerCase();

    return {
      name: suggestedName,
      description:
        categoryDescriptions[category] ||
        `OneTrust Category ${category}`,
      adobePurposes: standardOTtoAdobeMapping[category] || [],
      oneTrustCategory: category,
    };
  });

  // Build purpose mapping (exclude essential/empty mappings)
  const purposeMapping: Record<string, string[]> = {};
  suggestedNotices.forEach((notice) => {
    if (notice.adobePurposes.length > 0) {
      purposeMapping[notice.name] = notice.adobePurposes;
    }
  });

  // Check if Fides already has matching keys
  const fidesKeys = (fidesDiagnostics && fidesDiagnostics.consentKeys) || [];
  const suggestedKeys = suggestedNotices.map((n) => n.name);
  const matchedKeys = suggestedKeys.filter((key) => fidesKeys.includes(key));
  const missingKeys = suggestedKeys.filter((key) => !fidesKeys.includes(key));

  const allMatched = matchedKeys.length === suggestedKeys.length;

  return {
    success: true,
    oneTrustCategories: actualCategories,
    suggestedFidesNotices: suggestedNotices,
    purposeMapping,
    fidesHasMatchingKeys: matchedKeys.length > 0,
    matchedKeys,
    missingKeys,
    recommendedAction: allMatched
      ? `✅ Fides has all matching keys! Use: Fides.aep({ purposeMapping: ${JSON.stringify(purposeMapping)} })`
      : `⚠️  Create ${missingKeys.length} Fides notice(s): [${missingKeys.join(", ")}]. Then use: Fides.aep({ purposeMapping: ${JSON.stringify(purposeMapping)} })`,
  };
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
// OneTrust Integration
// ============================================================================

/**
 * Singleton OneTrust provider instance for reading/writing consent
 */
const oneTrustProvider = new OneTrustProvider();

/**
 * Read consent state from OneTrust cookie and convert to Fides format
 * Uses the battle-tested OneTrustProvider class
 * @returns Fides-compatible consent object or null if OneTrust not found
 */
function readOneTrustConsent(): Record<string, boolean | string> | null {
  try {
    const cookieValue = oneTrustProvider.getConsentCookie();
    if (!cookieValue) {
      return null;
    }

    // Use OneTrustProvider's parsing logic with default mapping
    const fidesConsent = oneTrustProvider.convertToFidesConsent(cookieValue, {
      otFidesMapping: JSON.stringify(
        Object.entries(DEFAULT_ONETRUST_TO_FIDES_MAPPING).reduce(
          (acc, [otCat, fidesKey]) => {
            acc[otCat] = [fidesKey]; // OneTrustProvider expects array of keys
            return acc;
          },
          {} as Record<string, string[]>,
        ),
      ),
    });

    return fidesConsent || null;
  } catch (error) {
    console.error("[Fides Adobe] Error reading OneTrust consent:", error);
    return null;
  }
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
 * On first load, reads existing OneTrust consent if available.
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
 *
 * // Migration: Read OneTrust consent
 * const otConsent = aep.oneTrust.read();
 * if (otConsent) {
 *   console.log('OneTrust consent:', otConsent);
 * }
 * ```
 */
export const aep = (options?: AEPOptions): AEPIntegration => {
  const debug = options?.debug || false;

  // Read OneTrust consent once on initialization for migration
  const oneTrustConsent = readOneTrustConsent();
  if (oneTrustConsent && debug) {
    console.log(
      "[Fides Adobe] OneTrust consent detected on initialization:",
      oneTrustConsent,
    );
  }

  // Subscribe to Fides consent events using shared helper
  subscribeToConsent((consent) => pushConsentToAdobe(consent, options));

  // Return integration API
  return {
    consent: (): AEPConsentState => {
      return getAdobeConsentState();
    },
  };
};
