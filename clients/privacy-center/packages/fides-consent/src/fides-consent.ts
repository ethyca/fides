/**
 * This script defines the browser script entrypoint for Fides consent logic. It is distributed
 * as `fides-consent.js` and is accessed from the `Fides` global variable.
 */

// This file is created at build time by `generateConsentConfig` in `rollup.config.js`.
import consentConfig from "./consent-config.json";

import { gtm } from "./integrations/gtm";
import { meta } from "./integrations/meta";
import { shopify } from "./integrations/shopify";
import { ConsentConfig } from "./lib/consent-config";
import { getConsentContext } from "./lib/consent-context";
import { getConsentCookie, makeDefaults } from "./lib/cookie";

const config: ConsentConfig = consentConfig;
const context = getConsentContext();
const defaults = makeDefaults({
  config,
  context,
});

/**
 * Immediately load the stored consent settings from the browser cookie.
 */
const consent = getConsentCookie(defaults);

const Fides = {
  consent,

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
