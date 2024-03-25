/**
 * Defines the list of FidesEvent names. See {@link FidesEvent} for details on each!
 *
 * NOTE: We mark this type @private to exclude it from the generated SDK
 * documentation, since it's mostly just noise - the list of events on {@link
 * FidesEvent} provides a good reference.
 * 
 * @private
 */
export type FidesEventType =
  | "FidesInitialized"
  | "FidesUpdated"
  | "FidesUIShown"
  | "FidesUIChanged"
  | "FidesModalClosed";

/**
 * FidesJS dispatches a variety of lifecyle events to the global `window`,
 * making it easy to subscribe to an event stream to keep your application
 * updated in real-time. Each of these events extends the standard
 * [CustomEvent](https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent)
 * interface and include a {@link detail} object with various properties that
 * can be used for inspecting current consent preferences, generating analytics,
 * etc.
 *
 * @example
 * ```ts
 * window.addEventListener("FidesUpdated", (evt) => {
 *   console.log("Received 'FidesUpdated' event! Current consent preferences: ", evt.detail.consent);
 * });
 * ```
 *
 * See the list below for information on what events are dispatched (and when!)
 * and the {@link detail} reference for the available properties.
 *
 * For more information on working with these kind of `CustomEvent` objects in
 * the browser, see the MDN docs:
 * {@link https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent}
 *
 * ### List of FidesEvent Types
 *
 * - `FidesInitialized`: Dispatched when initialization is complete and the
 * current user's consent preferences - either previously saved or applicable
 * defaults - have been set on the `Fides` global object.
 *
 * - `FidesUpdated`: Dispatched whenever the current user's consent preferences
 * are updated on the `Fides` global object due to a user action (e.g. accepting
 * all, applying GPC). The
 *
 * - `FidesUIShown`: Dispatched whenever a FidesJS UI component is rendered and
 * shown to the current user (banner, modal, etc.). The specific component shown
 * can be obtained from the `detail.extraDetails.servingComponent` property on
 * the event.
 *
 * - `FidesUIChanged`: Dispatched whenever the current user changes their
 * preferences in the FidesJS UI but has yet to *save* those changes (i.e.
 * "dirty").
 *
 * - `FidesModalClosed`: Dispatched whenever the FidesJS modal is closed.
 *
 */
export interface FidesEvent extends CustomEvent {
  /**
   * Event properties passed by FidesJS when dispatched. Depending on the event type, some properties may or may not be set, so most of these are marked as optional.
   *
   * @example
   * ```ts
   * window.addEventListener("FidesUpdated", (evt) => {
   *   if (evt.detail.extraDetails?.consentMethod === "accept") {
   *     console.log("Current user clicked the 'Accept' button!");
   *   }
   * });
   * ```
   */
  detail: {
    /**
     * User's current consent preferences; see {@link Fides.consent} for detail.
     */
    consent: Record<string, boolean>;

    /**
     * User's current consent string; see {@link Fides.fides_string} for detail.
     */
    fides_string?: string;

    /**
     * Extra event properties, for additional context.
     */
    extraDetails?: {
      /**
       * Which FidesJS UI component (if any) caused this event.
       */
      servingComponent?: "banner" | "modal" | "tcf_banner" | "tcf_overlay";

      /**
       * What consent method (if any) caused this event.
       */
      consentMethod?: "accept" | "reject" | "save" | "dismiss" | "gpc";
    };
  };
};