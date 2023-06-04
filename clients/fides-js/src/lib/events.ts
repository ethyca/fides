import { FidesCookie } from "./cookie";

/**
 * Defines the available event names:
 * - FidesInitialized: dispatched when initialization is complete, from Fides.init()
 * - FidesUpdated: dispatched when preferences are updated, from updateConsentPreferences() or Fides.init()
 */
export type FidesEvent = "FidesInitialized" | "FidesUpdated";

/**
 * Defines the properties available on event.detail. As of now, these are an
 * explicit subset of properties from the Fides cookie
 * TODO: add identity and meta?
 */
export type FidesEventDetail = Pick<FidesCookie, "consent">;

/**
 * Dispatch a custom event on the window object, providing the current Fides
 * state on the "detail" property of the event.
 * 
 * Example usage:
 * ```
 * window.addEventListener("FidesUpdated", (evt) => console.log("Fides.consent updated:", evt.detail.consent));
 * ```
 * 
 * The snippet above will print a console log whenever consent preferences are initialized/updated, like:
 * ```
 * Fides.consent updated: { data_sales_and_sharing: true }
 * ```
 */
export const dispatchFidesEvent = (eventName: FidesEvent, cookie: FidesCookie) => {
  if (typeof window !== "undefined" && typeof CustomEvent !== "undefined") {
    // Pick a subset of the Fides cookie properties to provide as event detail
    const { consent }: FidesEventDetail = cookie;
    const detail: FidesEventDetail = { consent };
    const event = new CustomEvent(eventName, { detail });
    window.dispatchEvent(event);
  }
};