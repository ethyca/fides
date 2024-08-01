import type { FidesEventType } from "../docs";
import { FidesCookie } from "./consent-types";
import { debugLog } from "./consent-utils";

// Bonus points: update the WindowEventMap interface with our custom event types
declare global {
  interface WindowEventMap extends Record<FidesEventType, FidesEvent> {}
}

/**
 * Defines the type of "extra" details that can be optionally added to certain
 * events. This is intentionally vague, but constrained to be basic (primitive)
 * values for simplicity.
 */
export type FidesEventExtraDetails = Record<
  string,
  string | number | boolean | undefined
>;

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
  cookie: FidesCookie | undefined,
  debug: boolean,
  extraDetails?: FidesEventExtraDetails,
) => {
  if (typeof window !== "undefined" && typeof CustomEvent !== "undefined") {
    // Extracts consentMethod directly from the cookie instead of having to pass in duplicate data to this method
    const constructedExtraDetails: FidesEventExtraDetails = {
      consentMethod: cookie?.fides_meta.consentMethod,
      ...extraDetails,
    };
    const event = new CustomEvent(type, {
      detail: { ...cookie, debug, extraDetails: constructedExtraDetails },
    });
    performance?.mark(type);
    debugLog(
      debug,
      `Dispatching event type ${type} ${
        constructedExtraDetails?.servingComponent
          ? `from ${constructedExtraDetails.servingComponent} `
          : ""
      }${cookie ? `with cookie ${JSON.stringify(cookie)} ` : ""}${
        constructedExtraDetails
          ? `with extra details ${JSON.stringify(constructedExtraDetails)} `
          : ""
      }`,
    );
    window.dispatchEvent(event);
  }
};
