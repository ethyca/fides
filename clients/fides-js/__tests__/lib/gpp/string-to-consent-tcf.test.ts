import { CmpApi } from "@iabgpp/cmpapi";

import { InitializedFidesGlobal } from "~/lib/providers/fides-global-context";

import {
  ComponentType,
  ExperienceConfig,
  FidesCookie,
  PrivacyExperienceMinimal,
  UserConsentPreference,
} from "../../../src/lib/consent-types";
import { fidesStringToConsent } from "../../../src/lib/gpp/string-to-consent";
import { makeStub } from "../../../src/lib/gpp/stub";
import {
  updateConsent,
  UpdateConsentOptions,
} from "../../../src/lib/preferences";

// Mock fidesDebugger
(globalThis as any).fidesDebugger = jest.fn();

jest.mock("../../../src/lib/preferences", () => ({
  updateConsent: jest.fn(),
}));

const mockExperienceConfig = (override?: Partial<ExperienceConfig>) => {
  const base: Partial<ExperienceConfig> = {
    component: ComponentType.TCF_OVERLAY,
    translations: [
      { language: "en", privacy_experience_config_history_id: "321" },
    ],
  };
  if (!override) {
    return base;
  }
  return { ...base, ...override };
};

const mockPrivacyExperience = (
  override?: Partial<PrivacyExperienceMinimal>,
) => {
  const base: PrivacyExperienceMinimal = {
    id: "id",
    privacy_notices: [],
    gpp_settings: {
      enabled: true,
      us_approach: undefined,
      mspa_covered_transactions: true,
      mspa_opt_out_option_mode: true,
      mspa_service_provider_mode: false,
      enable_tcfeu_string: true,
    },
    experience_config: mockExperienceConfig() as ExperienceConfig,
    meta: {
      version_hash: "1a2b3c4d5e6f",
    },
    minimal_tcf: true,
    tcf_feature_ids: [1, 2, 3],
    tcf_purpose_consent_ids: [1, 3, 4],
    tcf_purpose_legitimate_interest_ids: [2, 7, 8, 10],
    tcf_special_feature_ids: [],
    tcf_special_purpose_ids: [1, 2],
    tcf_system_consent_ids: [],
    tcf_system_legitimate_interest_ids: [],
    tcf_vendor_consent_ids: ["gvl.740"],
    tcf_vendor_legitimate_interest_ids: ["gvl.740"],
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
      tcfEnabled: true,
      gppEnabled: true,
    },
    cookie: mockFidesCookie(),
    geolocation: {
      location: "eea",
      country: "eea",
    },
    locale: "en",
    experience: mockPrivacyExperience(),
    ...override,
  };
};

const expectUpdateConsent = (
  overrideFidesGlobal?: Partial<InitializedFidesGlobal>,
) => {
  const baseFidesGlobal: Partial<InitializedFidesGlobal> = {
    cookie: mockFidesCookie(),
    experience: mockPrivacyExperience(),
  };
  if (!overrideFidesGlobal) {
    return baseFidesGlobal;
  }
  return { ...baseFidesGlobal, ...overrideFidesGlobal };
};

const expectUpdateConsentOptions = (
  override?: Partial<UpdateConsentOptions>,
) => {
  const base: Partial<UpdateConsentOptions> = {
    noticeConsent: {},
    updateCookie: jest.fn(),
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

  it("should map tcf string to consent preferences with opt in to all", () => {
    mockWindowFides();
    const cmpApi = new CmpApi(1, 1);
    fidesStringToConsent({
      fidesString:
        "CQNvpkAQNvpkAGXABBENBfFgALAAAENAAAAAFyQAQFyAXJABAXIAAAAA,2~~dv.,DBABMA~CQNvpkAQNvpkAGXABBENBfFgALAAAENAAAAAFyQAQFyAXJABAXIAAAAA",
      cmpApi,
    });
    expect(updateConsent).toHaveBeenCalledWith(
      expect.objectContaining(expectUpdateConsent()),
      expect.objectContaining(
        expectUpdateConsentOptions({
          tcf: {
            purpose_consent_preferences: [
              { id: 1, preference: UserConsentPreference.OPT_IN },
              { id: 3, preference: UserConsentPreference.OPT_IN },
              { id: 4, preference: UserConsentPreference.OPT_IN },
            ],
            purpose_legitimate_interests_preferences: [
              { id: 2, preference: UserConsentPreference.OPT_IN },
              { id: 7, preference: UserConsentPreference.OPT_IN },
              { id: 8, preference: UserConsentPreference.OPT_IN },
              { id: 10, preference: UserConsentPreference.OPT_IN },
            ],
            special_feature_preferences: [],
            system_consent_preferences: [],
            system_legitimate_interests_preferences: [],
            vendor_consent_preferences: [
              { id: "gvl.740", preference: UserConsentPreference.OPT_IN },
            ],
            vendor_legitimate_interests_preferences: [
              { id: "gvl.740", preference: UserConsentPreference.OPT_IN },
            ],
          },
          updateCookie: expect.any(Function),
        }),
      ),
    );
  });

  it("should map tcf string to consent preferences with opt out of all", () => {
    mockWindowFides();
    const cmpApi = new CmpApi(1, 1);
    fidesStringToConsent({
      fidesString:
        "CQNvpkAQNvpkAGXABBENBfFgAAAAAAAAAAAAAAAAAAAA,2~~dv.,DBABMA~CQNvpkAQNvpkAGXABBENBfFgAAAAAAAAAAAAAAAAAAAA",
      cmpApi,
    });
    expect(updateConsent).toHaveBeenCalledWith(
      expect.objectContaining(expectUpdateConsent()),
      expect.objectContaining(
        expectUpdateConsentOptions({
          tcf: {
            purpose_consent_preferences: [],
            purpose_legitimate_interests_preferences: [],
            special_feature_preferences: [],
            system_consent_preferences: [],
            system_legitimate_interests_preferences: [],
            vendor_consent_preferences: [],
            vendor_legitimate_interests_preferences: [],
          },
          updateCookie: expect.any(Function),
        }),
      ),
    );
  });

  it("should map tcf string to consent preferences with opt in to some", () => {
    mockWindowFides();
    const cmpApi = new CmpApi(1, 1);
    fidesStringToConsent({
      fidesString:
        "CQNvpkAQNvpkAGXABBENBfFgAJAAAAIAAAAAAAAAAAAA,2~~dv.,DBABMA~CQNvpkAQNvpkAGXABBENBfFgAJAAAAIAAAAAAAAAAAAA",
      cmpApi,
    });
    expect(updateConsent).toHaveBeenCalledWith(
      expect.objectContaining(expectUpdateConsent()),
      expect.objectContaining(
        expectUpdateConsentOptions({
          tcf: {
            purpose_consent_preferences: [
              { id: 1, preference: UserConsentPreference.OPT_IN },
              { id: 4, preference: UserConsentPreference.OPT_IN },
            ],
            purpose_legitimate_interests_preferences: [
              { id: 7, preference: UserConsentPreference.OPT_IN },
            ],
            special_feature_preferences: [],
            system_consent_preferences: [],
            system_legitimate_interests_preferences: [],
            vendor_consent_preferences: [],
            vendor_legitimate_interests_preferences: [],
          },
          updateCookie: expect.any(Function),
        }),
      ),
    );
  });
});
