import { PrivacyExperience } from "../consent-types";
import { TcfModelType } from "./types";

export const TCF_COOKIE_KEY_TO_EXPERIENCE_KEY: {
  cookieKey: TcfModelType;
  experienceKey: keyof Pick<
    PrivacyExperience,
    | "tcf_purposes"
    | "tcf_special_purposes"
    | "tcf_features"
    | "tcf_special_features"
    | "tcf_vendors"
    | "tcf_systems"
  >;
}[] = [
  { cookieKey: "purpose_preferences", experienceKey: "tcf_purposes" },
  {
    cookieKey: "special_purpose_preferences",
    experienceKey: "tcf_special_purposes",
  },
  { cookieKey: "feature_preferences", experienceKey: "tcf_features" },
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
