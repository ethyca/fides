/**
 * FidesJS supports a variety of custom options to modify it's behavior or
 * enabled more advanced usage. For example, the `fides_locale` option can be
 * provided to override the browser locale. See the properties list below for
 * the supported options and example usage for each.
 *
 * Any of the FidesJS options can be provided in one of three ways:
 *
 * 1. **Query Params** (e.g. `example.com?fides_locale=es`): typically used only for testing
 * 2. **Window Object** (e.g. `window.fides_overrides = { fides_locale: "es" }`): typically used to configure FidesJS via an inline `<script>` tag on
 * the page for customization
 * 3. **Cookie Values** (e.g. `document.cookie="fides_locale=fr-CA"`): typically used
 * to pass page-specific options from your server to the browser, or from a
 * native app -> webview, etc.
 *
 * If the same option is provided in multiple ways, they are evaluated in that
 * order of precedence:
 * 1. Query Params (top priority)
 * 2. Window Object (second priority)
 * 3. Cookie Values (last priority)
 *
 * @example
 * ```html
 * <head>
 *   <script>
 *     // Configure FidesJS options using the window.fides_overrides object
 *     window.fides_overrides = {
 *       fides_disable_banner: true,
 *       fides_embed: true,
 *       fides_locale: "es",
 *     };
 *   </script>
 *   <script src="path/to/fides.js"></script>
 * </head>
 * ```
 */
export interface FidesOptions {
  /**
   * When `true`, disable the FidesJS banner from being shown.
   * 
   * Defaults to `false`.
   */ 
  fides_disable_banner: boolean;

  /**
   * When `true`, disable FidesJS from saving user consent preferences to the Fides API
   * 
   * Defaults to `false`.
   */ 
  fides_disable_save_api: boolean;

  /**
   * When `true`, require FidesJS to "embed" it's UI into a specific `<div>` on
   * the page, instead of as an overlay over the `<body>` itself. This is useful
   * for creating a dedicated page to manage consent preferences on your site.
   * 
   * To use the `fides_embed` option, ensure that a DOM element with
   * `id="fides-embed-container"` exists on the page, which FidesJS will then
   * use as the parent element to render within.
   * 
   * NOTE: If you're using a JavaScript framework (e.g. React), ensure that you
   * do not re-render the parent `<div>` element, as this could remove the
   * FidesJS UI fully from the page!
   * 
   * Defaults to `false`.
   * 
   * @example
   * ```html
   * <head>
   *   <script>
   *     // Configure FidesJS to embed into the page
   *     window.fides_overrides = {
   *       fides_embed: true,
   *     };
   *   </script>
   *   <script src="path/to/fides.js"></script>
   * </head>
   * <body>
   *   <div id="fides-embed-container">
   *     <!-- FidesJS will render it's UI here! -->
   *   </div>
   * </body>
   * ```
   */ 
  fides_embed: boolean;

  /**
   * Override the browser's preferred locale (`navigator.language`) when
   * selecting the best translations for the FidesJS UI. 
   * 
   * Must be set to a `string` that is a valid language code (e.g. `"en-US"`,
   * `"fr"`, `"zh-CN"`). See https://developer.mozilla.org/en-US/docs/Web/API/Navigator/language
   * 
   * Defaults to `undefined`.
   */
  fides_locale: string;

  /**
   * TODO (PROD-1887): Add docs for using this option. Once added, remove the
   * @internal tag and rebuild!
   * 
   * @internal
   */
  fides_primary_color: string;

  /**
   * Override the current user's `fides_string` consent preferences (see {@link
   * Fides.fides_string}). Can be used to synchronize consent preferences for a
   * registered user from a custom backend, where the `fides_string` could be
   * provided by the server across multiple devices, etc.
   * selecting the best translations for the FidesJS UI. 
   * 
   * Defaults to `undefined`.
   */
  fides_string: string;

  /**
   * Override the value for `gdprApplies` set in the IAB TCF CMP API.  FidesJS
   * will always default this value to `true` (since the TCF experience will
   * typically only be enabled in locations where GDPR applies), but this can be
   * overriden at the page-level as needed. Only applicable to a TCF experience.
   * 
   * For more details, see the [TCF CMP API technical specification](https://github.com/InteractiveAdvertisingBureau/GDPR-Transparency-and-Consent-Framework/blob/master/TCFv2/IAB%20Tech%20Lab%20-%20CMP%20API%20v2.md#what-does-the-gdprapplies-value-mean)  * 
   * 
   * Defaults to `true`.
   */
  fides_tcf_gdpr_applies: boolean;
};
