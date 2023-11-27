import { TCModel } from "@iabtechlabtcf/core";
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
  cookieKey: TcfModelType;
  experienceKey: keyof TcfExperienceRecords;
  tcfModelKey?: keyof TCModel;
  enabledIdsKey?: keyof EnabledIds;
}[] = [
  {
    cookieKey: "purpose_consent_preferences",
    experienceKey: "tcf_purpose_consents",
    tcfModelKey: "purposeConsents",
    enabledIdsKey: "purposesConsent",
  },
  {
    cookieKey: "purpose_legitimate_interests_preferences",
    experienceKey: "tcf_purpose_legitimate_interests",
    tcfModelKey: "purposeLegitimateInterests",
    enabledIdsKey: "purposesLegint",
  },
  {
    cookieKey: "special_feature_preferences",
    experienceKey: "tcf_special_features",
    tcfModelKey: "specialFeatureOptins",
    enabledIdsKey: "specialFeatures",
  },
  {
    cookieKey: "vendor_consent_preferences",
    experienceKey: "tcf_vendor_consents",
    tcfModelKey: "vendorConsents",
    enabledIdsKey: "vendorsConsent",
  },
  {
    cookieKey: "vendor_legitimate_interests_preferences",
    experienceKey: "tcf_vendor_legitimate_interests",
    tcfModelKey: "vendorLegitimateInterests",
    enabledIdsKey: "vendorsLegint",
  },
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
