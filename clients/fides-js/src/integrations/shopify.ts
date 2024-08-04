declare global {
  interface Window {
    Shopify?: {
      /** https://shopify.dev/api/consent-tracking#loading-pattern-for-visitor-tracking */
      loadFeatures(
        features: Array<{ name: string; version: string }>,
        callback: (error: Error) => void,
      ): void;
      customerPrivacy?: {
        /** https://shopify.dev/api/consent-tracking#settrackingconsent-consent-boolean-callback-function */
        setTrackingConsent(consent: boolean, callback: () => void): void;
      };
    };
  }
}

type ShopifyOptions = {
  tracking: boolean | undefined;
};

const applyOptions = (options: ShopifyOptions) => {
  if (!window.Shopify?.customerPrivacy) {
    throw Error("Fides could not access Shopify's customerPrivacy API");
  }

  window.Shopify.customerPrivacy.setTrackingConsent(
    Boolean(options.tracking),
    () => {},
  );
};

/**
 * Call Fides.shopify to configure Shopify customer privacy. Currently the only consent option
 * Shopify allows to be configured is user tracking.
 *
 * DEFER: Update this integration to support async Fides events
 *
 * @example
 * Fides.shopify({ tracking: Fides.consent.data_sales })
 */
export const shopify = (options: ShopifyOptions) => {
  if (!window.Shopify) {
    throw Error(
      "Fides.shopify was called but Shopify is not present in the page.",
    );
  }

  // If the API is already present, simply call it.
  if (window.Shopify.customerPrivacy) {
    applyOptions(options);
    return;
  }

  // Otherwise we need to load the feature before applying the options.
  window.Shopify.loadFeatures(
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

      applyOptions(options);
    },
  );
};
