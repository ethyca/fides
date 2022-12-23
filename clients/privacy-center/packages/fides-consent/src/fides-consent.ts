/**
 * This script defines the browser script entrypoint for Fides consent logic. It is distributed
 * as `fides-consent.js` and is accessed from the `Fides` global variable.
 */

import { getConsentCookie } from "./lib/cookie";

const Fides = {
  /**
   * Immediately load the stored consent settings from the browser cookie.
   */
  consent: getConsentCookie(),

  /**
   * Call this to configure Google Tag Manager. The user's consent choices will be
   * pushed into GTM's `dataLayer` under `Fides.consent`.
   */
  gtm() {
    if (typeof window === "undefined") {
      return;
    }

    const dataLayer: any[] = (window as any)?.dataLayer ?? [];
    dataLayer.push({
      Fides: {
        consent: Fides.consent,
      },
    });
  },
};

export default Fides;
