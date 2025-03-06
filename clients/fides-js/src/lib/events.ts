import type { FidesEvent as DocsFidesEvent, FidesEventType } from "../docs";
import { FidesCookie } from "./consent-types";

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
 * Defines the properties available on event.detail. Currently the FidesCookie
 * and an extra field `meta` for any other details that the event wants to pass
 * around.
 */
export type FidesEventDetail = FidesCookie & {
  debug?: boolean;
  extraDetails?: FidesEventExtraDetails;
};

/**
 * Defines the properties available on event.detail.extraDetails.servingToggle
 */
export type FidesServingToggleDetails = NonNullable<
  DocsFidesEvent["detail"]["extraDetails"]
>["servingToggle"];

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
  extraDetails?: FidesEvent["detail"]["extraDetails"],
) => {
  if (typeof window !== "undefined" && typeof CustomEvent !== "undefined") {
    // Extracts consentMethod directly from the cookie instead of having to pass in duplicate data to this method
    const constructedExtraDetails: FidesEventExtraDetails = {
      consentMethod: cookie?.fides_meta.consentMethod,
      ...extraDetails,
    };
    const event = new CustomEvent(type, {
      detail: { ...cookie, debug, extraDetails: constructedExtraDetails },
      bubbles: true,
    });
    const perfMark = performance?.mark?.(type);
    fidesDebugger(
      `Dispatching event type ${type} ${
        constructedExtraDetails?.servingComponent
          ? `from ${constructedExtraDetails.servingComponent} `
          : ""
      }${cookie ? `with cookie ${JSON.stringify(cookie)} ` : ""}${
        constructedExtraDetails
          ? `with extra details ${JSON.stringify(constructedExtraDetails)} `
          : ""
      } (${perfMark?.startTime?.toFixed(2)}ms)`,
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
