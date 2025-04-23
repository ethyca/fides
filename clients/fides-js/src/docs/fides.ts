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
   * will be given a default value of `false`. This allows writing very simple
   * (and readable!) code to check a user's consent preferences.
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
   * User's current consent string(s) combined into a single value. This is used by
   * FidesJS to store IAB consent strings from various frameworks such as TCF, GPP,
   * and Google's "Additional Consent" string. Additionally, we support passing a
   * Notice Consent string, which is a base64 encoded string of the user's Notice
   * Consent preferences. See {@link FidesOptions.fides_string} for more details.
   *
   * The string consists of four parts separated by commas in the format:
   * `TC_STRING,AC_STRING,GPP_STRING,NC_STRING` where:
   *
   * - TC_STRING: IAB TCF (Transparency & Consent Framework) string
   * - AC_STRING: Google's Additional Consent string
   * - GPP_STRING: IAB GPP (Global Privacy Platform) string
   * - NC_STRING: Base64 encoded string of the user's Notice Consent preferences.
   *
   * @example
   * console.log(Fides.fides_string);
   * // "CPzHq4APzHq4AAMABBENAUEAALAAAEOAAAAAAEAEACACAAAA,1~61.70,DBABLA~BVAUAAAAAWA.QA,eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjowLCJhbmFseXRpY3MiOjF9"
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
   * The modal's "Trigger link label" text can be customized, per regulation, for each language defined in the `experience`.
   *
   * Use this function to get the label in the appropriate language for the user's current locale.
   * To always return in the default language only, pass the `disableLocalization` option as `true`.
   *
   * @example
   * Get the link text in the user's current locale (eg. Spanish):
   * ```ts
   * console.log(Fides.getModalLinkLabel()); // "Tus preferencias de privacidad"
   * ```
   *
   * Get the link text in the default locale to match other links on the page:
   * ```ts
   * console.log(Fides.getModalLinkLabel({ disableLocalization: true })); // "Your Privacy Choices"
   * ```
   *
   * @example
   * Apply the link text to a custom modal link element on Fides initialization:
   * ```html
   * <button class="my-custom-show-modal" id="fides-modal-link-label" onclick="Fides.showModal()"><button>
   * <script id="fides-js">
   *   function() {
   *     addEventListener("FidesInitialized", ( function() {
   *       document.getElementById('fides-modal-link-label').innerText = Fides.getModalLinkLabel();
   *     }));
   *   }
   * </script>
   * ```
   */
  getModalLinkLabel: (options?: { disableLocalization: boolean }) => string;

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
   * NOTE: If using custom JavaScript to show the modal, you may also want to set
   * the `modalLinkId` global setting on the Fides Privacy Center to prevent the
   * automated searching for, and binding the click event to, the modal link. If using
   * Fides Cloud, contact Ethyca Support for details on adjusting global settings.
   *
   * This function is not available for Headless experiences.
   *
   *
   * @example
   * Showing the FidesJS modal via an `onclick` handler on a custom button element:
   * ```html
   * <button class="my-custom-show-modal" onclick="Fides.showModal()">
   *   Your Privacy Choices
   * </button>
   * ```
   *
   * Another option, using a custom link element instead:
   * ```html
   * <a role="button" class="my-custom-show-modal" onclick="Fides.showModal()">
   *   Your Privacy Choices
   * </a>
   * ```
   *
   * Showing/hiding the custom element using the `fides-overlay-modal-link` CSS class:
   * ```css
   * /* Hide the custom element by default *\/
   * .my-custom-show-modal {
   *   display: none;
   * }
   * /* Only show the custom element when applicable *\/
   * .fides-overlay-modal-link-shown .my-custom-show-modal {
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
   * See the [Google Tag Manager tutorial](/docs/tutorials/consent-management/consent-management-configuration/google-tag-manager-consent-mode) for more.
   *
   * @param options - Optional configuration for the GTM integration
   * @param options.non_applicable_flag_mode - Controls how non-applicable privacy notices are handled in the data layer. Can be "omit" (default) to exclude non-applicable notices, or "include" to include them with a default value.
   * @param options.flag_type - Controls how consent values are represented in the data layer. Can be "boolean" (default) for true/false values, or "consent_mechanism" for string values like "opt_in", "opt_out", "acknowledge", "not_applicable".
   *
   * @example
   * Basic usage in your site's `<head>`:
   * ```html
   * <head>
   *   <script src="path/to/fides.js"></script>
   *   <script>Fides.gtm()</script>
   * </head>
   * ```
   *
   * @example
   * With options to include non-applicable notices and use consent mechanism strings:
   * ```html
   * <head>
   *   <script src="path/to/fides.js"></script>
   *   <script>
   *     Fides.gtm({
   *       non_applicable_flag_mode: "include",
   *       flag_type: "consent_mechanism"
   *     });
   *   </script>
   * </head>
   * ```
   */
  gtm: (options?: {
    non_applicable_flag_mode?: "omit" | "include";
    flag_type?: "boolean" | "consent_mechanism";
  }) => void;

  /**
   * Initializes FidesJS with an initial configuration object.
   *
   * In most cases, you should never have to call this directly, since
   * Fides Cloud will automatically bundle a `Fides.init(...)` call server-side
   * with the appropriate configuration options for the user's session based on
   * their location, property ID, and the matching experience config from Fides.
   *
   * However, initialization can be called manually if needed - for example to delay
   * initialization until after your own custom JavaScript has run to set up some
   * config options. In this case, you can disable the automatic initialization
   * by including the query param `initialize=false` in the Fides script URL
   * (see [Privacy Center FidesJS Hosting](/docs/dev-docs/js/privacy-center-fidesjs-hosting) for details).
   * You will then need to call `Fides.init()` manually at the appropriate time.
   *
   * This function can also be used to reinitialize FidesJS. This is useful when
   * you're working on a single page application (SPA) and you want to modify any
   * FidesJS options after initialization - for example, switching between
   * regular/embedded mode with `fides_embed`, overriding the user's language with
   * `fides_locale`, etc. Doing so without passing a config will reinitialize
   * FidesJS with the initial configuration, but taking into account any new overrides
   * such as the `fides_overrides` global or the query params.
   *
   * @example
   * Disable FidesJS initialization and trigger manually instead:
   * ```html
   * <head>
   *   <script src="https://privacy.example.com/fides.js?initialize=false"></script>
   * </head>
   * <body>
   *   <!--- Later, in your own application code... -->
   *   <script>Fides.init()</script>
   * </body>
   * ```
   * Configure overrides after loading Fides.js tag.
   * ```html
   * <head>
   *   <script src="path/to/fides.js">
   *     // Loading Fides.js before setting window.fides_overrides requires re-initialization
   *   </script>
   *
   *   <script>
   *     function onChange(newData) {
   *       // Update Fides options
   *       window.fides_overrides = window.fides_overrides || {};
   *       window.fides_overrides = {
   *         fides_locale: newData,
   *       };
   *
   *       // Reinitialize FidesJS
   *       window.Fides.init();
   *     };
   *   </script>
   * </head>
   * ```
   *
   */
  init: (config?: any) => Promise<void>;

  /**
   * An alternative way to subscribe to Fides events. The same events are supported, except the callback
   * receives the event details directly. This is useful in restricted environments where you can't
   * directly access `window.addEventListener`.
   *
   * Returns an unsubscribe function that can be called to remove the event listener.
   *
   * @example
   * ```ts
   * const unsubscribe = Fides.onFidesEvent("FidesUpdated", (detail) => {
   *   console.log(detail.consent);
   *   unsubscribe();
   * });
   * ```
   *
   * @param type The type of event to listen for, such as `FidesInitialized`, `FidesUpdated`, etc.
   * @param callback The callback function to call when the event is triggered
   */
  onFidesEvent: (type: any, callback: (detail: any) => void) => () => void;

  /**
   * @deprecated
   * `Fides.init()` can now be used directly instead of `Fides.reinitialize()`.
   */
  reinitialize: () => Promise<void>;

  /**
   * Check if the FidesJS experience should be shown to the user. This function
   * will return `true` if the user's session (location, property ID, etc.)
   * matches an `experience` with a banner component, and the user has not yet
   * interacted with the banner (e.g. by accepting or rejecting the consent
   * preferences) or in the case when the previous consent is no longer valid.
   */
  shouldShowExperience: () => boolean;

  /**
   * Encode the user's consent preferences into a Notice Consent string. See {@link FidesOptions.fides_string} for more details.
   *
   * @example
   * ```ts
   * const encoded = Fides.encodeNoticeConsentString({data_sales_and_sharing:0,analytics:1});
   * console.log(encoded); // "eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjowLCJhbmFseXRpY3MiOjF9"
   * ```
   *
   * @param consent The user's consent preferences to encode. (Numeric values are supported for smaller string results and will be decoded to boolean values)
   */
  encodeNoticeConsentString: (
    consent: Record<string, boolean | 0 | 1>,
  ) => string;

  /**
   * Decode a Notice Consent string into a user's consent preferences. See {@link FidesOptions.fides_string} for more details.
   *
   * @example
   * ```ts
   * const decoded = Fides.decodeNoticeConsentString("eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjowLCJhbmFseXRpY3MiOjF9");
   * console.log(decoded); // {data_sales_and_sharing: false, analytics: true}
   * ```
   *
   * @param base64String The Notice Consent string to decode.
   */
  decodeNoticeConsentString: (base64String: string) => {
    [noticeKey: string]: boolean;
  };

  /**
   * The detected geolocation that Fides uses to determine the user's experience.
   * This field is read-only.
   *
   * @example
   * ```ts
   * {
   *   "country": "ca",
   *   "location": "ca-on",
   *   "region": "on"
   * }
   * ```
   */
  geolocation?: any;

  /**
   * The detected i18n locale that Fides uses to determine the language shown to the user.
   *
   * @example
   * ```ts
   * "en"
   * ```
   *
   * This field is read-only.
   */
  locale: string;

  /**
   * The user's identity values, which only include a copy of the fides user device id that we store in the fides_consent cookie e.g.
   *
   * @example
   * ```ts
   * {
   *   "fides_user_device_id": "1234-"
   * }
   * ```
   *
   * This field is read-only.
   */
  identity: Record<string, string>;

  /**
   * NOTE: The properties below are all marked @internal, despite being exported
   * on the global Fides object. This is because they are mostly implementation
   * details and internals that we probably *should* be hiding, to avoid
   * customers getting too comfortable with accessing them.
   */

  /**
   * @internal
   */
  config?: any;

  /**
   * @internal
   */
  cookie?: any;

  /**
   * @internal
   */
  experience?: any;

  /**
   * DEFER (PROD-1815): This probably *should* be part of the documented SDK.
   *
   * @internal
   */
  fides_meta: Record<any, any>;

  /**
   * @internal
   */
  options: any;

  /**
   * @internal
   */
  saved_consent: Record<string, boolean>;

  /**
   * @internal
   */
  tcf_consent: any;

  /**
   * @internal
   */
  meta: (options: any) => void;

  /**
   * @internal
   */
  shopify: (options: any) => void;

  /**
   * @internal
   */
  blueconic: (options?: { approach: "onetrust" }) => void;
}
