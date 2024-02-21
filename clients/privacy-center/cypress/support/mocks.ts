import {
  PrivacyNotice,
  PrivacyNoticeTranslations,
  EnforcementLevel,
  ExperienceConfig,
  ConsentMechanism,
  UserConsentPreference,
  FidesCookie,
} from "fides-js";
import {
  EmbeddedVendor,
  TCFVendorConsentRecord,
  TCFVendorLegitimateInterestsRecord,
  TCFVendorRelationships,
} from "~/types/api";

export const mockPrivacyNoticeTranslation = (
  params?: Partial<PrivacyNoticeTranslations>
) => {
  const translation = {
    id: "pri_sdafsf",
    language: "en",
    title: "Test privacy notice",
    description: "a test sample privacy notice configuration",
    privacy_notice_history_id: "pri_b09058a7-9f54-4360-8da5-4521e8975d4f",
  };
  return { ...translation, ...params };
};

/**
 * Mocks the privacy notice, optionally pass in custom translations that override the default translation
 */
export const mockPrivacyNotice = (
  params: Partial<PrivacyNotice>,
  translations?: PrivacyNoticeTranslations[]
) => {
  const defaultTranslations = [mockPrivacyNoticeTranslation()];
  const notice = {
    name: "Test privacy notice with GPC enabled",
    internal_description:
      "a test sample privacy notice configuration for internal use",
    consent_mechanism: ConsentMechanism.OPT_OUT,
    default_preference: UserConsentPreference.OPT_IN,
    has_gpc_flag: true,
    disabled: false,
    origin: "12435134",
    data_uses: ["advertising", "third_party_sharing"],
    enforcement_level: EnforcementLevel.SYSTEM_WIDE,
    id: "pri_4bed96d0-b9e3-4596-a807-26b783836374",
    created_at: "2023-04-24T21:29:08.870351+00:00",
    updated_at: "2023-04-24T21:29:08.870351+00:00",
    notice_key: "advertising",
    cookies: [],
    translations: translations || defaultTranslations,
  };
  return { ...notice, ...params };
};

export const mockCookie = (params: Partial<FidesCookie>) => {
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

  return { ...cookie, ...params };
};

/**
 * Mocks the various TCF vendor objects, since they are related to each other.
 * By providing some basic vendor data, we return:
 * 1. `record`: a top level TCFVendorConsentRecord | TCFVendorLegitimateInterestsRecord
 * 2. `relationship`: a filled out TCFVendorRelationships object
 * 3. `embedded`: an EmbeddedVendor object which goes inside Purposes and Features
 */
export const mockTcfVendorObjects = (
  params: Partial<TCFVendorConsentRecord | TCFVendorLegitimateInterestsRecord>
): {
  record: TCFVendorConsentRecord | TCFVendorLegitimateInterestsRecord;
  relationship: TCFVendorRelationships;
  embedded: EmbeddedVendor;
} => {
  const baseVendor = {
    id: "gvl.2",
    has_vendor_id: true,
    name: "Test",
    description: "A longer description",
    default_preference: UserConsentPreference.OPT_OUT,
    current_preference: undefined,
    outdated_preference: undefined,
    current_served: undefined,
    outdated_served: undefined,
    purpose_consents: [
      {
        id: 4,
        name: "Use profiles to select personalised advertising",
      },
    ],
  };
  const record = { ...baseVendor, ...params };

  const relationship = {
    cookie_max_age_seconds: 360000,
    cookie_refresh: true,
    id: record.id,
    has_vendor_id: record.has_vendor_id,
    name: record.name,
    description: record.description,
    special_purposes: [
      {
        id: 1,
        name: "Ensure security, prevent and detect fraud, and fix errors",
        retention_period: "1",
      },
    ],
    uses_cookies: true,
    uses_non_cookie_access: true,
    features: [],
    special_features: [],
    privacy_policy_url: "https://www.example.com/privacy",
    legitimate_interest_disclosure_url:
      "https://www.example.com/legitimate_interest_disclosure",
  };

  const embedded = {
    id: record.id,
    name: record.name,
  };
  return { record, relationship, embedded };
};
