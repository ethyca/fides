import {
  makeConsentItems,
  makeDataUseConsent,
} from "~/features/consent/helpers";
import { ApiUserConsents, ConsentItem } from "~/features/consent/types";

describe("makeConsentItems", () => {
  const consentOptions = [
    {
      description: "Data shared with third parties",
      fidesDataUseKey: "third_party_sharing",
      highlight: true,
      name: "Third Party Sharing",
      url: "https://example.com/privacy#data-sales",
    },
    {
      description: "Configured description",
      fidesDataUseKey: "custom.use",
      highlight: true,
      name: "Custom",
      url: "https://example.com/privacy#custom",
    },
    {
      default: true,
      description: "Default opted in",
      fidesDataUseKey: "provide.service",
      highlight: false,
      name: "Provide a service",
      url: "https://example.com/privacy#provide-service",
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
        consentValue: false,
        defaultValue: false,
        description: "Data shared with third parties",
        fidesDataUseKey: "third_party_sharing",
        highlight: true,
        name: "Third Party Sharing",
        url: "https://example.com/privacy#data-sales",
      },
      {
        consentValue: true,
        defaultValue: false,
        description: "Custom API description",
        fidesDataUseKey: "custom.use",
        highlight: true,
        name: "Custom",
        url: "https://example.com/privacy#custom",
      },
      {
        defaultValue: true,
        description: "Default opted in",
        fidesDataUseKey: "provide.service",
        highlight: false,
        name: "Provide a service",
        url: "https://example.com/privacy#provide-service",
      },
    ]);
  });

  it("Creates default items when there is no API response data", () => {
    const items = makeConsentItems({}, consentOptions);

    expect(items).toEqual([
      {
        defaultValue: false,
        description: "Data shared with third parties",
        fidesDataUseKey: "third_party_sharing",
        highlight: true,
        name: "Third Party Sharing",
        url: "https://example.com/privacy#data-sales",
      },
      {
        defaultValue: false,
        description: "Configured description",
        fidesDataUseKey: "custom.use",
        highlight: true,
        name: "Custom",
        url: "https://example.com/privacy#custom",
      },
      {
        defaultValue: true,
        description: "Default opted in",
        fidesDataUseKey: "provide.service",
        highlight: false,
        name: "Provide a service",
        url: "https://example.com/privacy#provide-service",
      },
    ]);
  });
});

describe("makeDataUseConsent", () => {
  const irrelevantProps = {
    description: "",
    highlight: false,
    name: "",
    url: "https://example.com/privacy#data-sales",
  };
  const consentItems: ConsentItem[] = [
    {
      consentValue: false,
      defaultValue: false,
      fidesDataUseKey: "third_party_sharing",
      ...irrelevantProps,
    },
    {
      consentValue: true,
      defaultValue: false,
      fidesDataUseKey: "custom.use",
      ...irrelevantProps,
    },
    {
      consentValue: false,
      defaultValue: true,
      fidesDataUseKey: "not.default",
      ...irrelevantProps,
    },
    {
      defaultValue: true,
      fidesDataUseKey: "provide.service",
      ...irrelevantProps,
    },
  ];

  it("Merges the items into a map from Data Use to consent boolean", () => {
    expect(makeDataUseConsent(consentItems)).toEqual({
      third_party_sharing: false,
      "custom.use": true,
      "not.default": false,
      "provide.service": true,
    });
  });
});
