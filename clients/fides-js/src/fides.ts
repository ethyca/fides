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
 *     }
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
import { ConsentConfig } from "./lib/consent-config";
import { getConsentContext } from "./lib/consent-context";
import { initFidesConsent } from "./lib/consent";
import {
  CookieKeyConsent,
  CookieIdentity,
  CookieMeta,
  getOrMakeFidesCookie,
  makeConsentDefaults,
} from "./lib/cookie";
import { ConsentBannerOptions } from "./lib/consent-types";
import { getBannerOptions } from "./lib/consent-utils";

export interface FidesConfig {
  consent: ConsentConfig;
  bannerOptions?: ConsentBannerOptions;
}

type Fides = {
  consent: CookieKeyConsent;
  fides_meta: CookieMeta;
  getBannerOptions: () => ConsentBannerOptions;
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
  // Configure the default values
  const context = getConsentContext();
  const defaults = makeConsentDefaults({
    config: config.consent,
    context,
  });

  // Load any existing user preferences from the browser cookie
  const cookie = getOrMakeFidesCookie(defaults);

  await initFidesConsent(defaults, config.bannerOptions);
  // Initialize the window.Fides object
  _Fides.consent = cookie.consent;
  _Fides.getBannerOptions = getBannerOptions;
  _Fides.fides_meta = cookie.fides_meta;
  _Fides.identity = cookie.identity;

  _Fides.initialized = true;
};

// The global Fides object; this is bound to window.Fides if available
_Fides = {
  consent: {},
  fides_meta: {},
  getBannerOptions,
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
