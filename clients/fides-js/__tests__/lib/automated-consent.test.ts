import {
  automaticallyApplyPreferences,
  calculateAutomatedConsent,
  saveAutomatedPreferencesToApi,
} from "../../src/lib/automated-consent";
import {
  AutomatedConsentContext,
  getGpcStatus,
} from "../../src/lib/consent-context";
import {
  ComponentType,
  ConsentMechanism,
  ConsentMethod,
  ExperienceConfig,
  FidesCookie,
  FidesGlobal,
  FidesInitOptions,
  PrivacyExperience,
  PrivacyNotice,
  UserConsentPreference,
} from "../../src/lib/consent-types";
import { decodeNoticeConsentString } from "../../src/lib/consent-utils";
import { savePreferencesApi, updateConsent } from "../../src/lib/preferences";
import mockFidesInitOptions from "../__fixtures__/mock_fides_init_options.json";

// Mock dependencies
jest.mock("../../src/lib/consent-context");
jest.mock("../../src/lib/preferences");
jest.mock("../../src/lib/fides-string", () => ({
  decodeFidesString: jest.fn().mockReturnValue({ nc: null }),
}));
jest.mock("../../src/lib/consent-migration", () => ({
  readConsentFromAnyProvider: jest
    .fn()
    .mockReturnValue({ consent: null, method: null }),
}));
jest.mock("../../src/lib/cookie", () => ({
  getFidesConsentCookie: jest.fn().mockReturnValue(null),
}));
jest.mock("../../src/lib/consent-utils", () => ({
  ...jest.requireActual("../../src/lib/consent-utils"),
  decodeNoticeConsentString: jest.fn().mockReturnValue({}),
}));
jest.mock("../../src/lib/fides-lifecycle-manager", () => ({
  fidesLifecycleManager: {
    getServedNoticeHistoryId: jest.fn().mockReturnValue(undefined),
  },
}));

// Mock fidesDebugger
(globalThis as any).fidesDebugger = jest.fn();

const mockGetGpcContext = getGpcStatus as jest.MockedFunction<
  typeof getGpcStatus
>;
const mockUpdateConsent = updateConsent as jest.MockedFunction<
  typeof updateConsent
>;
const mockSavePreferencesApi = savePreferencesApi as jest.MockedFunction<
  typeof savePreferencesApi
>;

describe("automaticallyApplyPreferences", () => {
  const mockCookie: FidesCookie = {
    consent: {},
    identity: {},
    fides_meta: {},
    tcf_consent: {},
  };

  const mockOptions: FidesInitOptions =
    mockFidesInitOptions as FidesInitOptions;

  const mockFidesGlobal = (override?: Partial<FidesGlobal>) => {
    let fidesGlobal: Pick<
      FidesGlobal,
      | "experience"
      | "cookie"
      | "geolocation"
      | "options"
      | "locale"
      | "saved_consent"
    > = {
      saved_consent: {},
      experience: undefined,
      cookie: mockCookie,
      geolocation: {
        country: "US",
      },
      options: mockOptions,
      locale: "en",
    };
    if (override) {
      fidesGlobal = { ...fidesGlobal, ...override };
    }
    return fidesGlobal;
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUpdateConsent.mockResolvedValue(undefined);
  });

  describe("Regular (non-TCF) experience", () => {
    const mockRegularExperience: PrivacyExperience = {
      id: "regular-exp-1",
      region: "us",
      created_at: "2023-01-01T00:00:00Z",
      updated_at: "2023-01-01T00:00:00Z",
      experience_config: {
        id: "config-1",
        component: ComponentType.BANNER_AND_MODAL,
        translations: [
          {
            language: "en",
            privacy_experience_config_history_id: "config-history-1",
          },
        ],
      } as ExperienceConfig,
      privacy_notices: [
        {
          id: "notice-1",
          notice_key: "analytics",
          name: "Analytics",
          consent_mechanism: ConsentMechanism.OPT_OUT,
          has_gpc_flag: true,
          default_preference: UserConsentPreference.OPT_OUT,
          translations: [
            {
              language: "en",
              title: "Analytics",
              description: "Analytics description",
              privacy_notice_history_id: "notice-history-1",
            },
          ],
        },
        {
          id: "notice-2",
          notice_key: "marketing",
          name: "Marketing",
          consent_mechanism: ConsentMechanism.OPT_IN,
          has_gpc_flag: true,
          default_preference: UserConsentPreference.OPT_IN,
          translations: [
            {
              language: "en",
              title: "Marketing",
              description: "Marketing description",
              privacy_notice_history_id: "notice-history-2",
            },
          ],
        },
      ] as PrivacyNotice[],
    };
    mockFidesGlobal({ experience: mockRegularExperience });

    it("applies GPC to notices when GPC is enabled", async () => {
      mockGetGpcContext.mockReturnValue({
        globalPrivacyControl: true,
      });
      const fidesGlobal = mockFidesGlobal({
        experience: mockRegularExperience,
      });

      const result = await automaticallyApplyPreferences(fidesGlobal);

      expect(result).toBe(true);
      expect(mockUpdateConsent).toHaveBeenCalledWith(
        fidesGlobal,
        expect.objectContaining({
          consentMethod: ConsentMethod.GPC,
          noticeConsent: { analytics: false, marketing: false },
        }),
      );
    });

    it("does not apply GPC when GPC is disabled", async () => {
      mockGetGpcContext.mockReturnValue({
        globalPrivacyControl: false,
      });

      const result = await automaticallyApplyPreferences(mockFidesGlobal());

      expect(result).toBe(false);
      expect(mockUpdateConsent).not.toHaveBeenCalled();
    });

    it("does not apply GPC to notices that already have prior consent", async () => {
      mockGetGpcContext.mockReturnValue({
        globalPrivacyControl: true,
      });
      const fidesGlobal = mockFidesGlobal({
        saved_consent: {
          analytics: true,
        },
        experience: mockRegularExperience,
      });

      const result = await automaticallyApplyPreferences(fidesGlobal);

      expect(result).toBe(true);
      expect(mockUpdateConsent).toHaveBeenCalledWith(
        fidesGlobal,
        expect.objectContaining({
          consentMethod: ConsentMethod.GPC,
          noticeConsent: { analytics: true, marketing: false },
        }),
      );
    });

    it("only applies GPC to notices with has_gpc_flag set to true", async () => {
      const experienceWithMixedGpcSupport: PrivacyExperience = {
        ...mockRegularExperience,
        privacy_notices: [
          {
            ...mockRegularExperience.privacy_notices![0],
            has_gpc_flag: true, // Supports GPC
          },
          {
            ...mockRegularExperience.privacy_notices![1],
            has_gpc_flag: false, // Does not support GPC
          },
        ] as PrivacyNotice[],
      };

      mockGetGpcContext.mockReturnValue({
        globalPrivacyControl: true,
      });

      const fidesGlobal = mockFidesGlobal({
        experience: experienceWithMixedGpcSupport,
      });

      const result = await automaticallyApplyPreferences(fidesGlobal);

      expect(result).toBe(true);
      expect(mockUpdateConsent).toHaveBeenCalledWith(
        fidesGlobal,
        expect.objectContaining({
          consentMethod: ConsentMethod.GPC,
          noticeConsent: { analytics: false, marketing: true },
        }),
      );
    });

    it("does not apply GPC to notice-only mechanisms", async () => {
      const experienceWithNoticeOnly: PrivacyExperience = {
        ...mockRegularExperience,
        privacy_notices: [
          {
            ...mockRegularExperience.privacy_notices![0],
            consent_mechanism: ConsentMechanism.NOTICE_ONLY,
          },
        ] as PrivacyNotice[],
      };
      const fidesGlobal = mockFidesGlobal({
        experience: experienceWithNoticeOnly,
      });

      mockGetGpcContext.mockReturnValue({
        globalPrivacyControl: true,
      });

      const result = await automaticallyApplyPreferences(fidesGlobal);

      expect(result).toBe(false);
      expect(mockUpdateConsent).not.toHaveBeenCalled();
    });
  });

  describe("TCF experience", () => {
    const mockTCFExperienceWithCustomNotices: PrivacyExperience = {
      id: "tcf-exp-1",
      region: "eea",
      created_at: "2023-01-01T00:00:00Z",
      updated_at: "2023-01-01T00:00:00Z",
      experience_config: {
        id: "config-1",
        component: ComponentType.TCF_OVERLAY,
        translations: [
          {
            language: "en",
            privacy_experience_config_history_id: "config-history-1",
          },
        ],
      } as ExperienceConfig,
      privacy_notices: [
        {
          id: "notice-1",
          notice_key: "custom_notice_1",
          name: "Custom Notice 1",
          consent_mechanism: ConsentMechanism.OPT_OUT,
          has_gpc_flag: true,
          default_preference: UserConsentPreference.OPT_OUT,
          translations: [
            {
              language: "en",
              title: "Custom Notice 1",
              description: "Description for custom notice 1",
              privacy_notice_history_id: "notice-history-1",
            },
          ],
        },
        {
          id: "notice-2",
          notice_key: "custom_notice_2",
          name: "Custom Notice 2",
          consent_mechanism: ConsentMechanism.OPT_IN,
          has_gpc_flag: true, // This notice also supports GPC
          default_preference: UserConsentPreference.OPT_IN,
          translations: [
            {
              language: "en",
              title: "Custom Notice 2",
              description: "Description for custom notice 2",
              privacy_notice_history_id: "notice-history-2",
            },
          ],
        },
      ] as PrivacyNotice[],
    };
    it("still applies GPC to TCF experiences with custom notices", async () => {
      mockGetGpcContext.mockReturnValue({
        globalPrivacyControl: true,
      });

      const fidesGlobal = mockFidesGlobal({
        experience: mockTCFExperienceWithCustomNotices,
        geolocation: {
          country: "EEA",
        },
      });

      const result = await automaticallyApplyPreferences(fidesGlobal);

      expect(result).toBe(true);
      expect(mockUpdateConsent).toHaveBeenCalledWith(
        fidesGlobal,
        expect.objectContaining({
          consentMethod: ConsentMethod.GPC,
          noticeConsent: { custom_notice_1: false, custom_notice_2: false },
        }),
      );
    });
  });
});

describe("calculateAutomatedConsent", () => {
  const mockRegularExperience: PrivacyExperience = {
    id: "regular-exp-1",
    region: "us",
    created_at: "2023-01-01T00:00:00Z",
    updated_at: "2023-01-01T00:00:00Z",
    experience_config: {
      id: "config-1",
      component: ComponentType.BANNER_AND_MODAL,
      translations: [
        {
          language: "en",
          privacy_experience_config_history_id: "config-history-1",
        },
      ],
    } as ExperienceConfig,
    privacy_notices: [
      {
        id: "notice-1",
        notice_key: "analytics",
        name: "Analytics",
        consent_mechanism: ConsentMechanism.OPT_OUT,
        has_gpc_flag: true,
        default_preference: UserConsentPreference.OPT_OUT,
        translations: [
          {
            language: "en",
            title: "Analytics",
            description: "Analytics description",
            privacy_notice_history_id: "notice-history-1",
          },
        ],
      },
      {
        id: "notice-2",
        notice_key: "marketing",
        name: "Marketing",
        consent_mechanism: ConsentMechanism.OPT_IN,
        has_gpc_flag: true,
        default_preference: UserConsentPreference.OPT_IN,
        translations: [
          {
            language: "en",
            title: "Marketing",
            description: "Marketing description",
            privacy_notice_history_id: "notice-history-2",
          },
        ],
      },
    ] as PrivacyNotice[],
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("returns no consent when context has no automated sources", () => {
    const context: AutomatedConsentContext = {};
    const savedConsent = {};

    const result = calculateAutomatedConsent(
      mockRegularExperience,
      savedConsent,
      context,
    );

    expect(result.applied).toBe(false);
    expect(result.consentMethod).toBeNull();
    expect(result.noticeConsent).toEqual({});
  });

  it("applies GPC when globalPrivacyControl is true", () => {
    const context: AutomatedConsentContext = {
      globalPrivacyControl: true,
    };
    const savedConsent = {};

    const result = calculateAutomatedConsent(
      mockRegularExperience,
      savedConsent,
      context,
    );

    expect(result.applied).toBe(true);
    expect(result.consentMethod).toBe(ConsentMethod.GPC);
    expect(result.noticeConsent).toEqual({
      analytics: false,
      marketing: false,
    });
  });

  it("applies migrated consent with higher priority than GPC", () => {
    const context: AutomatedConsentContext = {
      globalPrivacyControl: true,
      migratedConsent: {
        analytics: true, // Migrated says opt-in
      },
      migrationMethod: ConsentMethod.EXTERNAL_PROVIDER,
    };
    const savedConsent = {};

    const result = calculateAutomatedConsent(
      mockRegularExperience,
      savedConsent,
      context,
    );

    expect(result.applied).toBe(true);
    expect(result.consentMethod).toBe(ConsentMethod.EXTERNAL_PROVIDER);
    expect(result.noticeConsent).toEqual({
      analytics: true, // Migrated consent takes priority
      marketing: false, // GPC applied to marketing
    });
  });

  it("applies notice consent string with priority between migrated and GPC", () => {
    (decodeNoticeConsentString as jest.Mock).mockReturnValueOnce({
      analytics: true,
    });

    const context: AutomatedConsentContext = {
      globalPrivacyControl: true,
      noticeConsentString: "analytics:true", // Notice string says opt-in
    };
    const savedConsent = {};

    const result = calculateAutomatedConsent(
      mockRegularExperience,
      savedConsent,
      context,
    );

    expect(result.applied).toBe(true);
    // Should be SCRIPT method when notice consent string is applied
    expect(result.consentMethod).toBe(ConsentMethod.SCRIPT);
  });

  it("respects saved consent for GPC", () => {
    const context: AutomatedConsentContext = {
      globalPrivacyControl: true,
    };
    const savedConsent = {
      analytics: true, // User already opted in
    };

    const result = calculateAutomatedConsent(
      mockRegularExperience,
      savedConsent,
      context,
    );

    expect(result.applied).toBe(true);
    expect(result.consentMethod).toBe(ConsentMethod.GPC);
    expect(result.noticeConsent).toEqual({
      analytics: true, // Preserved existing consent
      marketing: false, // GPC applied only to marketing
    });
  });

  it("respects saved consent over migrated consent (including false values)", () => {
    const context: AutomatedConsentContext = {
      migratedConsent: {
        analytics: true, // Migrated says opt-in
        marketing: true, // Migrated says opt-in
      },
      migrationMethod: ConsentMethod.EXTERNAL_PROVIDER,
      hasFidesCookie: true, // Existing Fides cookie present
    };
    const savedConsent = {
      analytics: false, // User previously opted out
      marketing: false, // User previously opted out
    };

    const result = calculateAutomatedConsent(
      mockRegularExperience,
      savedConsent,
      context,
    );

    // No automated consent applied since hasFidesCookie is true
    expect(result.applied).toBe(false);
    expect(result.consentMethod).toBeNull();
    expect(result.noticeConsent).toEqual({});
  });

  it("applies migrated consent when no Fides cookie exists", () => {
    const context: AutomatedConsentContext = {
      migratedConsent: {
        analytics: true, // Migrated says opt-in
        marketing: false, // Migrated says opt-out
      },
      migrationMethod: ConsentMethod.EXTERNAL_PROVIDER,
      hasFidesCookie: false, // No existing Fides cookie
    };
    const savedConsent = {}; // Empty saved consent

    const result = calculateAutomatedConsent(
      mockRegularExperience,
      savedConsent,
      context,
    );

    // Migrated consent should be applied
    expect(result.applied).toBe(true);
    expect(result.consentMethod).toBe(ConsentMethod.EXTERNAL_PROVIDER);
    expect(result.noticeConsent).toEqual({
      analytics: true, // From migrated consent
      marketing: false, // From migrated consent
    });
  });

  it("does not apply GPC to notices without has_gpc_flag", () => {
    const experienceWithoutGpcFlag: PrivacyExperience = {
      ...mockRegularExperience,
      privacy_notices: [
        {
          ...mockRegularExperience.privacy_notices![0],
          has_gpc_flag: false,
        },
        {
          ...mockRegularExperience.privacy_notices![1],
          has_gpc_flag: false,
        },
      ] as PrivacyNotice[],
    };

    const context: AutomatedConsentContext = {
      globalPrivacyControl: true,
    };
    const savedConsent = {};

    const result = calculateAutomatedConsent(
      experienceWithoutGpcFlag,
      savedConsent,
      context,
    );

    expect(result.applied).toBe(false);
    expect(result.consentMethod).toBeNull();
  });

  it("does not apply GPC to notice-only mechanisms", () => {
    const experienceWithNoticeOnly: PrivacyExperience = {
      ...mockRegularExperience,
      privacy_notices: [
        {
          ...mockRegularExperience.privacy_notices![0],
          consent_mechanism: ConsentMechanism.NOTICE_ONLY,
        },
      ] as PrivacyNotice[],
    };

    const context: AutomatedConsentContext = {
      globalPrivacyControl: true,
    };
    const savedConsent = {};

    const result = calculateAutomatedConsent(
      experienceWithNoticeOnly,
      savedConsent,
      context,
    );

    expect(result.applied).toBe(false);
    expect(result.consentMethod).toBeNull();
  });

  it("returns no consent when experience is invalid", () => {
    const invalidExperience = {} as PrivacyExperience;
    const context: AutomatedConsentContext = {
      globalPrivacyControl: true,
    };
    const savedConsent = {};

    const result = calculateAutomatedConsent(
      invalidExperience,
      savedConsent,
      context,
    );

    expect(result.applied).toBe(false);
    expect(result.consentMethod).toBeNull();
    expect(result.noticeConsent).toEqual({});
  });
});

describe("saveAutomatedPreferencesToApi", () => {
  const mockRegularExperience: PrivacyExperience = {
    id: "regular-exp-1",
    region: "us",
    created_at: "2023-01-01T00:00:00Z",
    updated_at: "2023-01-01T00:00:00Z",
    experience_config: {
      id: "config-1",
      component: ComponentType.BANNER_AND_MODAL,
      privacy_experience_config_history_id: "config-history-1",
      translations: [
        {
          language: "en",
          privacy_experience_config_history_id: "config-history-1",
        },
      ],
    } as any,
    privacy_notices: [
      {
        id: "notice-1",
        notice_key: "analytics",
        name: "Analytics",
        consent_mechanism: ConsentMechanism.OPT_OUT,
        has_gpc_flag: true,
        default_preference: UserConsentPreference.OPT_OUT,
        translations: [
          {
            language: "en",
            title: "Analytics",
            description: "Analytics description",
            privacy_notice_history_id: "notice-history-1",
          },
        ],
      },
    ] as PrivacyNotice[],
  };

  const mockCookie: FidesCookie = {
    consent: {},
    identity: {},
    fides_meta: {},
    tcf_consent: {},
  };

  const mockOptions: FidesInitOptions =
    mockFidesInitOptions as FidesInitOptions;

  const mockFidesGlobal = {
    experience: mockRegularExperience,
    cookie: mockCookie,
    config: {
      options: mockOptions,
      geolocation: {
        location: "US",
      },
    },
    locale: "en",
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockSavePreferencesApi.mockResolvedValue(undefined);
  });

  it("calls savePreferencesApi with the correct parameters", async () => {
    const noticeConsent = {
      analytics: false,
      marketing: false,
    };
    const consentMethod = ConsentMethod.GPC;

    await saveAutomatedPreferencesToApi(
      mockFidesGlobal,
      noticeConsent,
      consentMethod,
    );

    expect(mockSavePreferencesApi).toHaveBeenCalledWith(
      mockOptions,
      mockFidesGlobal.cookie,
      mockFidesGlobal.experience,
      consentMethod,
      "config-history-1",
      [
        {
          noticeHistoryId: "notice-history-1",
          consentPreference: "opt_out",
        },
      ],
      undefined,
      "us",
      undefined,
    );
  });

  it("does not throw when savePreferencesApi fails", async () => {
    mockSavePreferencesApi.mockRejectedValue(new Error("API error"));

    const noticeConsent = {
      analytics: false,
    };
    const consentMethod = ConsentMethod.GPC;

    await expect(
      saveAutomatedPreferencesToApi(
        mockFidesGlobal,
        noticeConsent,
        consentMethod,
      ),
    ).resolves.not.toThrow();

    expect(mockSavePreferencesApi).toHaveBeenCalled();
  });
});
