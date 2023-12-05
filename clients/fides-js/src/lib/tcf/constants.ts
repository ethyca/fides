import {
  EnabledIds,
  LegalBasisEnum,
  TcfExperienceRecords,
  TcfModelType,
} from "./types";

/** CMP ID assigned to us by the IAB */
export const ETHYCA_CMP_ID = 407;

/**
 * We store all of our preference strings (TC, AC, etc.) together as one string so that
 * we can have a single-source-of-truth for offline storage & syncing. The code responsible
 * for serving our standards-compliant JS API is responsible for separating out the
 * preference strings for consumption.
 */
export const FIDES_SEPARATOR = ",";

export const TCF_KEY_MAP: {
  experienceKey: keyof TcfExperienceRecords;
  tcfModelKey:
    | "purposeConsents"
    | "purposeLegitimateInterests"
    | "specialFeatureOptins"
    | "vendorConsents"
    | "vendorLegitimateInterests";
  enabledIdsKey: keyof EnabledIds;
}[] = [
  {
    experienceKey: "tcf_purpose_consents",
    tcfModelKey: "purposeConsents",
    enabledIdsKey: "purposesConsent",
  },
  {
    experienceKey: "tcf_purpose_legitimate_interests",
    tcfModelKey: "purposeLegitimateInterests",
    enabledIdsKey: "purposesLegint",
  },
  {
    experienceKey: "tcf_special_features",
    tcfModelKey: "specialFeatureOptins",
    enabledIdsKey: "specialFeatures",
  },
  {
    experienceKey: "tcf_vendor_consents",
    tcfModelKey: "vendorConsents",
    enabledIdsKey: "vendorsConsent",
  },
  {
    experienceKey: "tcf_vendor_legitimate_interests",
    tcfModelKey: "vendorLegitimateInterests",
    enabledIdsKey: "vendorsLegint",
  },
];

// These preferences are stored in the cooke on `tcf_consent` instead of `fides_string` because they
// pertain to Fides Systems instead of vendors on the FidesString.
export const FIDES_SYSTEM_COOKIE_KEY_MAP: {
  cookieKey: TcfModelType;
  experienceKey: keyof TcfExperienceRecords;
}[] = [
  {
    cookieKey: "system_consent_preferences",
    experienceKey: "tcf_system_consents",
  },
  {
    cookieKey: "system_legitimate_interests_preferences",
    experienceKey: "tcf_system_legitimate_interests",
  },
];

// Just the experience keys where a user can make a choice (none of the notice-only ones)
export const EXPERIENCE_KEYS_WITH_PREFERENCES = TCF_KEY_MAP.filter(
  ({ experienceKey }) =>
    experienceKey !== "tcf_features" && experienceKey !== "tcf_special_purposes"
).map((key) => key.experienceKey);

export const LEGAL_BASIS_OPTIONS = [
  { label: "Consent", value: LegalBasisEnum.CONSENT },
  { label: "Legitimate interest", value: LegalBasisEnum.LEGITIMATE_INTERESTS },
];
