/**
 * This script defines the browser script entrypoint for Fides consent logic. It is distributed
 * as `fides-consent.js` and is accessed from the `Fides` global variable.
 */

// This file is created at build time by `generateConsentConfig` in `rollup.config.js`.
import consentConfig from "./consent-config.json";

import { gtm } from "./integrations/gtm";
import { meta } from "./integrations/meta";
import { shopify } from "./integrations/shopify";
import { getConsentCookie } from "./lib/cookie";

const Fides = {
  /**
   * Immediately load the stored consent settings from the browser cookie.
   */
  consent: getConsentCookie(consentConfig.defaults),

  gtm,
  meta,
  shopify,
};

declare global {
  interface Window {
    Fides: typeof Fides;
  }
}

export default Fides;
