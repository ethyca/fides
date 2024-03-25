import {
  FidesExperienceTranslationOverrides,
  FidesOptionsOverrides,
  OverrideExperienceTranslations,
  OverrideOptions,
} from "./consent-types";
import { LOCALE_REGEX } from "./i18n/i18n-constants";

// Regex to validate a location string, which must:
// 1) Start with a 2-3 character country code (e.g. "US")
// 2) Optionally end with a 2-3 character region code (e.g. "CA")
// 3) Separated by a dash (e.g. "US-CA")
export const VALID_ISO_3166_LOCATION_REGEX = /^\w{2,3}(-\w{2,3})?$/;

export const DEFAULT_OVERLAY_PRIMARY_COLOR = "#8243f2";

export const FIDES_OVERRIDE_OPTIONS_VALIDATOR_MAP: {
  overrideName: keyof FidesOptionsOverrides;
  overrideType: "string" | "boolean";
  overrideKey: keyof OverrideOptions;
  validationRegex: RegExp;
}[] = [
  {
    overrideName: "fidesEmbed",
    overrideType: "boolean",
    overrideKey: "fides_embed",
    validationRegex: /^(true|false)$/,
  },
  {
    overrideName: "fidesDisableSaveApi",
    overrideType: "boolean",
    overrideKey: "fides_disable_save_api",
    validationRegex: /^(true|false)$/,
  },
  {
    overrideName: "fidesDisableBanner",
    overrideType: "boolean",
    overrideKey: "fides_disable_banner",
    validationRegex: /^(true|false)$/,
  },
  {
    overrideName: "fidesString",
    overrideType: "string",
    overrideKey: "fides_string",
    validationRegex: /(.*)/,
  },
  {
    overrideName: "fidesTcfGdprApplies",
    overrideType: "boolean",
    overrideKey: "fides_tcf_gdpr_applies",
    validationRegex: /^(true|false)$/,
  },
  {
    overrideName: "fidesLocale",
    overrideType: "string",
    overrideKey: "fides_locale",
    validationRegex: LOCALE_REGEX,
  },
  {
    overrideName: "overlayPrimaryColor",
    overrideType: "string",
    overrideKey: "primary_color",
    validationRegex: /(.*)/,
  },
];

export const FIDES_OVERRIDE_LANGUAGE_VALIDATOR_MAP: {
  overrideName: keyof FidesExperienceTranslationOverrides;
  overrideType: "string" | "boolean";
  overrideKey: keyof OverrideExperienceTranslations;
  validationRegex: RegExp;
}[] = [
  {
    overrideName: "title",
    overrideType: "string",
    overrideKey: "title",
    validationRegex: /(.*)/,
  },
  {
    overrideName: "description",
    overrideType: "string",
    overrideKey: "description",
    validationRegex: /(.*)/,
  },
  {
    overrideName: "privacy_policy_link_url",
    overrideType: "string",
    overrideKey: "privacy_policy_link_url",
    validationRegex: /(.*)/,
  },
  {
    overrideName: "override_language",
    overrideType: "string",
    overrideKey: "override_language",
    validationRegex: LOCALE_REGEX,
  },
];
