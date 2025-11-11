/**
 * NVIDIA-specific demo utilities for Adobe + OneTrust integration
 *
 * These are test/demo helpers optimized for nvidia.com which has OneTrust + Adobe.
 */

import { NoticeConsent } from "../lib/consent-types";
import { OneTrustProvider } from "../lib/consent-migration/onetrust";
import {
  aep,
  AEPIntegration,
  AEPDiagnostics,
  AEPSuggestion,
  getFidesDiagnostics,
  getAlloyDiagnostics,
  getVisitorDiagnostics,
  getOptInDiagnostics,
  getAdobeCookies,
  getLaunchDiagnostics,
  getAnalyticsDiagnostics,
  getOneTrustDiagnostics,
  generateAEPSuggestion,
} from "./aep";

/**
 * Read OneTrust consent directly using standard mapping
 */
const readOneTrustConsent = (): NoticeConsent | null => {
  const provider = new OneTrustProvider();
  const cookieValue = provider.getConsentCookie();
  
  if (!cookieValue) {
    return null;
  }
  
  const otFidesMapping = JSON.stringify({
    C0001: "essential",
    C0002: "performance",
    C0003: "functional",
    C0004: "advertising",
  });
  
  return provider.convertToFidesConsent(cookieValue, { otFidesMapping }) || null;
};

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
  return {
    timestamp: new Date().toISOString(),
    fides: getFidesDiagnostics(),
    alloy: getAlloyDiagnostics(),
    visitor: getVisitorDiagnostics(),
    optIn: getOptInDiagnostics(),
    cookies: getAdobeCookies(),
    launch: getLaunchDiagnostics(),
    analytics: getAnalyticsDiagnostics(),
    oneTrust: getOneTrustDiagnostics(),
  };
};

/**
 * Suggest Fides notice configuration based on OneTrust categories.
 *
 * Analyzes the OneTrust OptanonConsent cookie and recommends:
 * - Fides notice names to create (essential, performance, functional, advertising)
 * - Adobe purpose mappings for each notice
 * - Whether Fides already has matching consent keys
 *
 * @returns Suggestion object with recommendations and validation
 *
 * @example
 * ```javascript
 * const suggestion = Fides.nvidia.suggest();
 *
 * if (!suggestion.success) {
 *   console.error(suggestion.error);
 *   // "❌ OneTrust not detected..."
 *   return;
 * }
 *
 * console.log('OneTrust categories:', suggestion.oneTrustCategories);
 * // ['C0001', 'C0002', 'C0003', 'C0004']
 *
 * console.log('Suggested Fides notices:', suggestion.suggestedFidesNotices);
 * // [{ name: 'essential', oneTrustCategory: 'C0001', ... }, ...]
 *
 * if (suggestion.fidesHasMatchingKeys) {
 *   // Use the suggested purpose mapping
 *   Fides.aep({ purposeMapping: suggestion.purposeMapping });
 * } else {
 *   console.log('Missing notices:', suggestion.missingKeys);
 *   // Create these in Fides Admin UI first
 * }
 * ```
 */
export const suggest = (): AEPSuggestion => {
  return generateAEPSuggestion();
};

/**
 * Initialize Adobe integration with auto-detected OneTrust mappings.
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
  // Detect OneTrust and get suggestions
  const suggestion = suggest();

  if (!suggestion.success) {
    throw new Error(
      `❌ Cannot initialize nvidia.aep: ${suggestion.error}\n\n` +
      `This function requires OneTrust to be present on the page.\n` +
      `Use Fides.aep({ purposeMapping: {...} }) with manual config instead.`
    );
  }

  console.log(`[nvidia.aep] OneTrust detected: ${suggestion.oneTrustCategories.join(", ")}`);
  console.log(`[nvidia.aep] Fides notices: ${suggestion.matchedKeys.join(", ")}`);

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
  }

  // Create configured instance
  const aepInstance = aep({
    purposeMapping: suggestion.purposeMapping,
    debug: false,
  });

  console.log(`[nvidia.aep] ✅ Adobe integration initialized with auto-detected mapping`);
  console.log(`[nvidia.aep] Use aep.consent() to check current Adobe consent`);

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

  // Step 1: Check if we have matching categories using suggest()
  log("\nStep 1: Checking OneTrust compatibility...");

  const suggestion = suggest();

  if (!suggestion.success) {
    log(`❌ ${suggestion.error}`);
    log("\n⚠️ Demo requires OneTrust to be present on the page.");
    log("   Please run this on nvidia.com or another OneTrust site.");
    throw new Error("OneTrust not detected - demo requires OneTrust on the page");
  }

  log(`✅ OneTrust detected: ${suggestion.oneTrustCategories.join(", ")}`);
  log(`   Suggested Fides notices: ${suggestion.suggestedFidesNotices.map(n => n.name).join(", ")}`);

  // Show what Fides actually has
  const actualFidesKeys = Object.keys((window as any).Fides?.consent || {});
  log(`   Current Fides consent keys: ${actualFidesKeys.length > 0 ? actualFidesKeys.join(", ") : "(none)"}`);

  if (!suggestion.fidesHasMatchingKeys) {
    log(`\n⚠️ Missing Fides notices: ${suggestion.missingKeys.join(", ")}`);
    log("   Please create these notices in Fides Admin UI:");
    suggestion.missingKeys.forEach((key) => {
      log(`   - ${key}`);
    });
    log(`\n   ${suggestion.recommendedAction}`);
    throw new Error(`Missing Fides notices: ${suggestion.missingKeys.join(", ")}`);
  }

  log(`✅ All Fides notices present: ${suggestion.matchedKeys.join(", ")}`);

  // Step 1.5: Initialize Fides consent from OneTrust if not already done
  log("\nStep 1.5: Reading OneTrust consent to initialize Fides...");
  const otConsentInitial = readOneTrustConsent();
  if (otConsentInitial) {
    // Update Fides consent to match OneTrust (for demo/migration scenario)
    (window as any).Fides.consent = otConsentInitial;
    log(`✅ Initialized Fides from OneTrust: ${formatConsent(otConsentInitial)}`);

    // Dispatch FidesUpdated event to trigger any existing subscriptions
    window.dispatchEvent(new CustomEvent('FidesUpdated', {
      detail: {
        consent: otConsentInitial,
        extraDetails: { trigger: { origin: 'onetrust_migration' } }
      }
    }));
  } else {
    log("⚠️ Could not read OneTrust consent");
  }

  // Step 2: Create AEP instance with correct purpose mapping
  log("\nStep 2: Initializing Adobe integration...");
  const aepInstance = aep({
    purposeMapping: suggestion.purposeMapping,
    debug: false, // We'll log ourselves
  });
  log("✅ Adobe integration initialized");

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

  // Step 4 & 5: Get initial state and log pre-sync
  log("\nStep 4-5: Getting initial consent state...");
  log("-".repeat(60));

  const getConsentSummary = () => {
    const fidesConsent = (window as any).Fides?.consent || {};
    const adobeConsent = aepInstance.consent();
    const otConsent = readOneTrustConsent();

    return {
      fides: fidesConsent,
      adobe: adobeConsent.summary,
      oneTrust: otConsent,
    };
  };

  const preSync = getConsentSummary();
  log("Fides:    " + formatConsent(preSync.fides));
  log("Adobe:    " + formatConsent(preSync.adobe));
  log("OneTrust: " + formatConsent(preSync.oneTrust));

  // Step 6-7: Read OneTrust and sync to Fides
  log("\nStep 6-7: Reading OneTrust consent...");
  const otConsent = readOneTrustConsent();

  if (!otConsent) {
    log("❌ Could not read OneTrust consent");
    throw new Error("Failed to read OneTrust consent");
  }

  log("✅ Read OneTrust consent: " + formatConsent(otConsent));

  // Note: In a production migration scenario, Fides would automatically
  // initialize from OneTrust. For this demo, we'll just verify the states match
  log("\nPost-sync consent state:");
  log("-".repeat(60));
  const postSync = getConsentSummary();
  log("Fides:    " + formatConsent(postSync.fides));
  log("Adobe:    " + formatConsent(postSync.adobe));
  log("OneTrust: " + formatConsent(postSync.oneTrust));

  // Step 8-9: Change one notice
  log("\nStep 8-9: Toggling 'performance' notice...");

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
  log("Fides:    " + formatConsent(afterToggle.fides));
  log("Adobe:    " + formatConsent(afterToggle.adobe));
  log("OneTrust: " + formatConsent(afterToggle.oneTrust));

  // Step 10: Opt-in to all
  log("\nStep 10: Opting IN to all notices...");

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

  await wait(1000); // Wait for cookie write and sync

  log("\nConsent state after OPT-IN ALL:");
  log("-".repeat(60));
  const afterOptIn = getConsentSummary();
  log("Fides:    " + formatConsent(afterOptIn.fides));
  log("Adobe:    " + formatConsent(afterOptIn.adobe));
  log("OneTrust: " + formatConsent(afterOptIn.oneTrust));

  // Step 11: Opt-out of all (except essential)
  log("\nStep 11: Opting OUT of all notices (except essential)...");

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

  await wait(1000); // Wait for cookie write and sync

  log("\nConsent state after OPT-OUT ALL:");
  log("-".repeat(60));
  const afterOptOut = getConsentSummary();
  log("Fides:    " + formatConsent(afterOptOut.fides));
  log("Adobe:    " + formatConsent(afterOptOut.adobe));
  log("OneTrust: " + formatConsent(afterOptOut.oneTrust));

  // Summary
  log("\n" + "=".repeat(60));
  log("✅ DEMO COMPLETE");
  log("=".repeat(60));
  log("\nSummary:");
  log(`  Active systems: ${activeSystems.join(", ")}`);
  log(`  OneTrust categories: ${suggestion.oneTrustCategories.join(", ")}`);
  log(`  Fides notices: ${suggestion.matchedKeys.join(", ")}`);
  log(`  Demonstrated: Toggle, Opt-in all, Opt-out all`);
  log("\nThe 'aep' instance is now active.");
  log("Continue testing with:");
  log("  aep.consent()       // Check current Adobe consent");
  log("  aep.oneTrust.read() // Check OneTrust cookie");
  log("  aep.dump()          // Full diagnostics");
  log("\n");

  return aepInstance;
};
