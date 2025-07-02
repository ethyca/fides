import { createShopifyConsent } from "../../src/integrations/shopify";
import {
  NoticeConsent,
  UserConsentPreference,
} from "../../src/lib/consent-types";

describe("createShopifyConsent", () => {
  it("should return all true when all related fides consents are true", () => {
    const fidesConsent: NoticeConsent = {
      data_sales_and_sharing: true,
      analytics: true,
      functional: true,
    };
    const shopifyConsent = createShopifyConsent(fidesConsent);
    expect(shopifyConsent).toEqual({
      marketing: true,
      analytics: true,
      preferences: true,
      sale_of_data: true,
    });
  });

  it("should return all false when all related fides consents are false", () => {
    const fidesConsent: NoticeConsent = {
      data_sales_and_sharing: false,
      analytics: false,
      functional: false,
    };
    const shopifyConsent = createShopifyConsent(fidesConsent);
    expect(shopifyConsent).toEqual({
      marketing: false,
      analytics: false,
      preferences: false,
      sale_of_data: false,
    });
  });

  it("should omit a value if no related fides consent is given", () => {
    const fidesConsent: NoticeConsent = {
      analytics: false,
      functional: false,
    };
    const shopifyConsent = createShopifyConsent(fidesConsent);
    expect(shopifyConsent).toEqual({
      analytics: false,
      preferences: false,
      sale_of_data: false,
    });
  });

  it("should handle mixed consent", () => {
    const fidesConsent: NoticeConsent = {
      data_sales_and_sharing: true,
      analytics: false,
    };
    const shopifyConsent = createShopifyConsent(fidesConsent);
    expect(shopifyConsent).toEqual({
      marketing: true,
      analytics: false,
      sale_of_data: true,
    });
  });

  it("can use options to set sale_of_data_default", () => {
    const fidesConsent: NoticeConsent = {
      analytics: false,
      functional: false,
    };
    const shopifyConsent = createShopifyConsent(fidesConsent, {
      sale_of_data_default: true,
    });
    expect(shopifyConsent).toEqual({
      analytics: false,
      preferences: false,
      sale_of_data: true,
    });
  });

  it("should handle string consent values", () => {
    const fidesConsent: NoticeConsent = {
      data_sales_and_sharing: UserConsentPreference.OPT_IN,
      analytics: UserConsentPreference.OPT_OUT,
      functional: UserConsentPreference.ACKNOWLEDGE,
    };
    const shopifyConsent = createShopifyConsent(fidesConsent);
    expect(shopifyConsent).toEqual({
      marketing: true,
      analytics: false,
      preferences: true,
      sale_of_data: true,
    });
  });
});
