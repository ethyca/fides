import { FidesOptionsOverrides, OverrideOptions } from "./consent-types";
import { LOCALE_REGEX } from "./i18n/i18n-constants";

// Regex to validate a location string, which must:
// 1) Start with a 2-3 character country code (e.g. "US")
// 2) Optionally end with a 2-3 character region code (e.g. "CA")
// 3) Separated by a dash (e.g. "US-CA")
export const VALID_ISO_3166_LOCATION_REGEX = /^\w{2,3}(-\w{2,3})?$/;

export const FIDES_OVERRIDE_OPTIONS_VALIDATOR_MAP: {
  fidesOption: keyof FidesOptionsOverrides;
  fidesOptionType: "string" | "boolean";
  fidesOverrideKey: keyof OverrideOptions;
  validationRegex: RegExp;
}[] = [
  {
    fidesOption: "fidesEmbed",
    fidesOptionType: "boolean",
    fidesOverrideKey: "fides_embed",
    validationRegex: /^(true|false)$/,
  },
  {
    fidesOption: "fidesDisableSaveApi",
    fidesOptionType: "boolean",
    fidesOverrideKey: "fides_disable_save_api",
    validationRegex: /^(true|false)$/,
  },
  {
    fidesOption: "fidesDisableBanner",
    fidesOptionType: "boolean",
    fidesOverrideKey: "fides_disable_banner",
    validationRegex: /^(true|false)$/,
  },
  {
    fidesOption: "fidesString",
    fidesOptionType: "string",
    fidesOverrideKey: "fides_string",
    validationRegex: /(.*)/,
  },
  {
    fidesOption: "fidesTcfGdprApplies",
    fidesOptionType: "boolean",
    fidesOverrideKey: "fides_tcf_gdpr_applies",
    validationRegex: /^(true|false)$/,
  },
  {
    fidesOption: "fidesLocale",
    fidesOptionType: "string",
    fidesOverrideKey: "fides_locale",
    validationRegex: LOCALE_REGEX,
  },
];
