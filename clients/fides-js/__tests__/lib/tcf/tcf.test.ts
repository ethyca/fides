import { TCString } from "@iabtechlabtcf/core";

import { PrivacyExperience, UserConsentPreference } from "~/lib/consent-types";
import { generateFidesString } from "~/lib/tcf";
import { FIDES_SEPARATOR } from "~/lib/tcf/constants";
import {
  GVLJson,
  TCFFeatureRecord,
  TCFPurposeConsentRecord,
  TCFPurposeLegitimateInterestsRecord,
  TCFVendorLegitimateInterestsRecord,
} from "~/lib/tcf/types";

describe("generateFidesString", () => {
  // Test TCF data:
  const mockGvl: GVLJson = {
    vendors: {
      740: {
        id: 740,
        name: "Test Vendor 740",
        purposes: [1, 2, 3],
        legIntPurposes: [2, 7, 8],
        flexiblePurposes: [],
        specialPurposes: [1],
        features: [1, 2],
        specialFeatures: [1],
        policyUrl: "https://test.com/privacy",
        usesCookies: true,
        cookieMaxAgeSeconds: 86400,
        cookieRefresh: false,
        usesNonCookieAccess: false,
      },
      254: {
        id: 254,
        name: "Test Vendor 254",
        purposes: [1, 4, 7],
        legIntPurposes: [],
        flexiblePurposes: [],
        specialPurposes: [2],
        features: [3],
        specialFeatures: [],
        policyUrl: "https://test2.com/privacy",
        usesCookies: true,
        cookieMaxAgeSeconds: 86400,
        cookieRefresh: false,
        usesNonCookieAccess: false,
      },
    },
    purposes: {
      1: {
        id: 1,
        name: "Store and/or access information on a device",
        description:
          "Cookies, device identifiers, or other information can be stored or accessed on your device for the purposes presented to you.",
      },
      2: {
        id: 2,
        name: "Select basic ads",
        description:
          "Ads can be shown to you based on the content you're viewing, the app you're using, your approximate location, or your device type.",
      },
      3: {
        id: 3,
        name: "Create a personalised ads profile",
        description:
          "A profile can be built about you and your interests to show you personalised ads that are relevant to you.",
      },
      4: {
        id: 4,
        name: "Select personalised ads",
        description:
          "Personalised ads can be shown to you based on a profile about you.",
      },
      7: {
        id: 7,
        name: "Measure ad performance",
        description:
          "The performance and effectiveness of ads that you see or interact with can be measured.",
      },
      8: {
        id: 8,
        name: "Measure content performance",
        description:
          "The performance and effectiveness of content that you see or interact with can be measured.",
      },
      10: {
        id: 10,
        name: "Develop and improve products",
        description:
          "Your data can be used to improve existing systems and software, and to develop new products.",
      },
    },
    specialPurposes: {
      1: {
        id: 1,
        name: "Ensure security, prevent fraud, and debug",
        description:
          "Your data can be used to monitor for and prevent fraudulent activity, and ensure systems and processes work properly and securely.",
      },
      2: {
        id: 2,
        name: "Technically deliver ads or content",
        description:
          "Your device can receive and send information that allows you to see and interact with ads and content.",
      },
    },
    features: {
      1: {
        id: 1,
        name: "Match and combine offline data sources",
        description:
          "Data from offline data sources can be combined with your online activity in support of one or more purposes.",
      },
      2: {
        id: 2,
        name: "Link different devices",
        description:
          "Different devices can be determined as belonging to you or your household in support of one or more purposes.",
      },
      3: {
        id: 3,
        name: "Receive and use automatically-sent device characteristics for identification",
        description:
          "Your device might be distinguished from other devices based on information it automatically sends, such as IP address or browser type.",
      },
    },
    specialFeatures: {
      1: {
        id: 1,
        name: "Use precise geolocation data",
        description:
          "Your precise geolocation data can be used in support of one or more purposes.",
      },
    },
    stacks: {
      1: {
        id: 1,
        name: "Basic ads",
        description: "Basic ads stack",
        purposes: [1, 2, 3],
        specialFeatures: [],
      },
      2: {
        id: 2,
        name: "Personalized ads",
        description: "Personalized ads stack",
        purposes: [1, 2, 3, 4],
        specialFeatures: [],
      },
      3: {
        id: 3,
        name: "Ad measurement",
        description: "Ad measurement stack",
        purposes: [7],
        specialFeatures: [],
      },
      4: {
        id: 4,
        name: "Content measurement",
        description: "Content measurement stack",
        purposes: [8],
        specialFeatures: [],
      },
    },
    dataCategories: {
      1: {
        id: 1,
        name: "IP addresses",
        description: "IP address and derived geographic location",
      },
      2: {
        id: 2,
        name: "Cookies and similar tech",
        description: "Cookie identifiers and similar technologies",
      },
    },
    vendorListVersion: 3,
    tcfPolicyVersion: 2,
    lastUpdated: "2023-01-01T00:00:00Z",
    gvlSpecificationVersion: 3,
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const mockFeatures: TCFFeatureRecord[] = [
    {
      id: 1,
      name: "Match and combine offline data sources",
      description: "Feature 1 description",
      default_preference: UserConsentPreference.ACKNOWLEDGE,
      vendors: [
        {
          id: "gvl.740",
          name: "Vendor 740",
        },
      ],
      systems: [],
    },
    {
      id: 2,
      name: "Link different devices",
      description: "Feature 2 description",
      default_preference: UserConsentPreference.ACKNOWLEDGE,
      vendors: [
        {
          id: "gvl.740",
          name: "Vendor 740",
        },
      ],
      systems: [],
    },
    {
      id: 3,
      name: "Receive and use automatically-sent device characteristics for identification",
      description: "Feature 3 description",
      default_preference: UserConsentPreference.ACKNOWLEDGE,
      vendors: [
        {
          id: "gvl.740",
          name: "Vendor 740",
        },
        {
          id: "gvl.254",
          name: "Vendor 254",
        },
      ],
      systems: [],
    },
  ];
  const mockTcfPurposeConsents: TCFPurposeConsentRecord[] = [
    {
      id: 1,
      name: "Store and/or access information on a device",
      description: "Purpose 1 description",
      illustrations: [],
      data_uses: [],
      default_preference: UserConsentPreference.OPT_IN,
      vendors: [
        {
          id: "gvl.740",
          name: "Test Vendor 740",
        },
        {
          id: "gvl.254",
          name: "Test Vendor 254",
        },
      ],
      systems: [],
    },
    {
      id: 2,
      name: "Select basic ads",
      description: "Purpose 2 description",
      illustrations: [],
      data_uses: [],
      default_preference: UserConsentPreference.OPT_IN,
      vendors: [
        {
          id: "gvl.254",
          name: "Test Vendor 254",
        },
      ],
      systems: [],
    },
    {
      id: 3,
      name: "Create a personalised ads profile",
      description: "Purpose 3 description",
      illustrations: [],
      data_uses: [],
      default_preference: UserConsentPreference.OPT_IN,
      vendors: [
        {
          id: "gvl.740",
          name: "Test Vendor 740",
        },
        {
          id: "gvl.254",
          name: "Test Vendor 254",
        },
      ],
      systems: [],
    },
    {
      id: 4,
      name: "Select personalised ads",
      description: "Purpose 4 description",
      illustrations: [],
      data_uses: [],
      default_preference: UserConsentPreference.OPT_IN,
      vendors: [
        {
          id: "gvl.740",
          name: "Test Vendor 740",
        },
        {
          id: "gvl.254",
          name: "Test Vendor 254",
        },
      ],
      systems: [],
    },
    {
      id: 7,
      name: "Measure ad performance",
      description: "Purpose 7 description",
      illustrations: [],
      data_uses: [],
      default_preference: UserConsentPreference.OPT_IN,
      vendors: [
        {
          id: "gvl.254",
          name: "Test Vendor 254",
        },
      ],
      systems: [],
    },
  ];

  const mockTCfVendorsLegitimateInterest: TCFVendorLegitimateInterestsRecord[] =
    [
      {
        id: "gvl.740",
        name: "Test Vendor 740",
        default_preference: UserConsentPreference.OPT_IN,
        purpose_legitimate_interests: [
          {
            id: 2,
            name: "Select basic ads",
          },
          {
            id: 7,
            name: "Measure ad performance",
          },
          {
            id: 8,
            name: "Measure content performance",
          },
          {
            id: 10,
            name: "Develop and improve products",
          },
        ],
      },
    ];

  const mockTcfPurposeLegitimateInterests: TCFPurposeLegitimateInterestsRecord[] =
    [
      {
        id: 2,
        name: "Select basic ads",
        description: "Purpose 2 legitimate interest description",
        illustrations: [],
        data_uses: ["marketing.advertising.serving"],
        default_preference: UserConsentPreference.OPT_IN,
        vendors: [
          {
            id: "gvl.740",
            name: "Test Vendor 740",
          },
        ],
        systems: [],
      },
      {
        id: 7,
        name: "Measure ad performance",
        description: "Purpose 7 legitimate interest description",
        illustrations: [],
        data_uses: ["analytics.reporting.ad_performance"],
        default_preference: UserConsentPreference.OPT_IN,
        vendors: [
          {
            id: "gvl.740",
            name: "Test Vendor 740",
          },
        ],
        systems: [],
      },
      {
        id: 8,
        name: "Measure content performance",
        description: "Purpose 8 legitimate interest description",
        illustrations: [],
        data_uses: ["analytics.reporting.content_performance"],
        default_preference: UserConsentPreference.OPT_IN,
        vendors: [
          {
            id: "gvl.740",
            name: "Test Vendor 740",
          },
        ],
        systems: [],
      },
      {
        id: 10,
        name: "Develop and improve products",
        description: "Purpose 10 legitimate interest description",
        illustrations: [],
        data_uses: ["functional.service.improve"],
        default_preference: UserConsentPreference.OPT_IN,
        vendors: [
          {
            id: "gvl.740",
            name: "Test Vendor 740",
          },
        ],
        systems: [],
      },
    ];

  const experience = {
    gvl: mockGvl,
    tcf_purpose_consents: mockTcfPurposeConsents,
    tcf_purpose_legitimate_interests: mockTcfPurposeLegitimateInterests,
    tcf_legitimate_interests_consent: [],
    tcf_special_purposes: [],
    tcf_features: mockFeatures,
    tcf_vendor_legitimate_interests: mockTCfVendorsLegitimateInterest,
    minimal_tcf: false,
  } as unknown as PrivacyExperience;

  it("generates a valid Fides String when no publisher country code is provided", async () => {
    const fidesString = await generateFidesString({
      experience,
      tcStringPreferences: {
        customPurposesConsent: [],
        features: ["1", "2", "3"],
        purposesConsent: ["1", "2", "3", "4", "7"],
        purposesLegint: ["2", "7", "8", "10"],
        specialFeatures: ["1"],
        specialPurposes: ["1", "2"],
        vendorsConsent: ["gvl.740", "gvl.254"],
        vendorsLegint: ["gvl.740"],
      },
    });

    expect(fidesString).not.toBeNull();
    expect(fidesString).not.toBeUndefined();
    expect(fidesString).not.toBe("");

    const [tcfString] = fidesString.split(FIDES_SEPARATOR);

    expect(tcfString).not.toBe("");

    const decodedTCString = TCString.decode(tcfString);
    expect(decodedTCString.publisherCountryCode).toBe("AA");
  });

  it("generates a valid Fides String when a publisher country code is provided", async () => {
    const experienceWithPublisherCountryCode = {
      ...experience,
      tcf_publisher_country_code: "US",
    } as unknown as PrivacyExperience;

    const fidesString = await generateFidesString({
      experience: experienceWithPublisherCountryCode,
      tcStringPreferences: {
        customPurposesConsent: [],
        features: ["1", "2", "3"],
        purposesConsent: ["1", "2", "3", "4", "7"],
        purposesLegint: ["2", "7", "8", "10"],
        specialFeatures: ["1"],
        specialPurposes: ["1", "2"],
        vendorsConsent: ["gvl.740", "gvl.254"],
        vendorsLegint: ["gvl.740"],
      },
    });

    expect(fidesString).not.toBeNull();
    expect(fidesString).not.toBeUndefined();
    expect(fidesString).not.toBe("");

    const [tcfString] = fidesString.split(FIDES_SEPARATOR);

    expect(tcfString).not.toBe("");

    const decodedTCString = TCString.decode(tcfString);
    expect(decodedTCString.publisherCountryCode).toBe("US");
  });

  it("saves special purpose vendor to Vendor Legitimate Interest ", async () => {
    // This test only check for opt out, but is applicable regardless of consent choice
    const experienceWithSpecialPurposeVendors = {
      ...experience,
      tcf_vendor_relationships: [
        {
          id: "gvl.777",
          name: "Vendor with Purposes but no Special Purposes",
          special_purposes: [],
          features: [],
          special_features: [],
          url: "https://test.com/privacy",
        },
        {
          id: "gvl.888",
          name: "Special Purpose Vendor with Purposes",
          special_purposes: [1, 2, 3],
          features: [],
          special_features: [],
          url: "https://test.com/privacy",
        },
        {
          id: "gvl.999",
          name: "Special Purpose Only Vendor",
          special_purposes: [1, 2],
          features: [],
          special_features: [],
          url: "https://test.com/privacy",
        },
        {
          id: "gvl.740",
          name: "Special Purpose and Legitimate Interest Vendor",
          special_purposes: [1],
          features: [],
        },
      ],
      gvl: {
        ...mockGvl,
        vendors: {
          ...mockGvl.vendors,
          777: {
            id: 777,
            name: "Vendor with Purposes but no Special Purposes",
            purposes: [1, 2, 3],
            legIntPurposes: [],
            flexiblePurposes: [],
            specialPurposes: [],
            features: [],
            specialFeatures: [],
            policyUrl: "https://test.com/privacy",
            usesCookies: true,
            cookieMaxAgeSeconds: 86400,
            cookieRefresh: false,
            usesNonCookieAccess: false,
          },
          888: {
            id: 888,
            name: "Special Purpose Vendor with Purposes",
            purposes: [1, 2, 3, 4, 7, 10],
            legIntPurposes: [],
            flexiblePurposes: [],
            specialPurposes: [1, 2],
            features: [],
            specialFeatures: [],
            policyUrl: "https://test.com/privacy",
            usesCookies: true,
            cookieMaxAgeSeconds: 86400,
            cookieRefresh: false,
            usesNonCookieAccess: false,
          },
          999: {
            id: 999,
            name: "Special Purpose Only Vendor",
            purposes: [],
            legIntPurposes: [],
            flexiblePurposes: [],
            specialPurposes: [1, 2],
            features: [],
            specialFeatures: [],
            policyUrl: "https://test.com/privacy",
            usesCookies: true,
            cookieMaxAgeSeconds: 86400,
            cookieRefresh: false,
            usesNonCookieAccess: false,
          },
        },
      },
    } as unknown as PrivacyExperience;

    const fidesString = await generateFidesString({
      experience: experienceWithSpecialPurposeVendors,
      tcStringPreferences: {
        customPurposesConsent: [],
        features: [],
        purposesConsent: [], // User opted out of all purposes
        purposesLegint: [],
        specialFeatures: [],
        specialPurposes: [], // Preferences are not saved here
        vendorsConsent: [], // User opted out of all vendors
        vendorsLegint: ["gvl.740"],
      },
    });

    expect(fidesString).not.toBeNull();
    expect(fidesString).not.toBeUndefined();
    expect(fidesString).not.toBe("");

    const [tcfString] = fidesString.split(FIDES_SEPARATOR);
    const decodedTCString = TCString.decode(tcfString);

    // Verify the special purpose only vendors are appropriately added to the legitimate interest section
    expect(decodedTCString.vendorConsents.size).toBe(0);
    expect(decodedTCString.vendorLegitimateInterests.has(740)).toBe(true);
    expect(decodedTCString.vendorLegitimateInterests.has(777)).toBe(false);
    expect(decodedTCString.vendorLegitimateInterests.has(888)).toBe(true);
    expect(decodedTCString.vendorLegitimateInterests.has(999)).toBe(true);
  });
});
