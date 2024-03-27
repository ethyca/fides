/**
 * Once FidesJS is initialized, it exports this global object to `window.Fides`
 * as the main API to integrate into your web applications.
 * 
 * You can then use `Fides` in your JavaScript code to check the user's current
 * consent preferences (e.g. `if (Fides.consent.marketing) { ... }`), enable
 * FidesJS integrations (e.g. `Fides.gtm()`), programmaticaly show the FidesJS
 * UI (e.g. `Fides.showModal()`) and more. See the full list of properties below
 * for details.
 * 
 * NOTE: FidesJS will need to be downloaded, executed, and initialized before
 * the `Fides` object is available. Therefore, your code should check for the
 * existence of Fides *or* subscribe to the global `FidesInitialized` event (see
 * {@link FidesEvent}) for details) before using the `Fides` object in your own code.
 *
 * @example
 * ```html
 * <head>
 *   <script src="path/to/fides.js"></script>
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
   * User's current consent preferences, formatted as a key/value object with:
   * - key: the applicable Fides `notice_key` (e.g. `data_sales_and_sharing`, `analytics`)
   * - value: `true` or `false`, depending on whether or not the current user
   * has consented to the notice
   * 
   * Note that FidesJS will automatically set default consent preferences based
   * on the type of notice - so, for example a typical "opt-in" analytics notice
   * will be given a default value of `false`. This allows very writing very
   * simple (and readable!) code to check a user's consent preferences.
   * 
   * The specific keys provided in the `Fides.consent` property are determined
   * based on your Fides configuration, and are provided to the browser based on
   * the user's location, property ID, etc.
   * 
   * @example
   * A `Fides.consent` value showing the user has opted-out of data sales & sharing:
   * ```ts
   * {
   *   "data_sales_and_sharing": false
   * }
   * ```
   * 
   * @example
   * A `Fides.consent` value showing the user has opted-in to analytics, but not marketing:
   * ```ts
   * {
   *   "analytics": true,
   *   "marketing": false
   * }
   * ```
   */
  consent: Record<string, boolean>;

  /**
   * User's current consent string(s) combined into a single value. Currently,
   * this is used by FidesJS to store IAB consent strings from various
   * frameworks such as TCF, GPP, and Google's "Additional Consent" string.
   * 
   * @example
   * Example `fides_string` showing a combination of:
   * - IAB TC string: `CPzHq4APzHq4AAMABBENAUEAALAAAEOAAAAAAEAEACACAAAA`
   * - Google AC string: `1~61.70`
   * ```ts
   * console.log(Fides.fides_string); // CPzHq4APzHq4AAMABBENAUEAALAAAEOAAAAAAEAEACACAAAA,1~61.70
   * ```
   * 
   */
  fides_string?: string;

  /**
   * Whether or not FidesJS has finished initialization and has loaded the
   * current user's experience, consent preferences, etc.
   * 
   * NOTE: To be notified when initialization has completed, you can subscribe
   * to the `FidesInitialized` event. See {@link FidesEvent} for details.
   */
  initialized: boolean;

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
   * programmatically at any time from your own custom JavaScript logic as
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
   * Showing the FidesJS modal programmatically in a JavaScript function:
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
   * Initialize FidesJS based
   *
   * NOTE: In most cases, you should never have to call this directly, since
   * Fides Cloud will automatically bundle a `Fides.init(...)` call server-side
   * with the appropriate options for the user's session based on their
   * location, property ID, and the latest configuration options from Fides.
   *
   * @param config something
   */
  init: (config: any) => Promise<void>;

  /**
   * NOTE: The properties below are all marked @private, despite being exported
   * on the global Fides object. This is because they are mostly implementation
   * details and internals that we probably *should* be hiding, to avoid
   * customers getting too comfortable with accessing them.
   */

  /**
   * DEFER (PROD-1815): This probably *should* be part of the documented SDK.
   * 
   * @private
   */
  fides_meta: Record<any, any>;

  /**
   * DEFER (PROD-1815): This probably *should* be part of the documented SDK.
   * 
   * @private
   */
  identity: Record<string, string>;

  /**
   * @private
   */
  experience?: any;

  /**
   * @private
   */
  geolocation?: any;

  /**
   * @private
   */
  options: any;

  /**
   * @private
   */
  tcf_consent: any;

  /**
   * @private
   */
  saved_consent: Record<string, boolean>;

  /**
   * @private
   */
  meta: (options: any) => void;

  /**
   * @private
   */
  shopify: (options: any) => void;
};