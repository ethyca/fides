import { ConsentContext } from "fides-js";

import { makeNoticeConsent } from "~/features/consent/helpers";
import { ConfigConsentOption } from "~/types/api";

describe("makeNoticeConsent", () => {
  // Some display options don't matter for these tests.
  const irrelevantProps = {
    description: "",
    highlight: false,
    name: "",
    url: "https://example.com/privacy#data-sales",
  };

  describe("With blank consent context", () => {
    const consentContext: ConsentContext = {};

    const dataUseSales: ConfigConsentOption = {
      fidesDataUseKey: "data_use.sales",
      cookieKeys: ["data_sales"],
      default: false,
      ...irrelevantProps,
    };
    const dataUseSalesGads: ConfigConsentOption = {
      fidesDataUseKey: "data_use.sales.gads",
      cookieKeys: ["data_sales", "google_ads"],
      default: false,
      ...irrelevantProps,
    };
    const dataUseSharingGanDefault: ConfigConsentOption = {
      fidesDataUseKey: "data_use.sharing.gan.default",
      cookieKeys: ["data_sharing", "google_analytics"],
      default: true,
      ...irrelevantProps,
    };
    const dataUseGanDefault: ConfigConsentOption = {
      cookieKeys: ["google_analytics"],
      fidesDataUseKey: "data_use.gan.default",
      default: true,
      ...irrelevantProps,
    };

    it("applies default consent", () => {
      expect(
        makeNoticeConsent({
          consentOptions: [dataUseSharingGanDefault],
          fidesKeyToConsent: {},
          consentContext,
        }),
      ).toEqual({
        data_sharing: true,
        google_analytics: true,
      });
    });

    it("allows overriding default consent", () => {
      expect(
        makeNoticeConsent({
          consentOptions: [dataUseGanDefault],
          fidesKeyToConsent: {
            [dataUseGanDefault.fidesDataUseKey]: false,
          },
          consentContext,
        }),
      ).toEqual({
        google_analytics: false,
      });
    });

    it("removes consent if some matching keys don't have consent", () => {
      expect(
        makeNoticeConsent({
          consentOptions: [dataUseSales, dataUseSalesGads],
          fidesKeyToConsent: {
            [dataUseSales.fidesDataUseKey]: false,
            [dataUseSalesGads.fidesDataUseKey]: true,
          },
          consentContext,
        }),
      ).toEqual({
        data_sales: false,
        google_ads: true,
      });
    });

    it("applies consent if all matching keys have consent", () => {
      expect(
        makeNoticeConsent({
          consentOptions: [dataUseSales, dataUseSalesGads],
          fidesKeyToConsent: {
            [dataUseSales.fidesDataUseKey]: true,
            [dataUseSalesGads.fidesDataUseKey]: true,
          },
          consentContext,
        }),
      ).toEqual({
        data_sales: true,
        google_ads: true,
      });
    });
  });

  describe("With GPC enabled in the consent context", () => {
    const consentContext: ConsentContext = {
      globalPrivacyControl: true,
    };

    const dataUseSalesDefaultNoGpc: ConfigConsentOption = {
      fidesDataUseKey: "data_use.sales",
      cookieKeys: ["data_sales"],
      default: {
        value: true,
        globalPrivacyControl: false,
      },
      ...irrelevantProps,
    };

    it("applies the GPC default consent", () => {
      expect(
        makeNoticeConsent({
          consentOptions: [dataUseSalesDefaultNoGpc],
          fidesKeyToConsent: {},
          consentContext,
        }),
      ).toEqual({
        data_sales: false,
      });
    });

    it("allows overriding the GPC default consent", () => {
      expect(
        makeNoticeConsent({
          consentOptions: [dataUseSalesDefaultNoGpc],
          fidesKeyToConsent: {
            [dataUseSalesDefaultNoGpc.fidesDataUseKey]: true,
          },
          consentContext,
        }),
      ).toEqual({
        data_sales: true,
      });
    });
  });
});
