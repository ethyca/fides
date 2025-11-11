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

  // Step 4: Get initial state after Fides initialization from OneTrust
  log("\nStep 4: Initial consent state after migration...");
  log("-".repeat(60));

  // Helper to get current Fides + Adobe state (OneTrust doesn't change, so we don't re-read it)
  const getConsentSummary = () => {
    const fidesConsent = (window as any).Fides?.consent || {};
    const adobeConsent = aepInstance.consent();

    return {
      fides: fidesConsent,
      adobe: adobeConsent.summary,
    };
  };

  const initial = getConsentSummary();
  log("Fides: " + formatConsent(initial.fides));
  log("Adobe: " + formatConsent(initial.adobe));

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
  const afterToggle = getConsentSummary();
  log("Fides: " + formatConsent(afterToggle.fides));
  log("Adobe: " + formatConsent(afterToggle.adobe));

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
  const afterOptIn = getConsentSummary();
  log("Fides: " + formatConsent(afterOptIn.fides));
  log("Adobe: " + formatConsent(afterOptIn.adobe));

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
  const afterOptOut = getConsentSummary();
  log("Fides: " + formatConsent(afterOptOut.fides));
  log("Adobe: " + formatConsent(afterOptOut.adobe));

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
  log("  aep.consent()          // Check current Adobe consent");
  log("  Fides.nvidia.status()  // Full diagnostics");
  log("\n");

  return aepInstance;
};
