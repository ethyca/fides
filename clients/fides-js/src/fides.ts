/**
 * Fides.js: Javascript library for Fides (https://github.com/ethyca/fides)
 *
 * This JS module provides easy access to interact with Fides from a webpage, including the ability to:
 * - initialize the page with default consent options (e.g. opt-out of advertising cookies, opt-in to analytics, etc.)
 * - read/write the current user's consent preferences to their browser as a cookie
 * - push the current user's consent preferences to other systems via integrations (Google Tag Manager, Meta, etc.)
 *
 * See https://fid.es for more information!
 *
 * Basic usage of this module in an HTML page is:
 * ```
 * <script src="https://privacy.{company}.com/fides.js"></script>
 * <script>
 *   window.Fides.init({
 *     consent: {
 *       options: [{
 *         cookieKeys: ["data_sales"],
 *         default: true,
 *         fidesDataUseKey: "advertising"
 *       }]
 *     },
 *     experience: {},
 *     geolocation: {},
 *     options: {
 *           debug: true,
 *           isDisabled: false,
 *           isGeolocationEnabled: false,
 *           geolocationApiUrl: "",
 *           privacyCenterUrl: "http://localhost:3000"
 *         }
 *   });
 * </script>
 * ```
 *
 * ...and later:
 * ```
 * <script>
 *   // Query user consent preferences
 *   if (window.Fides.consent.data_sales) {
 *     // ...enable advertising scripts
 *   }
 * ```
 */
import { gtm } from "./integrations/gtm";
import { meta } from "./integrations/meta";
import { shopify } from "./integrations/shopify";
import { getConsentContext } from "./lib/consent-context";
import { initFidesConsent } from "./lib/consent";
import {
  CookieKeyConsent,
  CookieIdentity,
  CookieMeta,
  getOrMakeFidesCookie,
  makeConsentDefaults,
} from "./lib/cookie";
import {
  defaultFidesOptions,
  ExperienceConfig,
  FidesConfig,
  FidesOptions,
  UserGeolocation,
} from "./lib/consent-types";

export type Fides = {
  consent: CookieKeyConsent;
  experience?: ExperienceConfig;
  geolocation?: UserGeolocation;
  options: FidesOptions;
  fides_meta: CookieMeta;
  gtm: typeof gtm;
  identity: CookieIdentity;
  init: typeof init;
  initialized: boolean;
  meta: typeof meta;
  shopify: typeof shopify;
};

declare global {
  interface Window {
    Fides: Fides;
  }
}

// The global Fides object; this is bound to window.Fides if available
// eslint-disable-next-line no-underscore-dangle,@typescript-eslint/naming-convention
let _Fides: Fides;

/**
 * Initialize the global Fides object with the given configuration values
 */
const init = async (config: FidesConfig) => {
  // passed-in config should override default options
  // eslint-disable-next-line no-param-reassign
  config.options = { ...defaultFidesOptions, ...config.options };
  // Configure the default consent values
  const context = getConsentContext();
  const consentDefaults = makeConsentDefaults({
    config: config.consent,
    context,
  });

  // Load any existing user preferences from the browser cookie
  const cookie = getOrMakeFidesCookie(consentDefaults);

  await initFidesConsent(config);

  // Initialize the window.Fides object
  _Fides.consent = cookie.consent;
  _Fides.fides_meta = cookie.fides_meta;
  _Fides.identity = cookie.identity;
  _Fides.experience = config.experience;
  _Fides.geolocation = config.geolocation;
  _Fides.options = config.options;

  _Fides.initialized = true;
};

// The global Fides object; this is bound to window.Fides if available
_Fides = {
  consent: {},
  experience: undefined,
  geolocation: {},
  options: { ...defaultFidesOptions, privacyCenterUrl: "" },
  fides_meta: {},
  identity: {},
  gtm,
  init,
  initialized: false,
  meta,
  shopify,
};

if (typeof window !== "undefined") {
  window.Fides = _Fides;
}

// Export everything from ./lib/* to use when importing fides.mjs as a module
export * from "./lib/consent";
export * from "./components/ConsentBanner";
export * from "./lib/consent-config";
export * from "./lib/consent-context";
export * from "./lib/consent-types";
export * from "./lib/consent-utils";
export * from "./lib/consent-value";
export * from "./lib/cookie";

export default Fides;
