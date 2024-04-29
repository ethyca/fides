import { debugLog } from "./consent-utils";
import { FidesCookie } from "./consent-types";
import type { FidesEventType } from "../docs";

// Bonus points: update the WindowEventMap interface with our custom event types
declare global {
  interface WindowEventMap extends Record<FidesEventType, FidesEvent> {}
}

/**
 * Defines the type of "extra" details that can be optionally added to certain
 * events. This is intentionally vague, but constrained to be basic (primitive)
 * values for simplicity.
 */
export type FidesEventExtraDetails = Record<string, string | number | boolean>;

/**
 * Defines the properties available on event.detail. Currently the FidesCookie
 * and an extra field `meta` for any other details that the event wants to pass
 * around.
 */
export type FidesEventDetail = FidesCookie & {
  debug?: boolean;
  extraDetails?: FidesEventExtraDetails;
};

/**
 * TODO (PROD-1815): Replace this type with this: import { FidesEvent } from "../types"
 *
 * However, this will require locking down some types and refactoring usage.
 */
export type FidesEvent = CustomEvent<FidesEventDetail>;

/**
 * Dispatch a custom event on the window object, providing the current Fides
 * state on the "detail" property of the event.
 *
 * Example usage:
 * ```
 * window.addEventListener("FidesInitialized", (evt) => console.log("Fides.consent initialized:", evt.detail.consent));
 * window.addEventListener("FidesUpdated", (evt) => console.log("Fides.consent updated:", evt.detail.consent));
 * ```
 *
 * The snippet above will print a console log whenever consent preferences are updated, like:
 * ```
 * Fides.consent initialized: { data_sales_and_sharing: false }
 * Fides.consent updated: { data_sales_and_sharing: true }
 * ```
 */
export const dispatchFidesEvent = (
  type: FidesEventType,
  cookie: FidesCookie,
  debug: boolean,
  extraDetails?: FidesEventExtraDetails
) => {
  if (typeof window !== "undefined" && typeof CustomEvent !== "undefined") {
    const event = new CustomEvent(type, {
      detail: { ...cookie, debug, extraDetails },
    });
    debugLog(
      debug,
      `Dispatching event type ${type} ${
        extraDetails?.servingComponent
          ? `from ${extraDetails.servingComponent} `
          : ""
      }with cookie ${JSON.stringify(cookie)} ${
        extraDetails?.consentMethod
          ? `using consent method ${extraDetails.consentMethod} `
          : ""
      }`
    );
    window.dispatchEvent(event);
  }
};
