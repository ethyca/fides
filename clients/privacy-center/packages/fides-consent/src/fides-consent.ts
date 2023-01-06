/**
 * This script defines the browser script entrypoint for Fides consent logic. It is distributed
 * as `fides-consent.js` and is accessed from the `Fides` global variable.
 */

// This file is created at build time by `generateConsentConfig` in `rollup.config.js`.
import consentConfig from "./consent-config.json";

import { getConsentCookie } from "./lib/cookie";

declare global {
  interface Window {
    /** GTM */
    dataLayer?: any[];

    /** Shopify */
    Shopify?: {
      loadFeatures(
        features: Array<{ name: string; version: string }>,
        callback: (error: Error) => void
      ): void;
      customerPrivacy?: {
        setTrackingConsent(consent: boolean, callback: () => void): void;
      };
    };
  }
}

const Fides = {
  /**
   * Immediately load the stored consent settings from the browser cookie.
   */
  consent: getConsentCookie(consentConfig.defaults),

  /**
   * Call Fides.gtm to configure Google Tag Manager. The user's consent choices will be
   * pushed into GTM's `dataLayer` under `Fides.consent`.
   */
  gtm() {
    const dataLayer = window?.dataLayer ?? [];
    dataLayer.push({
      Fides: {
        consent: Fides.consent,
      },
    });
  },

  /**
   * Call Fides.shopify to configure Shopify customer privacy. Currently the only consent option
   * Shopify allows to be configured is user tracking.
   *
   * @example
   * Fides.shopify({ tracking: Fides.consent.data_sales })
   */
  shopify(options: { tracking: boolean | undefined }) {
    const Shopify = window?.Shopify;
    if (!Shopify) {
      throw Error(
        "Fides.shopify was called but Shopify is not present in the page."
      );
    }

    const applyOptions = () => {
      if (!Shopify.customerPrivacy) {
        throw Error("Fides could not access Shopify's customerPrivacy API");
      }

      Shopify.customerPrivacy.setTrackingConsent(
        Boolean(options.tracking),
        () => {}
      );
    };

    // If the API is already present, simply call it.
    if (Shopify.customerPrivacy) {
      applyOptions();
      return;
    }

    // Otherwise we need to load the feature before applying the options.
    Shopify.loadFeatures(
      [
        {
          name: "consent-tracking-api",
          version: "0.1",
        },
      ],
      (error) => {
        if (error) {
          throw Error("Fides could not load Shopify's consent-tracking-api");
        }

        applyOptions();
      }
    );
  },
};

export default Fides;
