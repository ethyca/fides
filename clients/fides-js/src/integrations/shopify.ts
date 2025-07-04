import { MARKETING_CONSENT_KEYS } from "../lib/consent-constants";
import { NoticeConsent } from "../lib/consent-types";
import { processExternalConsentValue } from "../lib/shared-consent-utils";

export interface ShopifyOptions {
  sale_of_data_default?: boolean;
}

declare global {
  interface Window {
    Shopify?: {
      /** https://shopify.dev/docs/api/customer-privacy#loading-the-customer-privacy-api */
      loadFeatures(
        features: Array<{ name: string; version: string }>,
        callback: (error: Error) => void,
      ): void;
      currentVisitorConsent(): ShopifyConsentResponse;
      customerPrivacy?: {
        /** https://shopify.dev/docs/api/customer-privacy#collect-and-register-consent */
        setTrackingConsent(consent: ShopifyConsent, callback: () => void): void;
      };
    };
  }
}

const CONSENT_MAP = {
  marketing: MARKETING_CONSENT_KEYS,
  sale_of_data: MARKETING_CONSENT_KEYS,
  analytics: ["analytics"],
  preferences: ["functional"],
};

type ShopifyConsentResponse = {
  marketing: "yes" | "no" | "";
  analytics: "yes" | "no" | "";
  preferences: "yes" | "no" | "";
  sale_of_data: "yes" | "no" | "";
};

type ShopifyConsent = {
  marketing: boolean;
  analytics: boolean;
  preferences: boolean;
  sale_of_data: boolean;
};

export function createShopifyConsent(
  fidesConsent: NoticeConsent,
  options?: ShopifyOptions,
): ShopifyConsent {
  const processedConsent = Object.fromEntries(
    Object.entries(fidesConsent).map(([k, v]) => [
      k,
      processExternalConsentValue(v),
    ]),
  );
  const result: Partial<ShopifyConsent> = {};

  Object.entries(CONSENT_MAP).forEach(([key, values]) => {
    const hasTrue = values.some((value) => processedConsent[value] === true);
    const hasFalse = values.some((value) => processedConsent[value] === false);

    if (hasTrue) {
      result[key as keyof ShopifyConsent] = true;
    } else if (hasFalse) {
      result[key as keyof ShopifyConsent] = false;
    }
  });

  // Ensure sale_of_data is always set
  if (result.sale_of_data === undefined) {
    result.sale_of_data = options?.sale_of_data_default ?? false;
  }

  return result as ShopifyConsent;
}

// Helper function to push consent to Shopify from a Fides Consent object
const pushConsentToShopify = (
  fidesConsent: NoticeConsent,
  options?: ShopifyOptions,
) => {
  window.Shopify!.customerPrivacy!.setTrackingConsent(
    createShopifyConsent(fidesConsent, options),
    () => {},
  );
};

const applyOptions = (options?: ShopifyOptions) => {
  if (!window.Shopify?.customerPrivacy) {
    // eslint-disable-next-line no-console
    console.error("Fides could not access Shopify's customerPrivacy API");
  }
  // Listen for Fides events and push them to Shopify
  window.addEventListener("FidesReady", (event) =>
    pushConsentToShopify(event.detail.consent, options),
  );
  window.addEventListener("FidesUpdating", (event) =>
    pushConsentToShopify(event.detail.consent, options),
  );
  window.addEventListener("FidesUpdated", (event) =>
    pushConsentToShopify(event.detail.consent, options),
  );

  // If Fides was already initialized, push consent to Shopify immediately
  if (window.Fides?.initialized && window.Fides.cookie) {
    // cookie will always be present in the Fides object after initialization. Event details above also use the cookie.consent so let's stay consistent.
    pushConsentToShopify(window.Fides.cookie.consent, options);
  }
};

/**
 * Call Fides.shopify to configure Shopify customer privacy.
 */
export const shopify = (options?: ShopifyOptions) => {
  let timeoutId: ReturnType<typeof setTimeout>;
  let pollId: ReturnType<typeof setTimeout>;

  const cleanup = () => {
    clearTimeout(timeoutId);
    clearTimeout(pollId);
  };

  // Poll for the Shopify API to be available
  const poll = () => {
    if (window.Shopify) {
      cleanup();

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
      return;
    }

    // Continue polling every 200ms
    pollId = setTimeout(poll, 200);
  };

  // Set up 3-second timeout
  timeoutId = setTimeout(() => {
    cleanup();
    throw Error(
      "Fides.shopify was called but Shopify is not present in the page after 3 seconds.",
    );
  }, 3000);

  // Start polling immediately
  poll();
};
