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
 * NVIDIA-specific Adobe purpose mapping.
 *
 * Maps NVIDIA's Fides consent keys to Adobe purposes:
 * - performance → Analytics (collect, measure)
 * - functional → Target (personalize)
 * - advertising → AAM (personalize, share)
 */
const NVIDIA_PURPOSE_MAPPING = {
  performance: ['collect', 'measure'],
  functional: ['personalize'],
  advertising: ['personalize', 'share'],
};

/**
 * Consent state row showing the mapping chain and actual values
 */
interface ConsentRow {
  oneTrustCategory: string;
  oneTrustActive: boolean | null; // Actual value from OptanonConsent cookie
  fidesKey: string;
  fidesValue: boolean | string | null; // Actual value from window.Fides.consent
  adobePurposes: string[];
  adobeECIDCategory: string | null;
  ecidApproved: boolean | null; // Actual value from adobe.optIn.isApproved()
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
    oneTrustDetected: boolean;
    fidesInitialized: boolean;
    adobeECIDConfigured: boolean;
  };
}

/**
 * Get comprehensive consent state showing actual values across OneTrust, Fides, and Adobe.
 *
 * This pivots the data to show the mapping chain clearly:
 * OneTrust Category → Fides Key → Adobe Purposes → ECID Category
 *
 * Shows ACTUAL consent values at each step, not just configuration.
 *
 * @example
 * ```javascript
 * const state = Fides.nvidia.consent();
 *
 * // See the complete mapping chain with actual values:
 * state.rows.forEach(row => {
 *   console.log(`${row.oneTrustCategory} (${row.oneTrustActive})
 *     → ${row.fidesKey} (${row.fidesValue})
 *     → ${row.adobePurposes}
 *     → ${row.adobeECIDCategory} (${row.ecidApproved})`);
 * });
 * ```
 */
export const consent = (): ConsentState => {
  const timestamp = new Date().toISOString();

  // Get actual OneTrust state
  const otStatus = getOneTrustStatus();
  const otConsent = otStatus.categoriesConsent || {};

  // Get actual Fides state
  const fidesConsent = (window as any).Fides?.consent || {};
  const fidesInitialized = !!(window as any).Fides?.initialized;

  // Get actual Adobe ECID state
  const adobeOptIn = (window as any).adobe?.optIn;
  const ecidConfigured = !!adobeOptIn;

  // Build the mapping rows with ACTUAL values
  const rows: ConsentRow[] = [
    {
      oneTrustCategory: "C0001",
      oneTrustActive: otConsent.C0001 ?? null,
      fidesKey: "essential",
      fidesValue: fidesConsent.essential ?? null,
      adobePurposes: [], // Essential doesn't map to Adobe
      adobeECIDCategory: null,
      ecidApproved: null,
    },
    {
      oneTrustCategory: "C0002",
      oneTrustActive: otConsent.C0002 ?? null,
      fidesKey: "performance",
      fidesValue: fidesConsent.performance ?? null,
      adobePurposes: ["collect", "measure"],
      adobeECIDCategory: "aa", // Analytics
      ecidApproved: ecidConfigured
        ? (adobeOptIn.isApproved?.(adobeOptIn.Categories?.AA) ?? null)
        : null,
    },
    {
      oneTrustCategory: "C0003",
      oneTrustActive: otConsent.C0003 ?? null,
      fidesKey: "functional",
      fidesValue: fidesConsent.functional ?? null,
      adobePurposes: ["personalize"],
      adobeECIDCategory: "target", // Target
      ecidApproved: ecidConfigured
        ? (adobeOptIn.isApproved?.(adobeOptIn.Categories?.TARGET) ?? null)
        : null,
    },
    {
      oneTrustCategory: "C0004",
      oneTrustActive: otConsent.C0004 ?? null,
      fidesKey: "advertising",
      fidesValue: fidesConsent.advertising ?? null,
      adobePurposes: ["personalize", "share"],
      adobeECIDCategory: "aam", // Audience Manager
      ecidApproved: ecidConfigured
        ? (adobeOptIn.isApproved?.(adobeOptIn.Categories?.AAM) ?? null)
        : null,
    },
  ];

  return {
    timestamp,
    rows,
    summary: {
      oneTrustDetected: otStatus.detected,
      fidesInitialized,
      adobeECIDConfigured: ecidConfigured,
    },
  };
};

/**
 * Initialize Adobe integration with NVIDIA's configuration.
 *
 * Quick helper for testing on nvidia.com or other OneTrust sites.
 * Detects OneTrust categories, initializes Fides from OneTrust, and returns
 * a fully configured aep instance.
 *
 * @returns Configured AEP integration instance, or throws error if OneTrust not found
 *
 * @example
 * ```javascript
 * // On nvidia.com (or any OneTrust site):
 * const aep = Fides.nvidia.aep();
 *
 * // Integration is live! Check current state:
 * aep.consent();
 * aep.oneTrust.read();
 *
 * // Any Fides updates will sync to Adobe & OneTrust
 * window.Fides.consent.performance = true;
 * window.dispatchEvent(new CustomEvent('FidesUpdated', {
 *   detail: { consent: window.Fides.consent }
 * }));
 * ```
 */
export const nvidiaAEP = (): AEPIntegration => {
  // Initialize Fides consent from OneTrust
  const otConsent = readOneTrustConsent();
  if (otConsent) {
    (window as any).Fides.consent = otConsent;
    console.log(`[nvidia.aep] Initialized Fides from OneTrust`);

    // Dispatch update event
    window.dispatchEvent(new CustomEvent('FidesUpdated', {
      detail: {
        consent: otConsent,
        extraDetails: { trigger: { origin: 'nvidia_aep_init' } }
      }
    }));
  } else {
    console.log(`[nvidia.aep] ⚠️ OneTrust not found - using existing Fides consent`);
  }

  // Create configured instance with NVIDIA mapping
  const aepInstance = aep({
    purposeMapping: NVIDIA_PURPOSE_MAPPING,
    debug: false,
  });

  console.log(`[nvidia.aep] ✅ Adobe integration initialized`);
  console.log(`[nvidia.aep] Mapping: performance→Analytics, functional→Target, advertising→AAM`);

  return aepInstance;
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
export const nvidiaDemo = async (): Promise<AEPIntegration> => {
  const log = (msg: string) => {
    console.log(msg);
  };

  log("\nFIDES ADOBE + ONETRUST DEMO\n");
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

  // Step 2: Create AEP instance with NVIDIA's purpose mapping
  log("\nStep 2: Initializing Adobe integration...");
  const aepInstance = aep({
    purposeMapping: NVIDIA_PURPOSE_MAPPING,
    debug: false,
  });
  log("✅ Adobe integration initialized");
  log("   Mapping: performance→Analytics, functional→Target, advertising→AAM");

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
      const otVal = row.oneTrustActive === null ? 'N/A' : row.oneTrustActive;
      const fidesVal = row.fidesValue === null ? 'N/A' : row.fidesValue;
      const adobeVal = row.ecidApproved === null ? 'N/A' : row.ecidApproved;
      const ecidCat = row.adobeECIDCategory || 'none';

      log(`  ${row.oneTrustCategory} → ${row.fidesKey} → ${ecidCat}`);
      log(`    OneTrust: ${otVal}, Fides: ${fidesVal}, Adobe: ${adobeVal}`);
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

  // Summary
  log("\n" + "=".repeat(60));
  log("✅ DEMO COMPLETE");
  log("=".repeat(60));
  log("\nSummary:");
  log(`  Active systems: ${activeSystems.join(", ")}`);
  log(`  Purpose mapping: performance→Analytics, functional→Target, advertising→AAM`);
  log(`  Demonstrated: Init from OneTrust, Toggle, Opt-in all, Opt-out all`);
  log("\nThe 'aep' instance is now active - any Fides updates sync to Adobe automatically.");
  log("Continue testing with:");
  log("  aep.consent()            // Adobe ECID consent state");
  log("  Fides.nvidia.consent()   // Complete consent mapping table");
  log("  Fides.nvidia.status()    // Full system diagnostics");
  log("\n");

  return aepInstance;
};
