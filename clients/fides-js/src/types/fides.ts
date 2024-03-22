/**
 * Once FidesJS is initialized, it exports this global object to `window.Fides`
 * as the main API to integrate into your web applications.
 *
 * TODO: finish me!
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
   * User's current consent preferences.
   *
   * TODO
   */
  consent: Record<string, boolean>;

  /**
   * User's current advanced consent preferences.
   * 
   * TODO
   */
  fides_string?: string;

  /**
   * TODO
   */
  fides_meta: object;

  /**
   * User's current "identity" values, which are recorded
   */
  identity: Record<string, string>;

  /**
   * TODO
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
  init: (config: object) => Promise<void>;

  /**
   * NOTE: The properties below are all marked @private, despite being exported
   * on the global Fides object. This is because they are mostly implementation
   * details and internals that we probably *should* be hiding, to avoid
   * customers getting too comfortable with accessing them.
   */

  /**
   * @private
   */
  experience?: object;

  /**
   * @private
   */
  geolocation?: object;

  /**
   * @private
   */
  options: object;

  /**
   * @private
   */
  tcf_consent: object;

  /**
   * @private
   */
  saved_consent: Record<string, boolean>;

  /**
   * @private
   */
  meta: (options: object) => void;

  /**
   * @private
   */
  shopify: (options: object) => void;
};