import { TcfExperienceRecords, TcfModelType } from "./types";

export const TCF_COOKIE_KEY_TO_EXPERIENCE_KEY: {
  cookieKey: TcfModelType;
  experienceKey: keyof TcfExperienceRecords;
}[] = [
  {
    cookieKey: "purpose_consent_preferences",
    experienceKey: "tcf_consent_purposes",
  },
  {
    cookieKey: "purpose_legitimate_interests_preferences",
    experienceKey: "tcf_legitimate_interests_purposes",
  },
  {
    cookieKey: "special_feature_preferences",
    experienceKey: "tcf_special_features",
  },
  {
    cookieKey: "vendor_consent_preferences",
    experienceKey: "tcf_consent_vendors",
  },
  {
    cookieKey: "vendor_legitimate_interests_preferences",
    experienceKey: "tcf_legitimate_interests_vendors",
  },
  {
    cookieKey: "system_consent_preferences",
    experienceKey: "tcf_consent_systems",
  },
  {
    cookieKey: "system_legitimate_interests_preferences",
    experienceKey: "tcf_legitimate_interests_systems",
  },
];

// Just the experience keys where a user can make a choice (none of the notice-only ones)
export const EXPERIENCE_KEYS_WITH_PREFERENCES =
  TCF_COOKIE_KEY_TO_EXPERIENCE_KEY.filter(
    ({ experienceKey }) =>
      experienceKey !== "tcf_features" &&
      experienceKey !== "tcf_special_purposes"
  ).map((key) => key.experienceKey);
