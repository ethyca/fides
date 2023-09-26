import { TcfExperienceRecords, TcfModelType } from "./types";

export const TCF_COOKIE_KEY_TO_EXPERIENCE_KEY: {
  cookieKey: TcfModelType;
  experienceKey: keyof TcfExperienceRecords;
}[] = [
  { cookieKey: "purpose_preferences", experienceKey: "tcf_purposes" },
  {
    cookieKey: "special_feature_preferences",
    experienceKey: "tcf_special_features",
  },
  {
    cookieKey: "vendor_preferences",
    experienceKey: "tcf_vendors",
  },
  {
    cookieKey: "system_preferences",
    experienceKey: "tcf_systems",
  },
];
