/**
 * Defines the list of FidesEvent names. See {@link FidesEvent} for details on each!
 *
 * NOTE: We mark this type @private to exclude it from the generated SDK
 * documentation, since it's mostly just noise there - the list of events on
 * {@link FidesEvent} provides a good reference. But when coding, it's still
 * useful to have this union type around!
 *
 * `FidesInitialized` is deprecated and will be removed in a future release.
 * Use `FidesConsentLoaded` or `FidesReady` instead.
 *
 * @private
 */
export type FidesEventType =
  | "FidesInitializing"
  | "FidesInitialized"
  | "FidesConsentLoaded"
  | "FidesReady"
  | "FidesUpdating"
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
 * - `FidesInitializing`: Dispatched when initialization begins, which happens
 * immediately once the FidesJS script is loaded. If `Fides.init()` is called
 * multiple times, this event will also be dispatched each time.
 *
 * - `FidesConsentLoaded`: If previously saved consent was found during initialization,
 * we immediately set it on the `Fides` global object and dispatch this event.
 * This event will only be dispatched if consent was found.
 *
 * - `FidesReady`: Dispatched when initialization is complete and the
 * current user's consent preferences - either previously saved or applicable
 * defaults - have been set on the `Fides` global object.
 * This event will always be dispatched, even if no previous consent was found.
 *
 * - `FidesInitialized`: This event is dispatched based on the `fidesInitializedEventMode` setting:
 *   - "once" (default): fires alongside `FidesReady` only
 *   - "multiple": fires alongside both `FidesReady` and `FidesConsentLoaded` events
 *   - "disable": never fires
 * For new projects, we strongly encourage using `FidesReady` and `FidesConsentLoaded` instead.
 *
 * - `FidesUpdating`: Dispatched when a user action (e.g. accepting all, saving
 * changes, applying GPC) has started updating the user's consent preferences.
 * This event is dispatched immediately once the changes are made, but before
 * they are saved to the `Fides` object, `fides_consent` cookie on the user's
 * device, and the Fides API. To wait until the changes are fully
 * applied, use the `FidesUpdated` event instead.
 *
 * - `FidesUpdated`: Dispatched when a user action (e.g. accepting all, saving
 * changes, applying GPC) has finished updating the user's consent preferences.
 * This event is dispatched once the changes are fully saved to the `Fides`
 * object, `fides_consent` cookie on the user's device, and the Fides API. To
 * receive an event that fires before these changes are saved, use the
 * `FidesUpdating` event instead.
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
 * **Note**: The events `FidesUIShown`, `FidesUIChanged`, and `FidesModalClosed` are not available in a Headless experience, as they are specific to the FidesJS UI components.
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
     * High-precision timestamp from {@link https://developer.mozilla.org/en-US/docs/Web/API/Performance/mark performance.mark()}
     * representing when this event was created. The timestamp is measured in milliseconds since page load.
     *
     * May be undefined if the Performance API is not available.
     */
    timestamp?: number;

    /**
     * Extra event properties, for additional context.
     */
    extraDetails?: {
      /**
       * Which FidesJS UI component (if any) caused this event.
       */
      servingComponent?: "banner" | "modal" | "tcf_banner" | "tcf_overlay";

      /**
       * Whether the user should be shown the consent experience. Only available on FidesConsentLoaded and FidesReady events.
       */
      shouldShowExperience?: boolean;

      /**
       * What consent method (if any) caused this event.
       */
      consentMethod?:
        | "accept"
        | "reject"
        | "save"
        | "dismiss"
        | "acknowledge"
        | "gpc"
        | "script"
        | "ot_migration";

      /**
       * What UI element (if any) triggered this event, as well as the origin of
       * the event.
       */
      trigger?: {
        /**
         * Where the event originated from. If the event was triggered using an
         * SDK script, for example, this will be "external", meaning the event
         * was triggered by something other than a FidesJS UI element.
         */
        origin?: "fides" | "external";

        /**
         * The type of element that triggered the event. Additional types may be
         * added over time, so expect this type to grow.
         * Only present when origin is "fides".
         */
        type?: "toggle" | "button" | "link";

        /**
         * The UI label of the element that triggered the event.
         */
        label?: string;

        /**
         * The checked state of the element that triggered the event.
         * Only present when type is "toggle".
         */
        checked?: boolean;
      };

      /**
       * Information about the specific preference being changed, if this event
       * was triggered by a preference change.
       *
       * @example
       * ```ts
       * // For a notice toggle:
       * preference: {
       *   key: "advertising",
       *   type: "notice"
       * }
       *
       * // For a TCF purpose toggle:
       * preference: {
       *   key: "tcf_purpose_consent_4",
       *   type: "tcf_purpose_consent"
       * }
       *
       * // For a TCF vendor toggle:
       * preference: {
       *   key: "gvl.2",
       *   type: "tcf_vendor_consent",
       *   vendor_id: "gvl.2",
       *   vendor_list: "gvl",
       *   vendor_list_id: "2",
       *   vendor_name: "Captify"
       * }
       * ```
       */
      preference?: {
        /**
         * The unique key identifying this preference
         */
        key: string;

        /**
         * The type of preference being changed
         */
        type:
          | "notice"
          | "tcf_purpose_consent"
          | "tcf_purpose_legitimate_interest"
          | "tcf_special_feature"
          | "tcf_vendor_consent"
          | "tcf_vendor_legitimate_interest";

        /**
         * The vendor ID if this is a vendor-related preference
         */
        vendor_id?: string;

        /**
         * The vendor list type if this is a vendor-related preference
         */
        vendor_list?: "gvl" | "gacp" | "fds";

        /**
         * The vendor list ID if this is a vendor-related preference
         */
        vendor_list_id?: string;

        /**
         * The vendor name if this is a vendor-related preference
         */
        vendor_name?: string;
      };
    };
  };
}
