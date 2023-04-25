/***
 * TODO: description
 * 
 * Expected usage of this in an HTML file is:
 * ```
 * <script src="../dist/fides.js"></script>
 * <script>
 *   window.Fides.init({
 *     consent: {
 *       options: [...(default consent options here)]
 *     }
 *   });
 * </script>
 * ```
 */
import { gtm } from "./integrations/gtm";
import { meta } from "./integrations/meta";
import { shopify } from "./integrations/shopify";
import { ConsentConfig } from "./lib/consent-config";
import { getConsentContext } from "./lib/consent-context";
import { CookieKeyConsent, getConsentCookie, makeDefaults } from "./lib/cookie";

/**
 * Configuration options for the fides.js script
 */
export interface FidesConfig {
  consent: ConsentConfig;
}

type Fides = {
  consent: CookieKeyConsent;
  gtm: typeof gtm;
  init: typeof init;
  initialized: boolean;
  meta: typeof meta;
  shopify: typeof shopify;
}

declare global {
  interface Window {
    Fides: Fides;
  }
}

/**
 * Initialize the Fides object with configuration values
 */
const init = (config: FidesConfig) => {
  console.debug("Initializing fides.js...");
  // Configure the default values
  const context = getConsentContext();
  const defaults = makeDefaults({
    config: config.consent,
    context,
  });

  // Load any existing user preferences from the browser cookie
  const consent = getConsentCookie(defaults);

  // Initialize the window.Fides object
  // TODO: this shouldn't affect window.Fides, but instead a _Fides internal
  window.Fides.consent = consent;
  window.Fides.initialized = true;
}

// Define the window.Fides object (if running in a browser context)
if (typeof window !== "undefined") {
  const Fides: Fides = {
    consent: {},
    gtm,
    init,
    initialized: false,
    meta,
    shopify,
  };
  window.Fides = Fides;
}

// Export everything from ./lib/* to use when importing as a module
export * from "./lib/consent-config";
export * from "./lib/consent-context";
export * from "./lib/consent-value";
export * from "./lib/cookie";

export default Fides;
