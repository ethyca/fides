import { MARKETING_CONSENT_KEYS } from "../lib/consent-constants";
import { NoticeConsent } from "../lib/consent-types";

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
  sale_of_data: [
    "marketing",
    "data_sales_and_sharing",
    "data_sales_sharing_gpp_us_state",
    "data_sharing_gpp_us_state",
    "data_sales_gpp_us_state",
    "targeted_advertising_gpp_us_state",
  ],
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
  marketing: boolean | undefined;
  analytics: boolean | undefined;
  preferences: boolean | undefined;
  sale_of_data: boolean;
};

function createShopifyConsent(
  fidesConsent: Record<string, boolean>,
): ShopifyConsent {
  const consent = Object.fromEntries(
    Object.entries(CONSENT_MAP).map(([key, values]) => [
      key,
      values.some((value) => fidesConsent[value] === true) ||
        (values.some((value) => fidesConsent[value] === false)
          ? false
          : undefined),
    ]),
  ) as Partial<ShopifyConsent>;

  // Ensure sale_of_data is always boolean
  consent.sale_of_data = consent.sale_of_data ?? false;

  return consent as ShopifyConsent;
}

// Helper function to push consent to Shopify from a Fides Consent object
const pushConsentToShopify = (fidesConsent: NoticeConsent) => {
  // @ts-ignore - Shopify is loaded at this point
  window.Shopify.customerPrivacy.setTrackingConsent(
    createShopifyConsent(fidesConsent),
    () => {},
  );
};

const applyOptions = () => {
  if (!window.Shopify?.customerPrivacy) {
    // eslint-disable-next-line no-console
    console.error("Fides could not access Shopify's customerPrivacy API");
  }
  // Listen for Fides events and push them to Shopify
  window.addEventListener("FidesInitialized", (event) =>
    pushConsentToShopify(event.detail.consent),
  );
  window.addEventListener("FidesUpdating", (event) =>
    pushConsentToShopify(event.detail.consent),
  );
  window.addEventListener("FidesUpdated", (event) =>
    pushConsentToShopify(event.detail.consent),
  );

  // If Fides was already initialized, push consent to Shopify immediately
  if (window.Fides?.initialized) {
    pushConsentToShopify(window.Fides.consent);
  }
};

/**
 * Call Fides.shopify to configure Shopify customer privacy.
 */
export const shopify = () => {
  setTimeout(() => {
    if (!window.Shopify) {
      throw Error(
        "Fides.shopify was called but Shopify is not present in the page.",
      );
    }
    // If the API is already present, simply call it.
    if (window.Shopify.customerPrivacy) {
      applyOptions();
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

        applyOptions();
      },
    );
  }, 3000);
};
