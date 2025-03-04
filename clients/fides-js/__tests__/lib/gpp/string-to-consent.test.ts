import { CmpApi } from "@iabgpp/cmpapi";

import { fidesStringToConsent } from "~/lib/gpp/string-to-consent";

import {
  ComponentType,
  ConsentMechanism,
  ConsentMethod,
  ExperienceConfig,
  FidesCookie,
  FidesInitOptions,
  PrivacyExperience,
  PrivacyNotice,
  PrivacyNoticeFramework,
  UserConsentPreference,
} from "../../../src/lib/consent-types";
import { makeStub } from "../../../src/lib/gpp/stub";
import {
  GPPFieldMapping,
  GPPMechanismMapping,
  GPPUSApproach,
} from "../../../src/lib/gpp/types";
import {
  UpdateConsentPreferences,
  updateConsentPreferences,
} from "../../../src/lib/preferences";

// Mock fidesDebugger
(globalThis as any).fidesDebugger = jest.fn();

jest.mock("~/lib/preferences", () => ({
  updateConsentPreferences: jest.fn(),
}));

const mockGppMechanism = (override?: Partial<GPPMechanismMapping[]>) => {
  const base: GPPMechanismMapping[] = [
    {
      field: "SaleOptOut",
      not_available: "0",
      opt_out: "1",
      not_opt_out: "2",
    },
    {
      field: "SharingOptOut",
      not_available: "0",
      opt_out: "1",
      not_opt_out: "2",
    },
  ];
  if (!override) {
    return base;
  }
  return [...base, ...override];
};

const mockUSNatGppField = (override?: Partial<GPPFieldMapping>) => {
  const base: GPPFieldMapping = {
    region: "us",
    notice: ["SaleOptOutNotice", "SharingOptOutNotice", "SharingNotice"],
    mechanism: mockGppMechanism() as GPPMechanismMapping[],
  };
  if (!override) {
    return base;
  }
  return { ...base, ...override };
};

const mockUSStateGppField = (override?: Partial<GPPFieldMapping>) => {
  const base: GPPFieldMapping = {
    region: "us_ca",
    notice: ["SaleOptOutNotice", "SharingOptOutNotice"],
    mechanism: mockGppMechanism() as GPPMechanismMapping[],
  };
  if (!override) {
    return base;
  }
  return { ...base, ...override };
};

const mockUSNatPrivacyNotices = (override?: Partial<PrivacyNotice>[]) => {
  const base: Partial<PrivacyNotice>[] = [
    {
      notice_key: "data_sales_and_sharing",
      id: "456",
      gpp_field_mapping: undefined,
      translations: [
        {
          language: "en",
          privacy_notice_history_id: "456",
        },
      ],
    },
    {
      notice_key: "sales_sharing_targeted_advertising_gpp_us_national",
      id: "123",
      gpp_field_mapping: [mockUSNatGppField()],
      translations: [
        {
          language: "en",
          privacy_notice_history_id: "321",
        },
      ],
    },
  ];
  if (!override) {
    return base;
  }
  return [...base, ...override];
};

const mockUSStatePrivacyNotices = (override?: Partial<PrivacyNotice>[]) => {
  const base: Partial<PrivacyNotice>[] = [
    {
      notice_key: "targeted_advertising_gpp_us_state",
      id: "1234",
      gpp_field_mapping: [mockUSStateGppField()],
      consent_mechanism: ConsentMechanism.OPT_OUT,
      default_preference: UserConsentPreference.OPT_IN,
      framework: PrivacyNoticeFramework.GPP_US_STATE,
      translations: [
        {
          language: "en",
          privacy_notice_history_id: "4567",
        },
      ],
    },
  ];
  if (!override) {
    return base;
  }
  return [...base, ...override];
};

const mockExperienceConfig = (override?: Partial<ExperienceConfig>) => {
  const base: Partial<ExperienceConfig> = {
    component: ComponentType.MODAL,
    translations: [
      { language: "en", privacy_experience_config_history_id: "321" },
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
    privacy_notices: mockUSNatPrivacyNotices() as PrivacyNotice[],
    created_at: "2023-12-06T22:03:26.052630+00:00",
    updated_at: "2023-12-07T22:03:26.052630+00:00",
    gpp_settings: {
      enabled: true,
      us_approach: GPPUSApproach.NATIONAL,
      mspa_covered_transactions: true,
      mspa_opt_out_option_mode: true,
      mspa_service_provider_mode: false,
      enable_tcfeu_string: false,
    },
    experience_config: mockExperienceConfig() as ExperienceConfig,
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

const mockWindowFides = (override?: Partial<Window["Fides"]>) => {
  (window as any).Fides = {
    options: {
      tcfEnabled: false,
      gppEnabled: true,
    },
    cookie: mockFidesCookie(),
    geolocation: {
      location: "us-ca",
      country: "us",
      region: "ca",
    },
    locale: "en",
    experience: mockPrivacyExperience(),
    ...override,
  };
};

const expectUpdateConsentPreferences = (
  override?: Partial<UpdateConsentPreferences>,
) => {
  const base: Partial<UpdateConsentPreferences> = {
    consentMethod: ConsentMethod.SCRIPT,
    options: {
      tcfEnabled: false,
      gppEnabled: true,
    } as FidesInitOptions,
    cookie: mockFidesCookie(),
    experience: mockPrivacyExperience(),
    privacyExperienceConfigHistoryId: "321",
    userLocationString: "us_ca",
    consentPreferencesToSave: [],
  };
  if (!override) {
    return base;
  }
  return { ...base, ...override };
};

describe("fidesStringToConsent", () => {
  beforeEach(() => {
    makeStub();
    jest.clearAllMocks();
  });

  it("should return undefined if no experience", () => {
    const cmpApi = new CmpApi(1, 1);
    mockWindowFides({ experience: undefined });
    fidesStringToConsent({ fidesString: ",,DBABLA~BVAAAAAAAABY.QA", cmpApi });

    // Verify updateConsentPreferences was not called
    expect(updateConsentPreferences).not.toHaveBeenCalled();
  });

  it("should return undefined if no experience config", () => {
    const cmpApi = new CmpApi(1, 1);
    mockWindowFides({
      experience: {
        ...mockPrivacyExperience(),
        experience_config: undefined,
      },
    });
    fidesStringToConsent({ fidesString: ",,DBABLA~BVAAAAAAAABY.QA", cmpApi });
    expect(updateConsentPreferences).not.toHaveBeenCalled();
  });

  it("should return undefined if no privacy notices", () => {
    const cmpApi = new CmpApi(1, 1);
    mockWindowFides({
      experience: {
        ...mockPrivacyExperience(),
        privacy_notices: undefined,
      },
    });
    fidesStringToConsent({ fidesString: ",,DBABLA~BVAAAAAAAABY.QA", cmpApi });
    expect(updateConsentPreferences).not.toHaveBeenCalled();
  });

  it("should return undefined if no translation", () => {
    const cmpApi = new CmpApi(1, 1);
    mockWindowFides({
      experience: {
        ...mockPrivacyExperience(),
        experience_config: {
          ...mockPrivacyExperience().experience_config,
          translations: [],
        } as ExperienceConfig,
      },
    });
    fidesStringToConsent({ fidesString: ",,DBABLA~BVAAAAAAAABY.QA", cmpApi });
    expect(updateConsentPreferences).not.toHaveBeenCalled();
  });

  it("should return undefined if no gpp string", () => {
    const cmpApi = new CmpApi(1, 1);
    mockWindowFides();
    fidesStringToConsent({ fidesString: "", cmpApi });
    expect(updateConsentPreferences).not.toHaveBeenCalled();
  });

  it("should map usnat gpp string to consent preferences when opt out of all", () => {
    mockWindowFides();
    const cmpApi = new CmpApi(1, 1);
    fidesStringToConsent({ fidesString: ",,DBABLA~BVAUAAAAAABo.QA", cmpApi });
    expect(updateConsentPreferences).toHaveBeenCalledWith(
      expect.objectContaining(
        expectUpdateConsentPreferences({
          consentPreferencesToSave: [
            {
              consentPreference: UserConsentPreference.OPT_OUT,
              notice: mockUSNatPrivacyNotices()[0] as PrivacyNotice,
              noticeHistoryId: "456",
            },
            {
              consentPreference: UserConsentPreference.OPT_OUT,
              notice: mockUSNatPrivacyNotices()[1] as PrivacyNotice,
              noticeHistoryId: "321",
            },
          ],
        }),
      ),
    );
  });

  it("should map usnat gpp string to consent preferences when opt in to all", () => {
    mockWindowFides();
    const cmpApi = new CmpApi(1, 1);
    fidesStringToConsent({ fidesString: ",,DBABLA~BVAoAAAAAABo.QA", cmpApi });
    expect(updateConsentPreferences).toHaveBeenCalledWith(
      expect.objectContaining(
        expectUpdateConsentPreferences({
          consentPreferencesToSave: [
            {
              // correctly opt out (default) because this notice has no GPP field mapping
              consentPreference: UserConsentPreference.OPT_OUT,
              notice: mockUSNatPrivacyNotices()[0] as PrivacyNotice,
              noticeHistoryId: "456",
            },
            {
              consentPreference: UserConsentPreference.OPT_IN,
              notice: mockUSNatPrivacyNotices()[1] as PrivacyNotice,
              noticeHistoryId: "321",
            },
          ],
        }),
      ),
    );
  });
  it("should map us state gpp string to consent preferences when opt out of all", () => {
    mockWindowFides({
      experience: {
        ...mockPrivacyExperience({
          region: "us_ca",
          gpp_settings: {
            ...mockPrivacyExperience().gpp_settings,
            us_approach: GPPUSApproach.STATE,
          },
        }),
        privacy_notices: mockUSStatePrivacyNotices() as PrivacyNotice[],
      },
    });
    const cmpApi = new CmpApi(1, 1);
    fidesStringToConsent({ fidesString: ",,DBABBg~BUUAAABY.QA", cmpApi });
    expect(updateConsentPreferences).toHaveBeenCalledWith(
      expect.objectContaining(
        expectUpdateConsentPreferences({
          experience: {
            ...mockPrivacyExperience({
              region: "us_ca",
              gpp_settings: {
                ...mockPrivacyExperience().gpp_settings,
                us_approach: GPPUSApproach.STATE,
              },
            }),
            privacy_notices: mockUSStatePrivacyNotices() as PrivacyNotice[],
          },
          consentPreferencesToSave: [
            {
              consentPreference: UserConsentPreference.OPT_OUT,
              notice: mockUSStatePrivacyNotices()[0] as PrivacyNotice,
              noticeHistoryId: "4567",
            },
          ],
        }),
      ),
    );
  });
  it("should map us state gpp string to consent preferences when opt in to all", () => {
    mockWindowFides({
      experience: {
        ...mockPrivacyExperience({
          region: "us_ca",
          gpp_settings: {
            ...mockPrivacyExperience().gpp_settings,
            us_approach: GPPUSApproach.STATE,
          },
        }),
        privacy_notices: mockUSStatePrivacyNotices() as PrivacyNotice[],
      },
    });
    const cmpApi = new CmpApi(1, 1);
    fidesStringToConsent({ fidesString: ",,DBABBg~BUoAAABY.QA", cmpApi });
    expect(updateConsentPreferences).toHaveBeenCalledWith(
      expect.objectContaining(
        expectUpdateConsentPreferences({
          experience: {
            ...mockPrivacyExperience({
              region: "us_ca",
              gpp_settings: {
                ...mockPrivacyExperience().gpp_settings,
                us_approach: GPPUSApproach.STATE,
              },
            }),
            privacy_notices: mockUSStatePrivacyNotices() as PrivacyNotice[],
          },
          consentPreferencesToSave: [
            {
              consentPreference: UserConsentPreference.OPT_IN,
              notice: mockUSStatePrivacyNotices()[0] as PrivacyNotice,
              noticeHistoryId: "4567",
            },
          ],
        }),
      ),
    );
  });
  it("should map gpp string to array based (sensitive) consent preferences", () => {
    const mockSensitivePrivacyNotices: Partial<PrivacyNotice>[] = [
      {
        name: "Known Child Sensitive Data Consents (GPP - US National)",
        notice_key: "known_child_sensitive_data_consents_gpp_us_national",
        consent_mechanism: ConsentMechanism.OPT_IN,
        framework: PrivacyNoticeFramework.GPP_US_NATIONAL,
        default_preference: UserConsentPreference.OPT_OUT,
        id: "9876",
        translations: [
          {
            language: "en",
            privacy_notice_history_id: "567567",
          },
        ],
        gpp_field_mapping: [
          {
            region: "us",
            notice: undefined,
            mechanism: [
              {
                field: "KnownChildSensitiveDataConsents",
                not_available: "000",
                opt_out: "111",
                not_opt_out: "222",
              },
            ],
          },
        ],
      },
      {
        name: "Sensitive Personal Data Sharing (GPP - US National)",
        notice_key: "sensitive_personal_data_sharing_gpp_us_national",
        consent_mechanism: ConsentMechanism.OPT_IN,
        data_uses: ["third_party_sharing.legal_obligation"],
        framework: PrivacyNoticeFramework.GPP_US_NATIONAL,
        default_preference: UserConsentPreference.OPT_OUT,
        id: "5432",
        translations: [
          {
            language: "en",
            privacy_notice_history_id: "678678",
          },
        ],
        gpp_field_mapping: [
          {
            region: "us",
            notice: [
              "SensitiveDataLimitUseNotice",
              "SensitiveDataProcessingOptOutNotice",
            ],
            mechanism: [
              {
                field: "SensitiveDataProcessing",
                not_available: "0000000000000000",
                opt_out: "1111111111111111",
                not_opt_out: "2222222222222222",
              },
            ],
          },
        ],
      },
    ];

    mockWindowFides({
      experience: {
        ...mockPrivacyExperience(),
        privacy_notices: mockSensitivePrivacyNotices as PrivacyNotice[],
      },
    });
    const cmpApi = new CmpApi(1, 1);
    // opt in to all
    fidesStringToConsent({ fidesString: ",,DBABLA~BAFAqqqqqqho.QA", cmpApi });
    expect(updateConsentPreferences).toHaveBeenCalledWith(
      expect.objectContaining(
        expectUpdateConsentPreferences({
          experience: {
            ...mockPrivacyExperience(),
            privacy_notices: mockSensitivePrivacyNotices as PrivacyNotice[],
          },
          consentPreferencesToSave: [
            {
              consentPreference: UserConsentPreference.OPT_IN,
              notice: mockSensitivePrivacyNotices[0] as PrivacyNotice,
              noticeHistoryId: "567567",
            },
            {
              consentPreference: UserConsentPreference.OPT_IN,
              notice: mockSensitivePrivacyNotices[1] as PrivacyNotice,
              noticeHistoryId: "678678",
            },
          ],
        }),
      ),
    );

    // opt out of one
    fidesStringToConsent({ fidesString: ",,DBABLA~BAFAqqqqqlRo.QA", cmpApi });
    expect(updateConsentPreferences).toHaveBeenCalledWith(
      expect.objectContaining(
        expectUpdateConsentPreferences({
          experience: {
            ...mockPrivacyExperience(),
            privacy_notices: mockSensitivePrivacyNotices as PrivacyNotice[],
          },
          consentPreferencesToSave: [
            {
              consentPreference: UserConsentPreference.OPT_OUT,
              notice: mockSensitivePrivacyNotices[0] as PrivacyNotice,
              noticeHistoryId: "567567",
            },
            {
              consentPreference: UserConsentPreference.OPT_IN,
              notice: mockSensitivePrivacyNotices[1] as PrivacyNotice,
              noticeHistoryId: "678678",
            },
          ],
        }),
      ),
    );
  });
});
