import {
  FidesExperienceTranslationOverrides,
  FidesInitOptionsOverrides,
  OverrideExperienceTranslations,
  FidesOptions,
} from "./consent-types";
import { LOCALE_REGEX } from "./i18n/i18n-constants";

// Regex to validate a location string, which must:
// 1) Start with a 2-3 character country code (e.g. "US")
// 2) Optionally end with a 2-3 character region code (e.g. "CA")
// 3) Separated by a dash (e.g. "US-CA")
export const VALID_ISO_3166_LOCATION_REGEX = /^\w{2,3}(-\w{2,3})?$/;

/**
 * Define the mapping of a FidesOption (e.g. "fides_locale") to a
 * FidesInitOption (e.g. "fidesLocale"). This allows runtime options to be
 * provided by customers just-in-time for the `Fides.init()` call and override
 * default FidesInitOptions, etc.
 */
export const FIDES_OVERRIDE_OPTIONS_VALIDATOR_MAP: {
  overrideName: keyof FidesInitOptionsOverrides;
  overrideType: "string" | "boolean";
  overrideKey: keyof FidesOptions;
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
    overrideName: "fidesPrimaryColor",
    overrideType: "string",
    overrideKey: "fides_primary_color",
    validationRegex: /(.*)/,
  },
];

/**
 * Allows various user-provided experience lang overrides to be validated and mapped to the appropriate Fides variable.
 * overrideName is Fides internal, but overrideKey is the key the user uses to override the option.
 */
export const FIDES_OVERRIDE_EXPERIENCE_LANGUAGE_VALIDATOR_MAP: {
  overrideName: keyof FidesExperienceTranslationOverrides;
  overrideType: "string";
  overrideKey: keyof OverrideExperienceTranslations;
  validationRegex: RegExp;
}[] = [
  {
    overrideName: "title",
    overrideType: "string",
    overrideKey: "fides_title",
    validationRegex: /(.*)/,
  },
  {
    overrideName: "description",
    overrideType: "string",
    overrideKey: "fides_description",
    validationRegex: /(.*)/,
  },
  {
    overrideName: "privacy_policy_url",
    overrideType: "string",
    overrideKey: "fides_privacy_policy_url",
    validationRegex: /(.*)/,
  },
  {
    overrideName: "override_language",
    overrideType: "string",
    overrideKey: "fides_override_language",
    validationRegex: LOCALE_REGEX,
  },
];

export const FIDES_A11Y_CONSTANTS = {
  FIDES_BUTTON_GROUP_ID: "fides-button-group",
};
