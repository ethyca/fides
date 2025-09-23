/* eslint-disable no-underscore-dangle */

import { CmpApi, Sections } from "@iabgpp/cmpapi";

import {
  FidesCookie,
  PrivacyExperience,
  PrivacyNotice,
  PrivacyNoticeFramework,
  UserConsentPreference,
} from "../../../src/lib/consent-types";
import { GPPUSApproach } from "../../../src/lib/gpp/constants";
import { isGpcSubsectionSupported } from "../../../src/lib/gpp/gpp-utils";
import { makeStub } from "../../../src/lib/gpp/stub";
import {
  GPPFieldMapping,
  GPPMechanismMapping,
  GPPSection,
  GPPSettings,
} from "../../../src/lib/gpp/types";
import {
  setGppNoticesProvidedFromExperience,
  setGppOptOutsFromCookieAndExperience,
} from "../../../src/lib/gpp/us-notices";

const EMPTY_GPP_STRING = "DBAA";

const mockGppMechanism = (override?: Partial<GPPMechanismMapping>) => {
  const base: GPPMechanismMapping = {
    field: "SaleOptOut",
    not_available: "0",
    opt_out: "1",
    not_opt_out: "2",
  };
  if (!override) {
    return base;
  }
  return { ...base, ...override };
};

const mockGppField = (override?: Partial<GPPFieldMapping>) => {
  const base: GPPFieldMapping = {
    region: "us",
    notice: ["SensitiveDataLimitUseNotice"],
    mechanism: [mockGppMechanism()],
  };
  if (!override) {
    return base;
  }
  return { ...base, ...override };
};

const mockPrivacyNotice = (override?: Partial<PrivacyNotice>) => {
  const base: PrivacyNotice = {
    notice_key: "data_sales_and_sharing",
    id: "123",
    created_at: "",
    updated_at: "",
    cookies: [],
    default_preference: UserConsentPreference.OPT_OUT,
    gpp_field_mapping: [mockGppField()],
    translations: [
      {
        language: "en",
        privacy_notice_history_id: "321",
      },
    ],
  };
  if (!override) {
    return base;
  }
  return { ...base, ...override };
};

const mockPrivacyExperience = (override?: Partial<PrivacyExperience>) => {
  const base: PrivacyExperience = {
    id: "id",
    region: "us",
    privacy_notices: [mockPrivacyNotice()],
    created_at: "2023-12-06T22:03:26.052630+00:00",
    updated_at: "2023-12-07T22:03:26.052630+00:00",
    gpp_settings: {
      enabled: true,
      us_approach: GPPUSApproach.NATIONAL,
      mspa_covered_transactions: true,
      mspa_opt_out_option_mode: true,
      mspa_service_provider_mode: false,
      enable_tcfeu_string: true,
    },
  };

  if (!override) {
    return base;
  }
  return { ...base, ...override };
};

const mockFidesCookie = (override?: Partial<FidesCookie>) => {
  const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
  const CREATED_DATE = "2022-12-24T12:00:00.000Z";
  const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
  const cookie: FidesCookie = {
    identity: { fides_user_device_id: uuid },
    fides_meta: {
      version: "0.9.0",
      createdAt: CREATED_DATE,
      updatedAt: UPDATED_DATE,
    },
    consent: {},
    tcf_consent: {},
  };

  if (!override) {
    return cookie;
  }

  return { ...cookie, ...override };
};

describe("setGppNoticesProvidedFromExperience", () => {
  beforeEach(() => {
    // Make stub so that the library initializes without errors
    makeStub();
  });

  it("does nothing for region outside of US", () => {
    const cmpApi = new CmpApi(1, 1);
    const experience = mockPrivacyExperience({ region: "fr" });
    const sectionsChanged = setGppNoticesProvidedFromExperience({
      cmpApi,
      experience,
    });
    expect(sectionsChanged).toEqual([]);
    expect(cmpApi.getGppString()).toEqual(EMPTY_GPP_STRING);
    expect(cmpApi.getSection("usnat")).toBe(null);
  });

  it("sets all as not provided when there are no notices", () => {
    const cmpApi = new CmpApi(1, 1);
    const experience = mockPrivacyExperience({
      privacy_notices: [],
      region: "us",
    });
    const sectionsChanged = setGppNoticesProvidedFromExperience({
      cmpApi,
      experience,
    });
    expect(sectionsChanged).toEqual([{ name: "usnat", id: 7 }]);
    const section = cmpApi.getSection("usnat");
    // We decided to use 0 to mean notice was not provided (https://ethyca.atlassian.net/wiki/spaces/PM/pages/2895937552/GPP+Notice+Requirements)
    // All other consent fields should be 0 (N/A)
    expect(section).toEqual({
      Version: 1,
      SharingNotice: 0,
      SaleOptOutNotice: 0,
      SharingOptOutNotice: 0,
      TargetedAdvertisingOptOutNotice: 0,
      SensitiveDataProcessingOptOutNotice: 0,
      SensitiveDataLimitUseNotice: 0,
      SaleOptOut: 0,
      SharingOptOut: 0,
      TargetedAdvertisingOptOut: 0,
      SensitiveDataProcessing: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      KnownChildSensitiveDataConsents: [0, 0, 0],
      PersonalDataConsents: 0,
      MspaCoveredTransaction: 1,
      MspaOptOutOptionMode: 1,
      MspaServiceProviderMode: 2,
      GpcSegmentType: 1,
      Gpc: false,
    });
    expect(cmpApi.getGppString()).toEqual("DBABLA~BAAAAAAAAABY.QA");
  });

  it("can set some to provided", () => {
    const cmpApi = new CmpApi(1, 1);
    const notices = [
      mockPrivacyNotice({
        notice_key: "data_sales_and_sharing",
        gpp_field_mapping: [
          mockGppField({
            region: "us",
            notice: [
              "SharingNotice",
              "SaleOptOutNotice",
              "SharingOptOutNotice",
            ],
          }),
        ],
      }),
    ];
    const experience = mockPrivacyExperience({ privacy_notices: notices });
    const sectionsChanged = setGppNoticesProvidedFromExperience({
      cmpApi,
      experience,
    });
    expect(sectionsChanged).toEqual([{ name: "usnat", id: 7 }]);
    const section = cmpApi.getSection("usnat");
    expect(section).toEqual({
      Version: 1,
      SharingNotice: 1,
      SaleOptOutNotice: 1,
      SharingOptOutNotice: 1,
      TargetedAdvertisingOptOutNotice: 0,
      SensitiveDataProcessingOptOutNotice: 0,
      SensitiveDataLimitUseNotice: 0,
      SaleOptOut: 0,
      SharingOptOut: 0,
      TargetedAdvertisingOptOut: 0,
      SensitiveDataProcessing: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      KnownChildSensitiveDataConsents: [0, 0, 0],
      PersonalDataConsents: 0,
      MspaCoveredTransaction: 1,
      MspaOptOutOptionMode: 1,
      MspaServiceProviderMode: 2,
      GpcSegmentType: 1,
      Gpc: false,
    });
    expect(cmpApi.getGppString()).toEqual("DBABLA~BVAAAAAAAABY.QA");
  });

  it("can set all to provided", () => {
    const cmpApi = new CmpApi(1, 1);
    const notices = [
      mockPrivacyNotice({
        notice_key: "data_sales_and_sharing",
        gpp_field_mapping: [
          mockGppField({
            region: "us",
            notice: [
              "SharingNotice",
              "SaleOptOutNotice",
              "SharingOptOutNotice",
            ],
          }),
        ],
      }),
      mockPrivacyNotice({
        notice_key: "targeted_advertising",
        gpp_field_mapping: [
          mockGppField({
            region: "us",
            notice: ["TargetedAdvertisingOptOutNotice"],
          }),
        ],
      }),
      mockPrivacyNotice({
        notice_key: "sensitive_personal_data_sharing",
        gpp_field_mapping: [
          mockGppField({
            region: "us",
            notice: [
              "SensitiveDataProcessingOptOutNotice",
              "SensitiveDataLimitUseNotice",
            ],
          }),
        ],
      }),
    ];
    const experience = mockPrivacyExperience({ privacy_notices: notices });
    const sectionsChanged = setGppNoticesProvidedFromExperience({
      cmpApi,
      experience,
    });
    expect(sectionsChanged).toEqual([{ name: "usnat", id: 7 }]);
    const section = cmpApi.getSection("usnat");
    expect(section).toEqual({
      Version: 1,
      SharingNotice: 1,
      SaleOptOutNotice: 1,
      SharingOptOutNotice: 1,
      TargetedAdvertisingOptOutNotice: 1,
      SensitiveDataProcessingOptOutNotice: 1,
      SensitiveDataLimitUseNotice: 1,
      SaleOptOut: 0,
      SharingOptOut: 0,
      TargetedAdvertisingOptOut: 0,
      SensitiveDataProcessing: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      KnownChildSensitiveDataConsents: [0, 0, 0],
      PersonalDataConsents: 0,
      MspaCoveredTransaction: 1,
      MspaOptOutOptionMode: 1,
      MspaServiceProviderMode: 2,
      GpcSegmentType: 1,
      Gpc: false,
    });
    expect(cmpApi.getGppString()).toEqual("DBABLA~BVVAAAAAAABY.QA");
  });
});

describe("setGppOptOutsFromCookieAndExperience", () => {
  const DATA_SALES_SHARING_NOTICE = mockPrivacyNotice({
    notice_key: "data_sales_and_sharing",
    gpp_field_mapping: [
      mockGppField({
        region: "us",
        mechanism: [
          mockGppMechanism(),
          mockGppMechanism({
            field: "SharingOptOut",
          }),
        ],
      }),
    ],
  });
  const TARGETED_ADVERTISING_NOTICE = mockPrivacyNotice({
    notice_key: "targeted_advertising",
    gpp_field_mapping: [
      mockGppField({
        region: "us",
        mechanism: [mockGppMechanism({ field: "TargetedAdvertisingOptOut" })],
      }),
    ],
  });
  const SENSITIVE_PERSONAL_SHARING_NOTICE = mockPrivacyNotice({
    notice_key: "sensitive_personal_data_sharing",
    gpp_field_mapping: [
      mockGppField({
        region: "us",
        mechanism: [
          mockGppMechanism({
            field: "SensitiveDataProcessing",
            not_available: "0000000000000000",
            opt_out: "1111111111111111",
            not_opt_out: "2222222222222222",
          }),
        ],
      }),
    ],
  });
  const KNOWN_CHILD_SENSITIVE_NOTICE = mockPrivacyNotice({
    notice_key: "known_child_sensitive_data_consents",
    gpp_field_mapping: [
      mockGppField({
        region: "us",
        mechanism: [
          mockGppMechanism({
            field: "KnownChildSensitiveDataConsents",
            not_available: "000",
            opt_out: "111",
            not_opt_out: "222",
          }),
        ],
      }),
    ],
  });
  const PERSONAL_DATA_NOTICE = mockPrivacyNotice({
    notice_key: "personal_data_consents",
    gpp_field_mapping: [
      mockGppField({
        region: "us",
        mechanism: [mockGppMechanism({ field: "PersonalDataConsents" })],
      }),
    ],
  });
  const US_UT_NOTICE = mockPrivacyNotice({
    notice_key: "us_ut",
    framework: PrivacyNoticeFramework.GPP_US_STATE,
    gpp_field_mapping: [
      mockGppField({ region: "us_ut", mechanism: [mockGppMechanism()] }),
    ],
  });
  beforeEach(() => {
    // Make stub so that the library initializes without errors
    makeStub();
  });

  it("does nothing for region outside of US", () => {
    const cmpApi = new CmpApi(1, 1);
    const cookie = mockFidesCookie();
    const experience = mockPrivacyExperience({ region: "fr" });
    const sectionsChanged = setGppOptOutsFromCookieAndExperience({
      cmpApi,
      cookie,
      experience,
    });
    expect(sectionsChanged).toEqual([]);
    expect(cmpApi.getGppString()).toEqual(EMPTY_GPP_STRING);
    expect(cmpApi.getSection("usnat")).toBe(null);
  });

  it("sets all as 0 when there is no consent object in cookie", () => {
    const cmpApi = new CmpApi(1, 1);
    const cookie = mockFidesCookie({ consent: {} });
    const notices = [DATA_SALES_SHARING_NOTICE];
    const experience = mockPrivacyExperience({
      region: "us",
      privacy_notices: notices,
    });
    const sectionsChanged = setGppOptOutsFromCookieAndExperience({
      cmpApi,
      cookie,
      experience,
    });
    expect(sectionsChanged).toEqual([{ name: "usnat", id: 7 }]);
    const section = cmpApi.getSection("usnat");
    expect(section).toEqual({
      Version: 1,
      SharingNotice: 0,
      SaleOptOutNotice: 0,
      SharingOptOutNotice: 0,
      TargetedAdvertisingOptOutNotice: 0,
      SensitiveDataProcessingOptOutNotice: 0,
      SensitiveDataLimitUseNotice: 0,
      SaleOptOut: 0,
      SharingOptOut: 0,
      TargetedAdvertisingOptOut: 0,
      SensitiveDataProcessing: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      KnownChildSensitiveDataConsents: [0, 0, 0],
      PersonalDataConsents: 0,
      MspaCoveredTransaction: 1,
      MspaOptOutOptionMode: 1,
      MspaServiceProviderMode: 2,
      GpcSegmentType: 1,
      Gpc: false,
    });
    expect(cmpApi.getGppString()).toEqual("DBABLA~BAAAAAAAAABY.QA");
  });

  it("can set fields when there is a partial consent object in cookie", () => {
    const cmpApi = new CmpApi(1, 1);
    const cookie = mockFidesCookie({
      consent: { data_sales_and_sharing: true },
    });
    const notices = [DATA_SALES_SHARING_NOTICE];
    const experience = mockPrivacyExperience({
      region: "us",
      privacy_notices: notices,
    });
    setGppOptOutsFromCookieAndExperience({
      cmpApi,
      cookie,
      experience,
    });
    const section = cmpApi.getSection("usnat");
    expect(section).toEqual({
      Version: 1,
      SharingNotice: 0,
      SaleOptOutNotice: 0,
      SharingOptOutNotice: 0,
      TargetedAdvertisingOptOutNotice: 0,
      SensitiveDataProcessingOptOutNotice: 0,
      SensitiveDataLimitUseNotice: 0,
      SaleOptOut: 2,
      SharingOptOut: 2,
      TargetedAdvertisingOptOut: 0,
      SensitiveDataProcessing: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      KnownChildSensitiveDataConsents: [0, 0, 0],
      PersonalDataConsents: 0,
      MspaCoveredTransaction: 1,
      MspaOptOutOptionMode: 1,
      MspaServiceProviderMode: 2,
      GpcSegmentType: 1,
      Gpc: false,
    });
    expect(cmpApi.getGppString()).toEqual("DBABLA~BAAoAAAAAABY.QA");
  });

  it("can set all fields to not opted out for consent object in cookie", () => {
    const cmpApi = new CmpApi(1, 1);
    const cookie = mockFidesCookie({
      consent: {
        data_sales_and_sharing: true,
        targeted_advertising: true,
        sensitive_personal_data_sharing: true,
        known_child_sensitive_data_consents: true,
        personal_data_consents: true,
      },
    });
    const notices = [
      DATA_SALES_SHARING_NOTICE,
      TARGETED_ADVERTISING_NOTICE,
      SENSITIVE_PERSONAL_SHARING_NOTICE,
      KNOWN_CHILD_SENSITIVE_NOTICE,
      PERSONAL_DATA_NOTICE,
    ];
    const experience = mockPrivacyExperience({
      region: "us",
      privacy_notices: notices,
    });
    setGppOptOutsFromCookieAndExperience({
      cmpApi,
      cookie,
      experience,
    });
    const section = cmpApi.getSection("usnat");
    expect(section).toEqual({
      Version: 1,
      SharingNotice: 0,
      SaleOptOutNotice: 0,
      SharingOptOutNotice: 0,
      TargetedAdvertisingOptOutNotice: 0,
      SensitiveDataProcessingOptOutNotice: 0,
      SensitiveDataLimitUseNotice: 0,
      SaleOptOut: 2,
      SharingOptOut: 2,
      TargetedAdvertisingOptOut: 2,
      SensitiveDataProcessing: [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
      KnownChildSensitiveDataConsents: [2, 2, 2],
      PersonalDataConsents: 2,
      MspaCoveredTransaction: 1,
      MspaOptOutOptionMode: 1,
      MspaServiceProviderMode: 2,
      GpcSegmentType: 1,
      Gpc: false,
    });
    expect(cmpApi.getGppString()).toEqual("DBABLA~BAAqqqqqqqpY.QA");
  });

  it("can set all fields to opted out for consent object in cookie", () => {
    const cmpApi = new CmpApi(1, 1);
    const cookie = mockFidesCookie({
      consent: {
        data_sales_and_sharing: false,
        targeted_advertising: false,
        sensitive_personal_data_sharing: false,
        known_child_sensitive_data_consents: false,
        personal_data_consents: false,
      },
    });
    const notices = [
      DATA_SALES_SHARING_NOTICE,
      TARGETED_ADVERTISING_NOTICE,
      SENSITIVE_PERSONAL_SHARING_NOTICE,
      KNOWN_CHILD_SENSITIVE_NOTICE,
      PERSONAL_DATA_NOTICE,
    ];
    const experience = mockPrivacyExperience({
      region: "us",
      privacy_notices: notices,
    });
    setGppOptOutsFromCookieAndExperience({
      cmpApi,
      cookie,
      experience,
    });
    const section = cmpApi.getSection("usnat");
    expect(section).toEqual({
      Version: 1,
      SharingNotice: 0,
      SaleOptOutNotice: 0,
      SharingOptOutNotice: 0,
      TargetedAdvertisingOptOutNotice: 0,
      SensitiveDataProcessingOptOutNotice: 0,
      SensitiveDataLimitUseNotice: 0,
      SaleOptOut: 1,
      SharingOptOut: 1,
      TargetedAdvertisingOptOut: 1,
      SensitiveDataProcessing: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
      KnownChildSensitiveDataConsents: [1, 1, 1],
      PersonalDataConsents: 1,
      MspaCoveredTransaction: 1,
      MspaOptOutOptionMode: 1,
      MspaServiceProviderMode: 2,
      GpcSegmentType: 1,
      Gpc: false,
    });
    expect(cmpApi.getGppString()).toEqual("DBABLA~BAAVVVVVVVVY.QA");
  });

  it("sets MSPA fields to disabled when mspa_covered_transactions is false", () => {
    const cmpApi = new CmpApi(1, 1);
    const cookie = mockFidesCookie();
    const experience = mockPrivacyExperience({
      region: "us",
      gpp_settings: {
        enabled: true,
        us_approach: GPPUSApproach.NATIONAL,
        mspa_covered_transactions: false,
        mspa_opt_out_option_mode: true,
        mspa_service_provider_mode: true,
        enable_tcfeu_string: true,
      },
    });
    setGppOptOutsFromCookieAndExperience({
      cmpApi,
      cookie,
      experience,
    });
    const section = cmpApi.getSection("usnat");
    expect(section).toMatchObject({
      MspaCoveredTransaction: 2,
      MspaOptOutOptionMode: 0,
      MspaServiceProviderMode: 0,
    });
  });

  it("can use US gpp fields when gpp is set to national", () => {
    const cmpApi = new CmpApi(1, 1);
    const cookie = mockFidesCookie({
      consent: {
        data_sales_and_sharing: false,
        targeted_advertising: false,
        sensitive_personal_data_sharing: false,
        known_child_sensitive_data_consents: false,
        personal_data_consents: false,
      },
    });
    const notices = [
      DATA_SALES_SHARING_NOTICE,
      TARGETED_ADVERTISING_NOTICE,
      SENSITIVE_PERSONAL_SHARING_NOTICE,
      KNOWN_CHILD_SENSITIVE_NOTICE,
      PERSONAL_DATA_NOTICE,
    ];
    const experience = mockPrivacyExperience({
      region: "us_ca", // Set to a state
      privacy_notices: notices,
    });
    setGppOptOutsFromCookieAndExperience({
      cmpApi,
      cookie,
      experience,
    });
    const section = cmpApi.getSection("usnat");
    expect(section).toEqual({
      Version: 1,
      SharingNotice: 0,
      SaleOptOutNotice: 0,
      SharingOptOutNotice: 0,
      TargetedAdvertisingOptOutNotice: 0,
      SensitiveDataProcessingOptOutNotice: 0,
      SensitiveDataLimitUseNotice: 0,
      SaleOptOut: 1,
      SharingOptOut: 1,
      TargetedAdvertisingOptOut: 1,
      SensitiveDataProcessing: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
      KnownChildSensitiveDataConsents: [1, 1, 1],
      PersonalDataConsents: 1,
      MspaCoveredTransaction: 1,
      MspaOptOutOptionMode: 1,
      MspaServiceProviderMode: 2,
      GpcSegmentType: 1,
      Gpc: false,
    });
    expect(cmpApi.getGppString()).toEqual("DBABLA~BAAVVVVVVVVY.QA");
  });

  it("can use state gpp fields when gpp is set to state", () => {
    const cmpApi = new CmpApi(1, 1);
    const cookie = mockFidesCookie({
      consent: {
        data_sales_and_sharing: false,
        targeted_advertising: false,
        sensitive_personal_data_sharing: false,
        known_child_sensitive_data_consents: false,
        personal_data_consents: false,
      },
    });
    const notices = [
      DATA_SALES_SHARING_NOTICE,
      TARGETED_ADVERTISING_NOTICE,
      SENSITIVE_PERSONAL_SHARING_NOTICE,
      KNOWN_CHILD_SENSITIVE_NOTICE,
      PERSONAL_DATA_NOTICE,
    ];
    const experience = mockPrivacyExperience({
      region: "us_ut", // Set to a state
      privacy_notices: notices,
      gpp_settings: {
        enabled: true,
        us_approach: GPPUSApproach.STATE, // Set to state
        mspa_covered_transactions: true,
        mspa_opt_out_option_mode: true,
        mspa_service_provider_mode: false,
        enable_tcfeu_string: true,
      },
    });
    setGppOptOutsFromCookieAndExperience({
      cmpApi,
      cookie,
      experience,
    });
    const section = cmpApi.getSection("usut");
    expect(section).toEqual({
      Version: 1,
      SharingNotice: 0,
      SaleOptOutNotice: 0,
      TargetedAdvertisingOptOutNotice: 0,
      SensitiveDataProcessingOptOutNotice: 0,
      SaleOptOut: 0,
      TargetedAdvertisingOptOut: 0,
      SensitiveDataProcessing: [0, 0, 0, 0, 0, 0, 0, 0],
      KnownChildSensitiveDataConsents: 0,
      MspaCoveredTransaction: 1,
      MspaOptOutOptionMode: 1,
      MspaServiceProviderMode: 2,
    });
    expect(cmpApi.getGppString()).toEqual("DBABFg~BAAAAAWA");
  });

  it("does nothing for non-supported region when gpp is set to state", () => {
    const cmpApi = new CmpApi(1, 1);
    const experience = mockPrivacyExperience({
      region: "us_ny",
      gpp_settings: {
        enabled: true,
        us_approach: GPPUSApproach.STATE, // Set to state
        mspa_covered_transactions: true,
        mspa_opt_out_option_mode: true,
        mspa_service_provider_mode: false,
        enable_tcfeu_string: true,
      },
    });
    const sectionsChanged = setGppNoticesProvidedFromExperience({
      cmpApi,
      experience,
    });
    expect(sectionsChanged).toEqual([]);
    expect(cmpApi.getGppString()).toEqual(EMPTY_GPP_STRING);
    expect(cmpApi.getSection("usnat")).toBe(null);
    expect(cmpApi.getSection("usny")).toBe(null);
  });

  it("can use US gpp fields when gpp is set to all", () => {
    const cmpApi = new CmpApi(1, 1);
    const cookie = mockFidesCookie({
      consent: {
        data_sales_and_sharing: false,
        targeted_advertising: false,
        sensitive_personal_data_sharing: false,
        known_child_sensitive_data_consents: false,
        personal_data_consents: false,
      },
    });
    const notices = [
      DATA_SALES_SHARING_NOTICE,
      TARGETED_ADVERTISING_NOTICE,
      SENSITIVE_PERSONAL_SHARING_NOTICE,
      KNOWN_CHILD_SENSITIVE_NOTICE,
      PERSONAL_DATA_NOTICE,
    ];
    const experience = mockPrivacyExperience({
      region: "us_id", // Set to a non-supported state
      privacy_notices: notices,
      gpp_settings: {
        enabled: true,
        us_approach: GPPUSApproach.ALL, // Set to all
        mspa_covered_transactions: true,
        mspa_opt_out_option_mode: true,
        mspa_service_provider_mode: false,
        enable_tcfeu_string: true,
      },
    });
    setGppOptOutsFromCookieAndExperience({
      cmpApi,
      cookie,
      experience,
    });
    const section = cmpApi.getSection("usnat");
    expect(section).toEqual({
      Version: 1,
      SharingNotice: 0,
      SaleOptOutNotice: 0,
      SharingOptOutNotice: 0,
      TargetedAdvertisingOptOutNotice: 0,
      SensitiveDataProcessingOptOutNotice: 0,
      SensitiveDataLimitUseNotice: 0,
      SaleOptOut: 1,
      SharingOptOut: 1,
      TargetedAdvertisingOptOut: 1,
      SensitiveDataProcessing: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
      KnownChildSensitiveDataConsents: [1, 1, 1],
      PersonalDataConsents: 1,
      MspaCoveredTransaction: 1,
      MspaOptOutOptionMode: 1,
      MspaServiceProviderMode: 2,
      GpcSegmentType: 1,
      Gpc: false,
    });
    expect(cmpApi.getGppString()).toEqual("DBABLA~BAAVVVVVVVVY.QA");
  });

  it("can use state gpp fields when gpp is set to all", () => {
    const cmpApi = new CmpApi(1, 1);
    const cookie = mockFidesCookie({
      consent: {
        data_sales_and_sharing: false,
        targeted_advertising: false,
        sensitive_personal_data_sharing: false,
        known_child_sensitive_data_consents: false,
        personal_data_consents: false,
      },
    });
    const notices = [
      DATA_SALES_SHARING_NOTICE,
      TARGETED_ADVERTISING_NOTICE,
      SENSITIVE_PERSONAL_SHARING_NOTICE,
      KNOWN_CHILD_SENSITIVE_NOTICE,
      PERSONAL_DATA_NOTICE,
      US_UT_NOTICE,
    ];
    const experience = mockPrivacyExperience({
      region: "us_ut", // Set to a supported state
      privacy_notices: notices,
      gpp_settings: {
        enabled: true,
        us_approach: GPPUSApproach.ALL, // Set to all
        mspa_covered_transactions: true,
        mspa_opt_out_option_mode: true,
        mspa_service_provider_mode: false,
        enable_tcfeu_string: true,
      },
    });
    setGppOptOutsFromCookieAndExperience({
      cmpApi,
      cookie,
      experience,
    });
    const section = cmpApi.getSection("usut");
    expect(section).toEqual({
      Version: 1,
      SharingNotice: 0,
      SaleOptOutNotice: 0,
      TargetedAdvertisingOptOutNotice: 0,
      SensitiveDataProcessingOptOutNotice: 0,
      SaleOptOut: 0,
      TargetedAdvertisingOptOut: 0,
      SensitiveDataProcessing: [0, 0, 0, 0, 0, 0, 0, 0],
      KnownChildSensitiveDataConsents: 0,
      MspaCoveredTransaction: 1,
      MspaOptOutOptionMode: 1,
      MspaServiceProviderMode: 2,
    });
    expect(cmpApi.getGppString()).toEqual("DBABFg~BAAAAAWA");
  });

  it("can use US gpp fields when gpp is set to all and supported state has no notices", () => {
    const cmpApi = new CmpApi(1, 1);
    const cookie = mockFidesCookie({
      consent: {
        data_sales_and_sharing: false,
        targeted_advertising: false,
        sensitive_personal_data_sharing: false,
        known_child_sensitive_data_consents: false,
        personal_data_consents: false,
      },
    });
    const notices = [
      DATA_SALES_SHARING_NOTICE,
      TARGETED_ADVERTISING_NOTICE,
      SENSITIVE_PERSONAL_SHARING_NOTICE,
      KNOWN_CHILD_SENSITIVE_NOTICE,
      PERSONAL_DATA_NOTICE,
      US_UT_NOTICE,
    ];
    const experience = mockPrivacyExperience({
      region: "us_tx", // Set to a supported state but no notices are provided for that state
      privacy_notices: notices,
      gpp_settings: {
        enabled: true,
        us_approach: GPPUSApproach.ALL, // Set to all
        mspa_covered_transactions: true,
        mspa_opt_out_option_mode: true,
        mspa_service_provider_mode: false,
        enable_tcfeu_string: true,
      },
    });
    setGppOptOutsFromCookieAndExperience({
      cmpApi,
      cookie,
      experience,
    });
    const section = cmpApi.getSection("usnat");
    expect(section).toEqual({
      Version: 1,
      SharingNotice: 0,
      SaleOptOutNotice: 0,
      SharingOptOutNotice: 0,
      TargetedAdvertisingOptOutNotice: 0,
      SensitiveDataProcessingOptOutNotice: 0,
      SensitiveDataLimitUseNotice: 0,
      SaleOptOut: 1,
      SharingOptOut: 1,
      TargetedAdvertisingOptOut: 1,
      SensitiveDataProcessing: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
      KnownChildSensitiveDataConsents: [1, 1, 1],
      PersonalDataConsents: 1,
      MspaCoveredTransaction: 1,
      MspaOptOutOptionMode: 1,
      MspaServiceProviderMode: 2,
      GpcSegmentType: 1,
      Gpc: false,
    });
    expect(cmpApi.getGppString()).toEqual("DBABLA~BAAVVVVVVVVY.QA");
  });

  describe("encoding the GPC sub-section", () => {
    let cmpApi: CmpApi;
    let cookie: FidesCookie;
    let notices: PrivacyNotice[];
    let usnatExperience: PrivacyExperience;
    let uscaExperience: PrivacyExperience;
    let usutExperience: PrivacyExperience;
    const US_CA_NOTICE = mockPrivacyNotice({
      notice_key: "us_ca",
      framework: PrivacyNoticeFramework.GPP_US_STATE,
      gpp_field_mapping: [
        mockGppField({ region: "us_ca", mechanism: [mockGppMechanism()] }),
      ],
    });

    beforeEach(() => {
      // Configure a test setup with both National and State-by-state notices configured
      cmpApi = new CmpApi(1, 1);
      cookie = mockFidesCookie({ consent: {} });
      notices = [
        DATA_SALES_SHARING_NOTICE,
        TARGETED_ADVERTISING_NOTICE,
        SENSITIVE_PERSONAL_SHARING_NOTICE,
        KNOWN_CHILD_SENSITIVE_NOTICE,
        PERSONAL_DATA_NOTICE,
        US_UT_NOTICE,
        US_CA_NOTICE,
      ];
      const gppSettings: GPPSettings = {
        enabled: true,
        us_approach: GPPUSApproach.ALL,
        mspa_covered_transactions: true,
        mspa_opt_out_option_mode: true,
        mspa_service_provider_mode: false,
        enable_tcfeu_string: true,
      };
      usnatExperience = mockPrivacyExperience({
        region: "us",
        privacy_notices: notices,
        gpp_settings: gppSettings,
      });
      uscaExperience = mockPrivacyExperience({
        region: "us_ca",
        privacy_notices: notices,
        gpp_settings: gppSettings,
      });
      usutExperience = mockPrivacyExperience({
        region: "us_ut",
        privacy_notices: notices,
        gpp_settings: gppSettings,
      });
    });

    afterEach(() => {
      // Reset any modification of the navigator for globalPrivacyControl
      Object.defineProperty(window.navigator, "globalPrivacyControl", {
        value: undefined,
        writable: true,
        configurable: true,
      });
    });

    describe("when the browser GPC setting is true", () => {
      beforeEach(() => {
        Object.defineProperty(window.navigator, "globalPrivacyControl", {
          value: true,
          writable: true,
          configurable: true,
        });
      });

      it("sets Gpc=true in the usnat section", () => {
        const sectionsChanged = setGppOptOutsFromCookieAndExperience({
          cmpApi,
          cookie,
          experience: usnatExperience,
        });
        expect(sectionsChanged).toEqual([{ name: "usnat", id: 7 }]);
        const section = cmpApi.getSection("usnat");
        expect(section).toHaveProperty("GpcSegmentType", 1);
        expect(section).toHaveProperty("Gpc", true);
        expect(cmpApi.getGppString()).toEqual("DBABLA~BAAAAAAAAABY.YA");
      });

      it("sets Gpc=true in the usca section", () => {
        const sectionsChanged = setGppOptOutsFromCookieAndExperience({
          cmpApi,
          cookie,
          experience: uscaExperience,
        });
        expect(sectionsChanged).toEqual([{ name: "usca", id: 8 }]);
        const section = cmpApi.getSection("usca");
        expect(section).toHaveProperty("GpcSegmentType", 1);
        expect(section).toHaveProperty("Gpc", true);
        expect(cmpApi.getGppString()).toEqual("DBABBg~BAAAAABY.YA");
      });

      it("does not include Gpc in the usut section where GPC is not supported", () => {
        const sectionsChanged = setGppOptOutsFromCookieAndExperience({
          cmpApi,
          cookie,
          experience: usutExperience,
        });
        expect(sectionsChanged).toEqual([{ name: "usut", id: 11 }]);
        const section = cmpApi.getSection("usut");
        expect(section).not.toHaveProperty("GpcSegmentType");
        expect(section).not.toHaveProperty("Gpc");
        expect(cmpApi.getGppString()).toEqual("DBABFg~BAAAAAWA");
      });
    });

    describe("when the browser GPC setting is false", () => {
      beforeEach(() => {
        Object.defineProperty(window.navigator, "globalPrivacyControl", {
          value: false,
          writable: true,
          configurable: true,
        });
      });

      it("sets Gpc=false in the usnat section", () => {
        const sectionsChanged = setGppOptOutsFromCookieAndExperience({
          cmpApi,
          cookie,
          experience: usnatExperience,
        });
        expect(sectionsChanged).toEqual([{ name: "usnat", id: 7 }]);
        const section = cmpApi.getSection("usnat");
        expect(section).toHaveProperty("GpcSegmentType", 1);
        expect(section).toHaveProperty("Gpc", false);
        expect(cmpApi.getGppString()).toEqual("DBABLA~BAAAAAAAAABY.QA");
      });

      it("sets Gpc=false in the usca section", () => {
        const sectionsChanged = setGppOptOutsFromCookieAndExperience({
          cmpApi,
          cookie,
          experience: uscaExperience,
        });
        expect(sectionsChanged).toEqual([{ name: "usca", id: 8 }]);
        const section = cmpApi.getSection("usca");
        expect(section).toHaveProperty("GpcSegmentType", 1);
        expect(section).toHaveProperty("Gpc", false);
        expect(cmpApi.getGppString()).toEqual("DBABBg~BAAAAABY.QA");
      });

      it("does not include Gpc in the usut section where GPC is not supported", () => {
        const sectionsChanged = setGppOptOutsFromCookieAndExperience({
          cmpApi,
          cookie,
          experience: usutExperience,
        });
        expect(sectionsChanged).toEqual([{ name: "usut", id: 11 }]);
        const section = cmpApi.getSection("usut");
        expect(section).not.toHaveProperty("GpcSegmentType");
        expect(section).not.toHaveProperty("Gpc");
        expect(cmpApi.getGppString()).toEqual("DBABFg~BAAAAAWA");
      });
    });
  });
});

describe("isGpcSubsectionSupported", () => {
  const SECTIONS_WITH_GPC_SUBSECTION = [
    "usnat",
    "usca",
    "usco",
    "usct",
    "usde",
    "usia",
    "usmn",
    "usmt",
    "usne",
    "usnh",
    "usnj",
    "usor",
    "ustn",
    "ustx",
  ];
  const ALL_SECTIONS: GPPSection[] = Array.from(
    Array.from(Sections.SECTION_ID_NAME_MAP.entries()).map(([id, name]) => ({
      id,
      name,
    })),
  );

  it("should return true for all sections that support GPC", () => {
    ALL_SECTIONS.forEach((section) => {
      const expectationValue = SECTIONS_WITH_GPC_SUBSECTION.includes(
        section.name,
      );
      const actualValue = isGpcSubsectionSupported(section);

      // For readability, we want to show the section name in the error message
      const expectation = `${section}: ${expectationValue}`;
      const actual = `${section}: ${actualValue}`;
      expect(actual).toBe(expectation);
    });
  });

  it("should return false for any unexpected input types", () => {
    expect(isGpcSubsectionSupported(null as any)).toBe(false);
    expect(isGpcSubsectionSupported(undefined as any)).toBe(false);
    expect(isGpcSubsectionSupported("" as any)).toBe(false);
    expect(isGpcSubsectionSupported({} as any)).toBe(false);
    expect(isGpcSubsectionSupported({ id: 99 } as any)).toBe(false);
    expect(isGpcSubsectionSupported({ name: "usnat" } as any)).toBe(true);
    expect(isGpcSubsectionSupported({ name: "usca" } as any)).toBe(true);
    expect(isGpcSubsectionSupported({ name: "usco" } as any)).toBe(true);
    expect(isGpcSubsectionSupported({ name: "usct" } as any)).toBe(true);
  });
});
