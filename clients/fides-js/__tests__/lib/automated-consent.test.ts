import {
  calculateAutomatedConsent,
  saveAutomatedPreferencesToApi,
} from "../../src/lib/automated-consent";
import { ConsentContext } from "../../src/lib/consent-context";
import {
  ComponentType,
  ConsentMechanism,
  ConsentMethod,
  ExperienceConfig,
  FidesCookie,
  FidesInitOptions,
  PrivacyExperience,
  PrivacyNotice,
  UserConsentPreference,
} from "../../src/lib/consent-types";
import { decodeNoticeConsentString } from "../../src/lib/consent-utils";
import { savePreferencesApi } from "../../src/lib/preferences";
import mockFidesInitOptions from "../__fixtures__/mock_fides_init_options.json";

// Mock dependencies
jest.mock("../../src/lib/preferences");
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

const mockSavePreferencesApi = savePreferencesApi as jest.MockedFunction<
  typeof savePreferencesApi
>;

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
    const context: ConsentContext = {};
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
    const context: ConsentContext = {
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
    const context: ConsentContext = {
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

  it("applies notice consent string with priority over GPC", () => {
    (decodeNoticeConsentString as jest.Mock).mockReturnValueOnce({
      analytics: true,
    });

    const context: ConsentContext = {
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
    expect(result.noticeConsent).toEqual({
      analytics: true, // Notice string applied (overrides GPC)
      marketing: false, // GPC applied
    });
  });

  it("respects saved consent for GPC", () => {
    const context: ConsentContext = {
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
    const context: ConsentContext = {
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
    const context: ConsentContext = {
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

  it("forces NOTICE_ONLY mechanisms to true, ignoring migrated consent", () => {
    const experienceWithNoticeOnly: PrivacyExperience = {
      ...mockRegularExperience,
      privacy_notices: [
        {
          ...mockRegularExperience.privacy_notices![0],
          notice_key: "essential",
          consent_mechanism: ConsentMechanism.NOTICE_ONLY,
        },
        {
          ...mockRegularExperience.privacy_notices![1],
          notice_key: "analytics",
          consent_mechanism: ConsentMechanism.OPT_OUT,
        },
      ] as PrivacyNotice[],
    };

    const context: ConsentContext = {
      migratedConsent: {
        essential: false, // Migrated says opt-out (should be ignored)
        analytics: false, // Migrated says opt-out (should be applied)
      },
      migrationMethod: ConsentMethod.EXTERNAL_PROVIDER,
      hasFidesCookie: false,
    };
    const savedConsent = {};

    const result = calculateAutomatedConsent(
      experienceWithNoticeOnly,
      savedConsent,
      context,
    );

    // Migrated consent should be applied, but NOTICE_ONLY must be forced to true
    expect(result.applied).toBe(true);
    expect(result.consentMethod).toBe(ConsentMethod.EXTERNAL_PROVIDER);
    expect(result.noticeConsent).toEqual({
      essential: true, // Forced to true despite migrated consent saying false
      analytics: false, // From migrated consent
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

    const context: ConsentContext = {
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

    const context: ConsentContext = {
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
    const context: ConsentContext = {
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

  it("applies GPC to TCF experiences with custom notices", () => {
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
          has_gpc_flag: true,
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

    const context: ConsentContext = {
      globalPrivacyControl: true,
    };
    const savedConsent = {};

    const result = calculateAutomatedConsent(
      mockTCFExperienceWithCustomNotices,
      savedConsent,
      context,
    );

    expect(result.applied).toBe(true);
    expect(result.consentMethod).toBe(ConsentMethod.GPC);
    expect(result.noticeConsent).toEqual({
      custom_notice_1: false,
      custom_notice_2: false,
    });
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
