import { TcfExperienceRecords, TcfModelType } from "./types";

export const FIDES_SEPARATOR = ",";

export const TCF_COOKIE_KEY_TO_EXPERIENCE_KEY: {
  cookieKey: TcfModelType;
  experienceKey: keyof TcfExperienceRecords;
}[] = [
  {
    cookieKey: "purpose_consent_preferences",
    experienceKey: "tcf_purpose_consents",
  },
  {
    cookieKey: "purpose_legitimate_interests_preferences",
    experienceKey: "tcf_purpose_legitimate_interests",
  },
  {
    cookieKey: "special_feature_preferences",
    experienceKey: "tcf_special_features",
  },
  {
    cookieKey: "vendor_consent_preferences",
    experienceKey: "tcf_vendor_consents",
  },
  {
    cookieKey: "vendor_legitimate_interests_preferences",
    experienceKey: "tcf_vendor_legitimate_interests",
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
export const EXPERIENCE_KEYS_WITH_PREFERENCES =
  TCF_COOKIE_KEY_TO_EXPERIENCE_KEY.filter(
    ({ experienceKey }) =>
      experienceKey !== "tcf_features" &&
      experienceKey !== "tcf_special_purposes"
  ).map((key) => key.experienceKey);
