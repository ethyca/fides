import { automaticallyApplyPreferences } from "../../src/lib/automated-consent";
import { getConsentContext } from "../../src/lib/consent-context";
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
import { updateConsentPreferences } from "../../src/lib/preferences";

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

// Mock fidesDebugger
(globalThis as any).fidesDebugger = jest.fn();

const mockGetConsentContext = getConsentContext as jest.MockedFunction<
  typeof getConsentContext
>;
const mockUpdateConsentPreferences =
  updateConsentPreferences as jest.MockedFunction<
    typeof updateConsentPreferences
  >;

describe("automaticallyApplyPreferences", () => {
  const mockCookie: FidesCookie = {
    consent: {},
    identity: {},
    fides_meta: {},
    tcf_consent: {},
  };

  const mockOptions: FidesInitOptions = {
    fidesApiUrl: "https://api.example.com",
    debug: false,
    geolocationApiUrl: "",
    isOverlayEnabled: true,
    isPrefetchEnabled: false,
    isGeolocationEnabled: false,
    overlayParentId: null,
    modalLinkId: "",
    privacyCenterUrl: "",
    tcfEnabled: false,
    gppEnabled: false,
    fidesEmbed: false,
    fidesDisableSaveApi: false,
    fidesDisableNoticesServedApi: false,
    fidesDisableBanner: false,
    fidesString: null,
    apiOptions: null,
    fidesTcfGdprApplies: false,
    fidesJsBaseUrl: "",
    customOptionsPath: null,
    preventDismissal: false,
    allowHTMLDescription: null,
    base64Cookie: false,
    fidesLocale: undefined,
    fidesPrimaryColor: null,
    fidesClearCookie: false,
    showFidesBrandLink: false,
    fidesConsentOverride: null,
    otFidesMapping: null,
    fidesDisabledNotices: null,
    fidesConsentNonApplicableFlagMode: null,
    fidesConsentFlagType: null,
  };

  const mockI18n = {
    locale: "en",
    t: jest.fn((key: string) => key),
  } as any;

  beforeEach(() => {
    jest.clearAllMocks();
    mockUpdateConsentPreferences.mockResolvedValue(undefined);
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

    it("applies GPC to notices when GPC is enabled", async () => {
      mockGetConsentContext.mockReturnValue({
        globalPrivacyControl: true,
      });

      const result = await automaticallyApplyPreferences({
        savedConsent: {}, // No prior consent
        effectiveExperience: mockRegularExperience,
        cookie: mockCookie,
        fidesRegionString: "us",
        fidesOptions: mockOptions,
        i18n: mockI18n,
      });

      expect(result).toBe(true);
      expect(mockUpdateConsentPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          consentMethod: ConsentMethod.GPC,
          consentPreferencesToSave: expect.arrayContaining([
            expect.objectContaining({
              notice: expect.objectContaining({
                notice_key: "analytics",
              }),
              consentPreference: UserConsentPreference.OPT_OUT, // GPC applied
            }),
            expect.objectContaining({
              notice: expect.objectContaining({
                notice_key: "marketing",
              }),
              consentPreference: UserConsentPreference.OPT_OUT, // GPC applied
            }),
          ]),
        }),
      );
    });

    it("does not apply GPC when GPC is disabled", async () => {
      mockGetConsentContext.mockReturnValue({
        globalPrivacyControl: false,
      });

      const result = await automaticallyApplyPreferences({
        savedConsent: {},
        effectiveExperience: mockRegularExperience,
        cookie: mockCookie,
        fidesRegionString: "us",
        fidesOptions: mockOptions,
        i18n: mockI18n,
      });

      expect(result).toBe(false);
      expect(mockUpdateConsentPreferences).not.toHaveBeenCalled();
    });

    it("does not apply GPC to notices that already have prior consent", async () => {
      mockGetConsentContext.mockReturnValue({
        globalPrivacyControl: true,
      });

      const result = await automaticallyApplyPreferences({
        savedConsent: {
          analytics: true, // Prior consent exists
        },
        effectiveExperience: mockRegularExperience,
        cookie: mockCookie,
        fidesRegionString: "us",
        fidesOptions: mockOptions,
        i18n: mockI18n,
      });

      expect(result).toBe(true);
      expect(mockUpdateConsentPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          consentMethod: ConsentMethod.GPC,
          consentPreferencesToSave: expect.arrayContaining([
            expect.objectContaining({
              notice: expect.objectContaining({
                notice_key: "analytics",
              }),
              consentPreference: UserConsentPreference.OPT_IN, // Prior consent preserved, GPC not applied
            }),
            expect.objectContaining({
              notice: expect.objectContaining({
                notice_key: "marketing",
              }),
              consentPreference: UserConsentPreference.OPT_OUT, // GPC applied (no prior consent)
            }),
          ]),
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

      mockGetConsentContext.mockReturnValue({
        globalPrivacyControl: true,
      });

      const result = await automaticallyApplyPreferences({
        savedConsent: {},
        effectiveExperience: experienceWithMixedGpcSupport,
        cookie: mockCookie,
        fidesRegionString: "us",
        fidesOptions: mockOptions,
        i18n: mockI18n,
      });

      expect(result).toBe(true);
      expect(mockUpdateConsentPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          consentMethod: ConsentMethod.GPC,
          consentPreferencesToSave: expect.arrayContaining([
            expect.objectContaining({
              notice: expect.objectContaining({
                notice_key: "analytics",
              }),
              consentPreference: UserConsentPreference.OPT_OUT, // GPC applied
            }),
            expect.objectContaining({
              notice: expect.objectContaining({
                notice_key: "marketing",
              }),
              consentPreference: UserConsentPreference.OPT_IN, // GPC not applied (has_gpc_flag: false)
            }),
          ]),
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

      mockGetConsentContext.mockReturnValue({
        globalPrivacyControl: true,
      });

      const result = await automaticallyApplyPreferences({
        savedConsent: {},
        effectiveExperience: experienceWithNoticeOnly,
        cookie: mockCookie,
        fidesRegionString: "us",
        fidesOptions: mockOptions,
        i18n: mockI18n,
      });

      expect(result).toBe(false);
      expect(mockUpdateConsentPreferences).not.toHaveBeenCalled();
    });
  });

  describe("GPC with TCF custom notices", () => {
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
      mockGetConsentContext.mockReturnValue({
        globalPrivacyControl: true,
      });

      const result = await automaticallyApplyPreferences({
        savedConsent: {}, // No prior consent
        effectiveExperience: mockTCFExperienceWithCustomNotices,
        cookie: mockCookie,
        fidesRegionString: "eea",
        fidesOptions: mockOptions,
        i18n: mockI18n,
      });

      expect(result).toBe(true);
      expect(mockUpdateConsentPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          consentMethod: ConsentMethod.GPC,
          consentPreferencesToSave: expect.arrayContaining([
            expect.objectContaining({
              notice: expect.objectContaining({
                notice_key: "custom_notice_1",
              }),
              consentPreference: UserConsentPreference.OPT_OUT, // GPC applied
            }),
            expect.objectContaining({
              notice: expect.objectContaining({
                notice_key: "custom_notice_2",
              }),
              consentPreference: UserConsentPreference.OPT_OUT, // GPC applied
            }),
          ]),
        }),
      );
    });
  });
});
