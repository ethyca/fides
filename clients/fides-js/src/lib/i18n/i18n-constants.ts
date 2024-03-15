import type { Locale } from "./index";

/**
 * Default locale to fallback to is always English ("en")
 */
export const DEFAULT_LOCALE: Locale = "en";

/**
 * General-purpose regex used to validate a locale, as defined in RFC-5646
 * (see https://datatracker.ietf.org/doc/html/rfc5646)
 *
 * For our purposes we parse locales that are simple {language}-{region} codes like:
 *   "en-GB",
 *   "fr",
 *   "es-ES",
 *   "es-419",
 *
 * We also handle other codes like "zh-Hans-HK", but fallback to only capturing
 * the 2-3 letter language code in these variants instead of attempting to parse
 * out all the various combinations of languages, scripts, regions, variants...
 */
export const LOCALE_REGEX =
  /^([A-Za-z]{2,3})(?:(?:[_-]([A-Za-z0-9]{2,4}))?$|(?:(?:[_-]\w+)+))/;
//  ^^^language^^^^   ^^^^^^^^^^region^^^^^^^^^^^^ ^^^^^^other^^^^^^
