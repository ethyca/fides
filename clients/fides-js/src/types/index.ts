/**
 * # FidesJS: Javascript SDK for Fides
 *
 * FidesJS is a Javascript SDK to integrate Fides consent into any website or
 * app! Commonly referred to as a Consent Management Platform (CMP), FidesJS
 * includes all the UI components (banners, modals, etc.), state management, and
 * utility functions you need to collect consent & enforce data privacy in your
 * application.
 * 
 * For example, FidesJS is used to:
 * - automatically configure the current user session with the applicable
 *   default consent preferences for their location (e.g. opt-out of data sales,
 *   opt-in to analytics, etc.)
 * - show a consent UI component (banner, modal, etc.) to the current user with
 *   the applicable privacy notices for them to opt-in, opt-out, etc.
 * - store the current user's consent preferences in a first-party cookie to
 *   remember their choices in future sessions
 * - expose the current user's consent preferences via a simple `Fides.consent`
 *   Javascript API to integrate consent into your own application
 * - dispatch events on the global `window` (e.g. `FidesUpdated`,
 *   `FidesUIShown`) to easily sync consent changes to your application in
 *   real-time based on the current user's actions
 * - integrate the current user's consent to other scripts via integrations with
 *   Google Tag Manager, IAB TCF, etc.
 * - ...and more!
 * 
 * See {@link Fides} for how to use the `window.Fides` Javascript API and {@link
 * FidesEvent} for how to use `window.addEventListener(...)` to subscribe to
 * custom Fides events for real-time updates.
 * 
 * @packageDocumentation
 */

/**
 * NOTE: This file exports the small subset of types used by this project that
 * are the user-facing classes, functions, events, etc. that engineers
 * integrating FidesJS into their own applications rely on. The TSDoc comments
 * here are used to generate living developer documentation that is then
 * imported and hosted on Ethyca's developer docs here:
 * [FidesJS SDK Documentation](https://ethyca.com/docs/dev-docs/js)
 * 
 * Therefore, all the types here should be considered part of FidesJS'
 * *official* developer API, so treat them with care!
 * 
 * You can also use the \@private tag to intentionally leave specific
 * properties/comments/etc. undocumented; this can be useful for internal-only
 * types for developers contributing directly to FidesJS, but that shouldn't be
 * included in the generic developer documentation. This comment itself is a
 * good example of that!
 * 
 * @private
 */

/**
 * Once FidesJS is initialized, it exports this global object to `window.Fides`
 * as the main API to integrate into your web applications.
 * 
 * TODO: more
 * 
 * @example
 * ```html
 * <head>
 *  <script src="path/to/fides.js"></script>
 * </head>
 * <body>
 *   <!--- ...later, in your own application code... --->
 *   <script>
 *     // Query the current user's consent preferences
 *     if (Fides && Fides.consent.data_sales_and_sharing) {
 *       // Enable advertising scripts
 *       console.log("Current user has opt-in consent for the `data_sales_and_sharing` privacy notice!");
 *     }
 *   </script>
 * </body>
 * ```
 */
export interface Fides {
  /**
   * User's current consent preferences.
   * 
   * TODO
   */
  consent: Record<string, boolean>;

  /**
   * @private
   */
  experience?: object;

  /**
   * @private
   */
  geolocation?: object;

  /**
   * 
   */
  fides_string?: string;

  /**
   * @private
   */
  options: object;

  fides_meta: object;

  /**
   * @private
   */
  tcf_consent: object;

  /**
   * @private
   */
  saved_consent: Record<string, boolean>;

  /**
   * Enable the Google Tag Manager (GTM) integration. This should be called
   * immediately after FidesJS is included, and once enabled, FidesJS will
   * automatically push all {@link FidesEvent} events to the GTM data layer as
   * they occur, which can then be used to trigger/block tags in GTM based on
   * `Fides.consent` preferences or other business logic.
   * 
   * See the Google Tag Manager tutorial for more: {@link
   * https://fid.es/configuring-gtm-consent}
   * 
   * @example 
   * Enabling the GTM integration in your site's `<head>`:
   * ```html
   * <head>
   *   <script src="path/to/fides.js"></script>
   *   <script>Fides.gtm()</script>
   * </head>
   * ```
   */
  gtm: () => void;

  /**
   * User's current "identity" values, which are recorded
   */
  identity: Record<string, string>;

  /**
   * Initialize FidesJS based
   * 
   * NOTE: In most cases, you should never have to call this directly, since
   * Fides Cloud will automatically bundle a `Fides.init(...)` call server-side
   * with the appropriate options for the user's session based on their
   * location, property ID, and the latest configuration options from Fides.
   * 
   * @param config something
   */
  init: (config: object) => Promise<void>;

  /**
   * TODO
   */
  initialized: boolean;

  /**
   * @private
   */
  meta: (options: object) => void;

  /**
   * @private
   */
  shopify: (options: object) => void;

  /**
   * Display the FidesJS modal component on the page, if the current user's
   * session (location, property ID, etc.) matches an `experience` with a modal
   * component. If the `experience` does not match, this function has no effect
   * and can be called safely at any time. 
   * 
   * This function is designed to be used to programmatically show the FidesJS
   * modal via an `onclick` handler on a "modal link" element on the page.
   * However, since the modal is optional, this link should only be shown when
   * applicable. To make it easy to dynamically show/hide this "modal link",
   * FidesJS will automatically add the CSS class `fides-overlay-modal-link-shown`
   * to the `<body>` when applicable. This class can then be used to show/hide a
   * link on the page via CSS rules - see the example below!
   * 
   * When not used as a click handler, `Fides.showModal()` can be called
   * programmatically at any time from your own custom Javascript logic as
   * desired.
   * 
   * 
   * @example
   * Showing the FidesJS modal via an `onclick` handler on a custom link element:
   * ```html
   * <a href="#" class="my-custom-link" onclick="Fides.showModal()">
   *   Your Privacy Choices
   * </a>
   * ```
   * 
   * Showing/hiding the custom link element using the `fides-overlay-modal-link` CSS class:
   * ```css
   * /* Hide the modal link by default *\/
   * .my-custom-link {
   *   display: none;
   * }
   * /* Only show the modal link when applicable *\/
   * .fides-overlay-modal-link-shown .my-custom-link {
   *   display: inline;
   * }
   * ```
   * 
   * @example
   * Showing the FidesJS modal programmatically in a Javascript function:
   * ```ts
   * function myCustomShowModalFunction() {
   *   console.log("Displaying FidesJS consent modal")
   *   if (window.Fides) {
   *     window.Fides.showModal();
   *   }
   * }
   * ```
   */
  showModal: () => void;
};

/**
 * Defines the list of FidesEvent names. See {@link FidesEvent} for details on each!
 * 
 * NOTE: We don't include this type definition in the generated API
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
 * ### FidesJS Events
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
 * 
 */
export interface FidesEvent {
  /**
   * Event properties passed by FidesJS when dispatched. Depending on the event type, some properties may or may not be set, so most of these are marked as optional.
   * 
   * @example
   * ```ts
   * window.addEventListener("FidesUpdated", (evt) => {
   *   if (evt.detail.extraDetails?.consentMethod == "accept") {
   *     console.log("Current user clicked the 'Accept' button!");
   *   }
   * });
   * ```
   */
  detail: {
    /**
     * Current consent preferences
     * 
     * TODO
     */
    consent: Record<string, boolean>;

    /**
     * Extra event properties for context
     * 
     * TODO
     */
    extraDetails?: {
      /**
       * TODO
       */
      servingComponent?: string;

      /**
       * TODO
       */
      consentMethod?: string;
    }
  }
};