import { FidesCookie } from "./cookie";
import { debugLog } from "./consent-utils";

/**
 * Defines the available event names:
 * - FidesInitialized: dispatched when initialization is complete, from Fides.init()
 * - FidesUpdated: dispatched when preferences are updated from updateConsentPreferences()
 * - FidesUIShown: dispatched when either the banner or modal is shown to the user
 * - FidesUIChanged: dispatched when preferences are changed but not saved, i.e. "dirty".
 * - FidesModalClosed: dispatched when the modal is closed
 */
export type FidesEventType =
  | "FidesInitialized"
  | "FidesUpdated"
  | "FidesUIShown"
  | "FidesUIChanged"
  | "FidesModalClosed";

// Bonus points: update the WindowEventMap interface with our custom event types
declare global {
  interface WindowEventMap {
    FidesInitialized: FidesEvent;
    FidesUpdated: FidesEvent;
    FidesUIShown: FidesEvent;
    FidesUIChanged: FidesEvent;
    FidesModalClosed: FidesEvent;
  }
}

/**
 * Defines the properties available on event.detail. Currently the FidesCookie
 * and an extra field `meta` for any other details that the event wants to pass
 * around.
 */
export type FidesEventDetail = FidesCookie & {
  debug?: boolean;
  extraDetails?: Record<string, string>;
};

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
  extraDetails?: Record<string, string>
) => {
  if (typeof window !== "undefined" && typeof CustomEvent !== "undefined") {
    const event = new CustomEvent(type, {
      detail: { ...cookie, debug, extraDetails },
    });
    debugLog(
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
