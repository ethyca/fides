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
 * Configuration for consent event subscription
 */
export interface ConsentEventConfig {
  /**
   * Which events to listen to
   * @default ["FidesReady", "FidesUpdated"]
   */
  events?: FidesEventType[];

  /**
   * Whether to dispatch a synthetic event if Fides is already initialized
   * @default true
   */
  handleSynthetic?: boolean;
}

/**
 * Subscribe to Fides consent events with a handler function.
 * Handles both real-time events and synthetic events for late-loading integrations.
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
 */
export function subscribeToConsent(
  handler: (consent: NoticeConsent) => void,
  config?: ConsentEventConfig,
): void {
  const { events = ["FidesReady", "FidesUpdated"], handleSynthetic = true } =
    config || {};

  // Listen for Fides events
  events.forEach((eventName) => {
    window.addEventListener(eventName, (event) => {
      handler(event.detail.consent);
    });
  });

  // Handle existing Fides consent (synthetic event for late-loading integrations)
  if (handleSynthetic && window.Fides?.consent) {
    handler(window.Fides.consent);
  }
}
