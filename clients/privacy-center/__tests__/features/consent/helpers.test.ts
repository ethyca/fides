import {
  makeConsentItems,
  makeCookieKeyConsent,
} from "~/features/consent/helpers";
import { ApiUserConsents, ConsentItem } from "~/features/consent/types";
import { ConfigConsentOption } from "~/types/config";

describe("makeConsentItems", () => {
  const consentOptions: ConfigConsentOption[] = [
    {
      cookieKeys: ["data_sharing"],
      default: false,
      description: "Data shared with third parties",
      fidesDataUseKey: "third_party_sharing",
      highlight: true,
      name: "Third Party Sharing",
      url: "https://example.com/privacy#data-sales",
      executable: true,
    },
    {
      cookieKeys: ["custom_key"],
      default: false,
      description: "Configured description",
      fidesDataUseKey: "custom.use",
      highlight: true,
      name: "Custom",
      url: "https://example.com/privacy#custom",
      executable: false,
    },
    {
      cookieKeys: [],
      default: true,
      description: "Default opted in",
      fidesDataUseKey: "provide.service",
      name: "Provide a service",
      url: "https://example.com/privacy#provide-service",
      executable: false,
    },
  ];

  it("Matches config options with API response data", () => {
    const data: ApiUserConsents = {
      consent: [
        {
          data_use: "third_party_sharing",
          opt_in: false,
        },
        {
          data_use: "custom.use",
          data_use_description: "Custom API description",
          opt_in: true,
        },
      ],
    };

    const items = makeConsentItems(data, consentOptions);

    expect(items).toEqual([
      {
        cookieKeys: ["data_sharing"],
        consentValue: false,
        defaultValue: false,
        description: "Data shared with third parties",
        fidesDataUseKey: "third_party_sharing",
        highlight: true,
        name: "Third Party Sharing",
        url: "https://example.com/privacy#data-sales",
        executable: true,
      },
      {
        cookieKeys: ["custom_key"],
        consentValue: true,
        defaultValue: false,
        description: "Custom API description",
        fidesDataUseKey: "custom.use",
        highlight: true,
        name: "Custom",
        url: "https://example.com/privacy#custom",
        executable: false,
      },
      {
        cookieKeys: [],
        defaultValue: true,
        description: "Default opted in",
        fidesDataUseKey: "provide.service",
        highlight: false,
        name: "Provide a service",
        url: "https://example.com/privacy#provide-service",
        executable: false,
      },
    ]);
  });

  it("Creates default items when there is no API response data", () => {
    const items = makeConsentItems({}, consentOptions);

    expect(items).toEqual([
      {
        cookieKeys: ["data_sharing"],
        defaultValue: false,
        description: "Data shared with third parties",
        fidesDataUseKey: "third_party_sharing",
        highlight: true,
        name: "Third Party Sharing",
        url: "https://example.com/privacy#data-sales",
        executable: true,
      },
      {
        cookieKeys: ["custom_key"],
        defaultValue: false,
        description: "Configured description",
        fidesDataUseKey: "custom.use",
        highlight: true,
        name: "Custom",
        url: "https://example.com/privacy#custom",
        executable: false,
      },
      {
        cookieKeys: [],
        defaultValue: true,
        description: "Default opted in",
        fidesDataUseKey: "provide.service",
        highlight: false,
        name: "Provide a service",
        url: "https://example.com/privacy#provide-service",
        executable: false,
      },
    ]);
  });
});

describe("makeCookieKeyConsent", () => {
  // Only the consent booleans and cookieKeys matter for resolving the cookie mapping.
  const irrelevantProps = {
    description: "",
    highlight: false,
    name: "",
    fidesDataUseKey: "",
    url: "https://example.com/privacy#data-sales",
  };

  const dataSalesWithConsent: ConsentItem = {
    cookieKeys: ["data_sales"],
    consentValue: true,
    defaultValue: false,
    ...irrelevantProps,
  };
  const dataSalesWithoutConsent: ConsentItem = {
    cookieKeys: ["data_sales", "google_ads"],
    consentValue: false,
    defaultValue: false,
    ...irrelevantProps,
  };
  const dataSharingWithConsent: ConsentItem = {
    cookieKeys: ["data_sharing", "google_analytics"],
    consentValue: true,
    defaultValue: false,
    ...irrelevantProps,
  };
  const dataSharingWithDefaultConsent: ConsentItem = {
    cookieKeys: ["data_sharing", "google_analytics"],
    defaultValue: true,
    ...irrelevantProps,
  };
  const analyticsWithoutConsent: ConsentItem = {
    cookieKeys: ["google_analytics"],
    consentValue: false,
    defaultValue: true,
    ...irrelevantProps,
  };

  it("Applies default consent", () => {
    expect(makeCookieKeyConsent([dataSharingWithDefaultConsent])).toEqual({
      data_sharing: true,
      google_analytics: true,
    });
  });

  it("Allows overriding default consent", () => {
    expect(makeCookieKeyConsent([analyticsWithoutConsent])).toEqual({
      google_analytics: false,
    });
  });

  it("Removes consent if some matching keys don't have consent", () => {
    expect(
      makeCookieKeyConsent([dataSalesWithConsent, dataSalesWithoutConsent])
    ).toEqual({
      data_sales: false,
      google_ads: false,
    });
  });

  it("Applies consent if all matching keys have consent", () => {
    expect(
      makeCookieKeyConsent([
        dataSharingWithConsent,
        dataSharingWithDefaultConsent,
      ])
    ).toEqual({
      data_sharing: true,
      google_analytics: true,
    });
  });
});
