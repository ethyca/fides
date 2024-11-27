import {
  FidesExperienceTranslationOverrides,
  FidesInitOptionsOverrides,
  FidesOptions,
  OverrideExperienceTranslations,
} from "./consent-types";
import { LOCALE_REGEX } from "./i18n/i18n-constants";

/**
 * Regex to validate a [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2) code:
 * 1. Starts with a 2 letter country code (e.g. "US", "GB") (see [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2))
 * 2. (Optional) Ends with a 1-3 alphanumeric character region code (e.g. "CA", "123", "X") (see [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2))
 * 3. Country & region codes must be separated by a hyphen (e.g. "US-CA")
 *
 * Fides also supports a special `EEA` geolocation code to denote the European
 * Economic Area; this is not part of ISO 3166-2, but is supported for
 * convenience.
 */
export const VALID_ISO_3166_LOCATION_REGEX =
  /^(?:([a-z]{2})(-[a-z0-9]{1,3})?|(eea))$/i;

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
    overrideName: "fidesDisableNoticesServedApi",
    overrideType: "boolean",
    overrideKey: "fides_disable_notices_served_api",
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
  {
    overrideName: "fidesClearCookie",
    overrideType: "string",
    overrideKey: "fides_clear_cookie",
    validationRegex: /(.*)/,
  },
  {
    overrideName: "fidesKnownPreference",
    overrideType: "string",
    overrideKey: "fides_known_preference",
    validationRegex: /^(accept|reject)$/,
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

export const FIDES_OVERLAY_WRAPPER = "fides-overlay-wrapper";
export const FIDES_I18N_ICON = "fides-i18n-icon";

export const MARKETING_CONSENT_KEYS = [
  "marketing",
  "data_sales_and_sharing",
  "data_sales_sharing_gpp_us_state",
  "data_sharing_gpp_us_state",
  "data_sales_gpp_us_state",
  "targeted_advertising_gpp_us_state",
  "sales_sharing_targeted_advertising_gpp_us_national",
];
