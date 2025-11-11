/**
 * NVIDIA-specific demo utilities for Adobe + OneTrust integration
 *
 * These are test/demo helpers optimized for nvidia.com which has OneTrust + Adobe.
 */

import { NoticeConsent } from "../lib/consent-types";
import {
  aep,
  AEPIntegration,
  AEPDiagnostics,
  getFidesDiagnostics,
  getAlloyDiagnostics,
  getVisitorDiagnostics,
  getOptInDiagnostics,
  getAdobeCookies,
  getLaunchDiagnostics,
  getAnalyticsDiagnostics,
} from "./aep";
import { gtagConsent, GtagConsentIntegration } from "./gtag-consent";
import { status as getOneTrustStatus, readConsent as readOneTrustConsent } from "./onetrust";

/**
 * Get comprehensive diagnostics for the NVIDIA environment.
 *
 * Shows status of:
 * - Fides consent configuration
 * - Adobe Web SDK (Alloy)
 * - Adobe Visitor API (ECID)
 * - Adobe ECID Opt-In Service
 * - Adobe Launch
 * - Adobe Analytics
 * - OneTrust consent
 * - Adobe cookies
 *
 * @returns Comprehensive diagnostic information
 *
 * @example
 * ```javascript
 * const status = Fides.nvidia.status();
 * console.log('ECID:', status.visitor.marketingCloudVisitorID);
 * console.log('OneTrust detected:', status.oneTrust?.detected);
 * console.log('Fides consent keys:', status.fides.consentKeys);
 * ```
 */
export const status = (): AEPDiagnostics => {
  // Get base OneTrust status
  const otStatus = getOneTrustStatus();

  // Add NVIDIA-specific Adobe mapping info
  const oneTrustDiagnostics: AEPDiagnostics["oneTrust"] = {
    detected: otStatus.detected,
    activeGroups: otStatus.activeGroups,
    categoriesConsent: otStatus.categoriesConsent,
    rawCookieValue: otStatus.rawCookieValue,
    parseError: otStatus.parseError,
  };

  // Add Adobe integration mapping (NVIDIA-specific)
  if (otStatus.detected && otStatus.activeGroups && otStatus.activeGroups.length > 0) {
    oneTrustDiagnostics.adobeIntegration = {
      detected: true,
      mapping: {
        C0001: [], // Strictly Necessary - not mapped
        C0002: ["collect", "measure"], // Performance → Analytics
        C0003: ["personalize"], // Functional → Target
        C0004: ["personalize", "share"], // Advertising → Target + AAM
      },
    };
  } else {
    oneTrustDiagnostics.adobeIntegration = {
      detected: false,
    };
  }

  return {
    timestamp: new Date().toISOString(),
    fides: getFidesDiagnostics(),
    alloy: getAlloyDiagnostics(),
    visitor: getVisitorDiagnostics(),
    optIn: getOptInDiagnostics(),
    cookies: getAdobeCookies(),
    launch: getLaunchDiagnostics(),
    analytics: getAnalyticsDiagnostics(),
    oneTrust: oneTrustDiagnostics,
  };
};

/**
 * NVIDIA-specific Adobe Web SDK purpose mapping.
 *
 * Maps NVIDIA's Fides consent keys to Adobe Web SDK purposes:
 * - performance → Analytics purposes (collect, measure)
 * - functional → Target purposes (personalize)
 * - advertising → AAM purposes (personalize, share)
 */
const NVIDIA_PURPOSE_MAPPING = {
  performance: ['collect', 'measure'],
  functional: ['personalize'],
  advertising: ['personalize', 'share'],
};

/**
 * NVIDIA-specific Adobe ECID Opt-In category mapping.
 *
 * Maps NVIDIA's Fides consent keys to Adobe ECID categories:
 * - performance → aa (Analytics)
 * - functional → target (Target)
 * - advertising → aam (Audience Manager)
 */
const NVIDIA_ECID_MAPPING = {
  performance: ['aa' as const],
  functional: ['target' as const],
  advertising: ['aam' as const],
};

/**
 * NVIDIA-specific Google Consent Mode v2 mapping.
 *
 * Maps NVIDIA's Fides consent keys to Google consent types:
 * - performance → analytics_storage
 * - functional → functionality_storage, personalization_storage
 * - advertising → ad_storage, ad_personalization, ad_user_data
 * - essential → (no mapping, always granted)
 */
const NVIDIA_GTAG_MAPPING = {
  performance: ['analytics_storage' as const],
  functional: ['functionality_storage' as const, 'personalization_storage' as const],
  advertising: ['ad_storage' as const, 'ad_personalization' as const, 'ad_user_data' as const],
};

/**
 * Consent state row showing the mapping chain and actual values
 */
interface ConsentRow {
  fidesKey: string;
  fidesValue: boolean | string | null; // Actual value from window.Fides.consent
  adobePurposes: string[];
  adobeECIDCategory: string | null;
  ecidApproved: boolean | null; // Actual value from adobe.optIn.isApproved()
  googleConsentTypes: string[]; // Google Consent Mode v2 types
  googleGranted: boolean | null; // Actual value (inferred from Fides consent)
}

/**
 * Complete consent state showing mappings and actual values across all systems.
 *
 * This makes it clear what's configuration vs. actual runtime values.
 */
interface ConsentState {
  timestamp: string;
  rows: ConsentRow[];
  summary: {
    fidesInitialized: boolean;
    adobeECIDConfigured: boolean;
    googleGtagDetected: boolean;
  };
}

/**
 * Get comprehensive consent state showing actual values across Fides, Adobe, and Google.
 *
 * This pivots the data to show the mapping chain clearly:
 * Fides Key → Adobe Purposes → ECID Category → Google Consent Types
 *
 * Shows ACTUAL consent values at each step, not just configuration.
 *
 * @example
 * ```javascript
 * const state = Fides.nvidia.consent();
 *
 * // See the complete mapping chain with actual values:
 * state.rows.forEach(row => {
 *   console.log(`${row.fidesKey} (${row.fidesValue})
 *     → Adobe: ${row.adobeECIDCategory} (${row.ecidApproved})
 *     → Google: ${row.googleConsentTypes} (${row.googleGranted})`);
 * });
 * ```
 */
export const consent = (): ConsentState => {
  const timestamp = new Date().toISOString();

  // Get actual Fides state
  const fidesConsent = (window as any).Fides?.consent || {};
  const fidesInitialized = !!(window as any).Fides?.initialized;

  // Get actual Adobe ECID state
  const adobeOptIn = (window as any).adobe?.optIn;
  const ecidConfigured = !!adobeOptIn;

  // Check if Google gtag is available
  const gtagDetected = typeof (window as any).gtag === 'function';

  // Build the mapping rows with ACTUAL values
  // Note: Google values show what Fides is pushing (or would push if gtag exists)
  const rows: ConsentRow[] = [
    {
      fidesKey: "essential",
      fidesValue: fidesConsent.essential ?? null,
      adobePurposes: [], // Essential doesn't map to Adobe
      adobeECIDCategory: null,
      ecidApproved: null,
      googleConsentTypes: [], // Essential doesn't map to Google
      googleGranted: null,
    },
    {
      fidesKey: "performance",
      fidesValue: fidesConsent.performance ?? null,
      adobePurposes: ["collect", "measure"],
      adobeECIDCategory: "aa", // Analytics
      ecidApproved: ecidConfigured
        ? (adobeOptIn.isApproved?.(adobeOptIn.Categories?.ANALYTICS) ?? null)
        : null,
      googleConsentTypes: NVIDIA_GTAG_MAPPING.performance,
      googleGranted: fidesConsent.performance !== null && fidesConsent.performance !== undefined
        ? !!fidesConsent.performance
        : null,
    },
    {
      fidesKey: "functional",
      fidesValue: fidesConsent.functional ?? null,
      adobePurposes: ["personalize"],
      adobeECIDCategory: "target", // Target
      ecidApproved: ecidConfigured
        ? (adobeOptIn.isApproved?.(adobeOptIn.Categories?.TARGET) ?? null)
        : null,
      googleConsentTypes: NVIDIA_GTAG_MAPPING.functional,
      googleGranted: fidesConsent.functional !== null && fidesConsent.functional !== undefined
        ? !!fidesConsent.functional
        : null,
    },
    {
      fidesKey: "advertising",
      fidesValue: fidesConsent.advertising ?? null,
      adobePurposes: ["personalize", "share"],
      adobeECIDCategory: "aam", // Audience Manager
      ecidApproved: ecidConfigured
        ? (adobeOptIn.isApproved?.(adobeOptIn.Categories?.AAM) ?? null)
        : null,
      googleConsentTypes: NVIDIA_GTAG_MAPPING.advertising,
      googleGranted: fidesConsent.advertising !== null && fidesConsent.advertising !== undefined
        ? !!fidesConsent.advertising
        : null,
    },
  ];

  return {
    timestamp,
    rows,
    summary: {
      fidesInitialized,
      adobeECIDConfigured: ecidConfigured,
      googleGtagDetected: gtagDetected,
    },
  };
};


/**
 * Format consent object with consistent key ordering for easy comparison
 */
const formatConsent = (consent: Record<string, any> | null): string => {
  if (!consent) return "null";

  // Sort keys alphabetically for consistent display
  const sortedKeys = Object.keys(consent).sort();
  const sortedObj: Record<string, any> = {};
  sortedKeys.forEach(key => {
    sortedObj[key] = consent[key];
  });

  return JSON.stringify(sortedObj);
};

/**
 * NVIDIA Demo: Comprehensive Adobe + OneTrust integration demo
 *
 * This function demonstrates the full Fides → Adobe → OneTrust sync workflow
 * on nvidia.com. It checks for OneTrust presence, initializes the Adobe
 * integration, and demonstrates consent synchronization.
 *
 * @returns Live AEP integration instance (throws error if demo fails)
 *
 * @example
 * ```javascript
 * // Run the demo on nvidia.com
 * const aep = await Fides.nvidia.demo();
 *
 * // Continue testing with the returned instance
 * aep.consent();
 * ```
 */
const DEMO_VERSION = "1.2.0";

export const nvidiaDemo = async (): Promise<AEPIntegration> => {
  const log = (msg: string) => {
    console.log(msg);
  };

  log("\nFIDES ADOBE + ONETRUST DEMO\n");
  log(`Version: ${DEMO_VERSION}`);
  log("=" .repeat(60));

  // Step 1: Read OneTrust once at the beginning (it won't change during demo)
  log("\nStep 1: Reading OneTrust consent to initialize Fides...");
  const initialOneTrustConsent = readOneTrustConsent();
  if (initialOneTrustConsent) {
    log(`✅ OneTrust initial state: ${formatConsent(initialOneTrustConsent)}`);

    // Initialize Fides from OneTrust (for demo/migration scenario)
    (window as any).Fides.consent = initialOneTrustConsent;
    log(`   Initialized Fides from OneTrust`);

    // Dispatch FidesUpdated event to trigger any existing subscriptions
    window.dispatchEvent(new CustomEvent('FidesUpdated', {
      detail: {
        consent: initialOneTrustConsent,
        extraDetails: { trigger: { origin: 'onetrust_migration' } }
      }
    }));
  } else {
    log("⚠️ Could not read OneTrust consent");
    throw new Error("Failed to read OneTrust consent - required for demo");
  }

  // Step 2: Create AEP instance with NVIDIA's mappings
  log("\nStep 2: Initializing Adobe integration...");
  const aepInstance = aep({
    purposeMapping: NVIDIA_PURPOSE_MAPPING,
    ecidMapping: NVIDIA_ECID_MAPPING,
    debug: false,
  });
  log("✅ Adobe integration initialized");
  log("   Web SDK: performance→(collect,measure), functional→(personalize), advertising→(personalize,share)");
  log("   ECID: performance→aa, functional→target, advertising→aam");

  // Step 2.5: Initialize Google Consent Mode v2
  log("\nStep 2.5: Initializing Google Consent Mode v2...");
  const gtagInstance = gtagConsent({
    purposeMapping: NVIDIA_GTAG_MAPPING,
    debug: false,
  });
  log("✅ Google Consent Mode initialized");
  log("   Mapping: performance→analytics_storage, functional→functionality/personalization, advertising→ad_storage/ad_personalization/ad_user_data");

  // Step 3: Detect active systems
  log("\nStep 3: Detecting active systems...");
  const diagnostics = status();
  const activeSystems: string[] = [];

  if (diagnostics.oneTrust?.detected) {
    activeSystems.push("OneTrust");
  }
  if (diagnostics.alloy?.configured) {
    activeSystems.push("Adobe Web SDK");
  }
  if (diagnostics.optIn?.configured) {
    activeSystems.push("Adobe ECID Opt-In");
  }

  if (activeSystems.length === 0) {
    log("❌ No consent systems detected!");
    throw new Error("No consent systems active - expected Adobe or OneTrust");
  }

  log(`✅ Active systems: ${activeSystems.join(", ")}`);

  // Step 4: Show initial consent state with mapping chain
  log("\nStep 4: Initial consent state after migration...");
  log("-".repeat(60));

  const showConsentTable = () => {
    const state = consent();
    state.rows.forEach(row => {
      const fidesVal = row.fidesValue === null ? 'N/A' : row.fidesValue;
      const adobeVal = row.ecidApproved === null ? 'N/A' : row.ecidApproved;
      const googleVal = row.googleGranted === null ? 'N/A' : row.googleGranted;
      const ecidCat = row.adobeECIDCategory || 'none';
      const googleTypes = row.googleConsentTypes.length > 0
        ? row.googleConsentTypes.join(', ')
        : 'none';

      log(`  ${row.fidesKey} → Adobe: ${ecidCat}, Google: ${googleTypes}`);
      log(`    Fides: ${fidesVal}, Adobe: ${adobeVal}, Google: ${googleVal}`);
    });
  };

  showConsentTable();

  // Step 5: Change one notice
  log("\nStep 5: Toggling 'performance' notice...");

  const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  // Get current Fides consent
  const currentConsent = { ...(window as any).Fides.consent };
  const currentPerformance = currentConsent.performance;

  // Toggle performance
  currentConsent.performance = !currentPerformance;
  (window as any).Fides.consent = currentConsent;

  // Dispatch update event to trigger sync
  window.dispatchEvent(new CustomEvent('FidesUpdated', {
    detail: {
      consent: currentConsent,
      extraDetails: { trigger: { origin: 'demo' } }
    }
  }));

  await wait(1000); // Wait for cookie write and sync

  log(`   Changed 'performance' from ${currentPerformance} → ${!currentPerformance}`);
  log("\nConsent state after toggle:");
  log("-".repeat(60));
  showConsentTable();

  // Step 6: Opt-in to all
  log("\nStep 6: Opting IN to all notices...");

  const optInAll: NoticeConsent = {};
  Object.keys(currentConsent).forEach(key => {
    optInAll[key] = true;
  });

  (window as any).Fides.consent = optInAll;
  window.dispatchEvent(new CustomEvent('FidesUpdated', {
    detail: {
      consent: optInAll,
      extraDetails: { trigger: { origin: 'demo' } }
    }
  }));

  await wait(1000); // Wait for sync

  log("\nConsent state after OPT-IN ALL:");
  log("-".repeat(60));
  showConsentTable();

  // Step 7: Opt-out of all (except essential)
  log("\nStep 7: Opting OUT of all notices (except essential)...");

  const optOutAll: NoticeConsent = {};
  Object.keys(currentConsent).forEach(key => {
    optOutAll[key] = key === 'essential'; // Keep essential true
  });

  (window as any).Fides.consent = optOutAll;
  window.dispatchEvent(new CustomEvent('FidesUpdated', {
    detail: {
      consent: optOutAll,
      extraDetails: { trigger: { origin: 'demo' } }
    }
  }));

  await wait(1000); // Wait for sync

  log("\nConsent state after OPT-OUT ALL:");
  log("-".repeat(60));
  showConsentTable();

  log("\n✅ Demo complete");

  return aepInstance;
};
