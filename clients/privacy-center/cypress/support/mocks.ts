import {
  ConsentMechanism,
  EnforcementLevel,
  FidesCookie,
  PrivacyNotice,
  PrivacyNoticeTranslation,
  UserConsentPreference,
} from "fides-js";

import {
  EmbeddedVendor,
  TCFVendorConsentRecord,
  TCFVendorLegitimateInterestsRecord,
  TCFVendorRelationships,
} from "~/types/api";

export const mockPrivacyNoticeTranslation = (
  params?: Partial<PrivacyNoticeTranslation>,
): PrivacyNoticeTranslation => {
  const translation: PrivacyNoticeTranslation = {
    language: "en",
    title: "Mock Advertising",
    description: "A mock sample privacy notice configuration",
    privacy_notice_history_id: "pri_notice-history-mock-advertising-en-000",
  };
  return { ...translation, ...params };
};

/**
 * Mocks the privacy notice, optionally pass in custom translations that override the default translation
 */
export const mockPrivacyNotice = (
  params: Partial<PrivacyNotice> & { title: string; id: string },
  translations?: PrivacyNoticeTranslation[],
): PrivacyNotice => {
  const { title, id } = params;
  const defaultTranslations = [mockPrivacyNoticeTranslation({ title })];
  const notice = {
    name: title,
    consent_mechanism: ConsentMechanism.OPT_OUT,
    default_preference: UserConsentPreference.OPT_IN,
    has_gpc_flag: true,
    disabled: false,
    data_uses: ["advertising", "third_party_sharing"],
    enforcement_level: EnforcementLevel.SYSTEM_WIDE,
    id,
    created_at: "2024-01-01T12:00:00.000000+00:00",
    updated_at: "2024-01-01T12:00:00.000000+00:00",
    notice_key: "advertising",
    cookies: [],
    translations: translations || defaultTranslations,
  };
  return { ...notice, ...params };
};

export const mockCookie = (params: Partial<FidesCookie>) => {
  const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
  const CREATED_DATE = "2024-01-01T12:00:00.000Z";
  const UPDATED_DATE = "2024-01-01T12:00:00.000Z";
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
  params: Partial<TCFVendorConsentRecord | TCFVendorLegitimateInterestsRecord>,
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
