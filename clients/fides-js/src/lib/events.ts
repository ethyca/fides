import type { FidesEvent as DocsFidesEvent, FidesEventType } from "../docs";
import { FidesCookie } from "./consent-types";
import { applyOverridesToConsent } from "./consent-utils";

// Bonus points: update the WindowEventMap interface with our custom event types
declare global {
  interface WindowEventMap extends Record<FidesEventType, FidesEvent> {}
}

/**
 * Defines the type of "extra" details that can be optionally added to certain
 * events. This is intentionally vague. See the /docs/fides-event.ts
 */
export type FidesEventExtraDetails = Record<
  string,
  string | number | boolean | Record<string, unknown> | undefined
>;

/**
 * Defines the properties available on event.detail. Currently includes:
 * - FidesCookie properties
 * - debug flag
 * - extraDetails for additional event context
 * - timestamp from performance.mark() if available
 */
export type FidesEventDetail = FidesCookie & {
  debug?: boolean;
  extraDetails?: FidesEventExtraDetails;
  timestamp?: number;
};

/**
 * Defines the properties available on event.detail.extraDetails.trigger
 */
export type FidesEventDetailsTrigger = NonNullable<
  DocsFidesEvent["detail"]["extraDetails"]
>["trigger"];

/**
 * Defines the properties available on event.detail.extraDetails.preference
 */
export type FidesEventDetailsPreference = NonNullable<
  DocsFidesEvent["detail"]["extraDetails"]
>["preference"];

/**
 * TODO (PROD-1815): Replace this type with this: import { FidesEvent } from "../types"
 *
 * However, this will require locking down some types and refactoring usage.
 */
export type FidesEvent = CustomEvent<FidesEventDetail>;

/**
 * Export the FidesEventType type from the docs module, for usage in tests.
 */
export type { FidesEventType };

/**
 * Dispatch a custom event on the window object, providing the current Fides
 * state on the "detail" property of the event.
 *
 * Example usage:
 * ```
 * window.addEventListener("FidesReady", (evt) => console.log("Fides.consent initialized:", evt.detail.consent));
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
  fidesCookie: FidesCookie | undefined,
  extraDetails?: FidesEventExtraDetails,
) => {
  const cookie = fidesCookie ? { ...fidesCookie } : undefined;
  if (typeof window !== "undefined" && typeof CustomEvent !== "undefined") {
    // Extracts consentMethod directly from the cookie instead of having to pass in duplicate data to this method
    const constructedExtraDetails: FidesEventExtraDetails = {
      consentMethod: cookie?.fides_meta
        .consentMethod as FidesEventExtraDetails["consentMethod"],
      ...extraDetails,
    };
    const perfMark = performance?.mark?.(type);
    const timestamp = perfMark?.startTime;
    const normalizedCookie: FidesCookie | undefined = cookie;
    if (normalizedCookie && cookie?.consent) {
      normalizedCookie.consent = applyOverridesToConsent(
        cookie.consent,
        window.Fides?.experience?.non_applicable_privacy_notices,
        window.Fides?.experience?.privacy_notices,
      );
    }
    const event = new CustomEvent(type, {
      detail: {
        ...normalizedCookie,
        debug: !!window.Fides?.options?.debug,
        extraDetails: constructedExtraDetails,
        timestamp,
      },
      bubbles: true,
    });
    fidesDebugger(
      `Dispatching event type ${type} ${
        constructedExtraDetails?.servingComponent
          ? `from ${constructedExtraDetails.servingComponent} `
          : ""
      }${cookie ? `with cookie ${JSON.stringify(cookie)} ` : ""}${
        constructedExtraDetails
          ? `with extra details ${JSON.stringify(constructedExtraDetails)} `
          : ""
      } (${timestamp?.toFixed(2)}ms)`,
    );
    window.dispatchEvent(event);
  }
};

/**
 * An alternative way to subscribe to Fides events. The same events are supported, except the callback
 * receives the event details directly. This is useful in restricted environments where you can't
 * directly access `window.addEventListener`.
 *
 * Returns an unsubscribe function that can be called to remove the event listener.
 */
export const onFidesEvent = (
  type: FidesEventType,
  callback: (evt: FidesEventDetail) => void,
): (() => void) => {
  const listener = (evt: FidesEvent) => callback(evt.detail);
  window.addEventListener(type, listener);
  return () => {
    window.removeEventListener(type, listener);
  };
};
