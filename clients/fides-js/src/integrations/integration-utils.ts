/**
 * Shared utilities for building Fides integrations
 */

import { FidesEventType } from "../docs";
import { FidesGlobal, NoticeConsent } from "../lib/consent-types";

declare global {
  interface Window {
    Fides: FidesGlobal;
  }
}

/**
 * Event subscription configuration
 * Maps each FidesEventType to whether it should trigger the handler
 */
export interface ConsentEventConfig {
  /**
   * Map of which Fides events should trigger the handler.
   * Listed as a Record so that future developers must explicitly consider
   * whether new events should be forwarded to integrations.
   *
   * @default Only FidesReady and FidesUpdated are enabled
   */
  events?: Record<FidesEventType, boolean>;

  /**
   * Whether to dispatch a synthetic event if Fides is already initialized
   * @default true
   */
  handleSynthetic?: boolean;
}

/**
 * Default event configuration for simple integrations
 * Most integrations only care about FidesReady and FidesUpdated
 */
const DEFAULT_EVENT_CONFIG: Record<FidesEventType, boolean> = {
  FidesInitializing: false,
  FidesInitialized: false,
  FidesConsentLoaded: false,
  FidesReady: true,
  FidesUpdating: false,
  FidesUpdated: true,
  FidesUIShown: false,
  FidesUIChanged: false,
  FidesModalClosed: false,
};

/**
 * Subscribe to Fides consent events with a handler function.
 * Handles both real-time events and synthetic events for late-loading integrations.
 *
 * Uses a Record pattern (similar to GTM integration) to force developers to
 * explicitly consider whether new FidesEventTypes should be forwarded to integrations.
 *
 * @param handler - Function to call when consent changes
 * @param config - Event configuration
 *
 * @example
 * ```typescript
 * subscribeToConsent((consent) => {
 *   console.log('Consent changed:', consent);
 *   // Push to vendor...
 * });
 * ```
 *
 * @example
 * ```typescript
 * // Custom event configuration
 * subscribeToConsent(
 *   (consent) => pushToVendor(consent),
 *   {
 *     events: {
 *       FidesInitializing: false,
 *       FidesInitialized: true,
 *       FidesConsentLoaded: false,
 *       FidesReady: true,
 *       FidesUpdating: false,
 *       FidesUpdated: true,
 *       FidesUIShown: false,
 *       FidesUIChanged: false,
 *       FidesModalClosed: false,
 *     },
 *   }
 * );
 * ```
 */
export function subscribeToConsent(
  handler: (consent: NoticeConsent) => void,
  config?: ConsentEventConfig,
): void {
  const eventConfig = config?.events || DEFAULT_EVENT_CONFIG;
  const handleSynthetic = config?.handleSynthetic ?? true;

  // Filter for events marked as true
  const eventsToForward = (
    Object.entries(eventConfig).filter(
      ([, shouldForward]) => shouldForward,
    ) as [FidesEventType, boolean][]
  ).map(([eventName]) => eventName);

  // Listen for Fides events
  eventsToForward.forEach((eventName) => {
    window.addEventListener(eventName, (event) => {
      handler(event.detail.consent);
    });
  });

  // Handle existing Fides consent (synthetic event for late-loading integrations)
  if (handleSynthetic && window.Fides?.consent) {
    handler(window.Fides.consent);
  }
}
