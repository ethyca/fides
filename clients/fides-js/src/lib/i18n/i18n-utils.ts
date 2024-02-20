import { FidesOptions, PrivacyExperience } from "../consent-types";
import type { I18n, Locale, Messages, MessageDescriptor } from "./index";

/**
 * Statically load all the pre-localized dictionaries from the ./locales directory.
 *
 * NOTE: This process isn't automatic. To add a new static locale, follow these steps:
 * 1) Add the static import of the new ./locales/{locale}/messages.json file
 * 2) Add the locale to the updateMessagesFromFiles() function below
 */
import messagesEn from "./locales/en/messages.json";
import messagesFr from "./locales/fr/messages.json";

/**
 * Default locale to fallback to is always English ("en")
 */
const DEFAULT_LOCALE: Locale = "en";

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
//                            ^^^language^^^^   ^^^^^^^^^^region^^^^^^^^^^^^ ^^^^^^other^^^^^^

/**
 * Load the statically-compiled messages from source into the message catalog.
 */
export function updateMessagesFromFiles(i18n: I18n): void {
  // NOTE: This doesn't automatically infer
  i18n.load("en", messagesEn);
  i18n.load("fr", messagesFr);
}

/**
 * Parse the provided PrivacyExperience object and load all translated strings
 * into the message catalog.
 */
export function updateMessagesFromExperience(
  i18n: I18n,
  experience: PrivacyExperience
): void {
  console.warn("updateMessagesFromExperience not implemented!");
}

/**
 * Detect the user's preferred locale from the browser or any overrides.
 */
export function detectUserLocale(
  navigator: Partial<Navigator>,
  options?: Partial<FidesOptions>
): Locale {
  const browserLocale = navigator?.language;
  const fidesLocaleOverride = options?.fidesLocale;
  return fidesLocaleOverride || browserLocale || DEFAULT_LOCALE;
}

/**
 * Match the user's preferred locale to the best match from the given locales.
 *
 * NOTE: This might seem trivial but doing it *correctly* is pretty complex.
 * There's a standards-track proposal to define a "Intl.LocaleMatcher" function as
 * part of the core library you can see here:
 * https://github.com/tc39/proposal-intl-localematcher
 *
 * This function follows the basic structure of that LocaleMatcher function (with fewer options) and does the following:
 * 1) Parse the locale string (e.g. "fr-CA" into {language}-{region})
 * 2) Return an exact match for {language}-{region} if possible (e.g. "fr-CA" -> "fr-CA")
 * 3) Fallback to the {language} only if possible (e.g. "fr-CA" -> "fr")
 * 4) Fallback to the default locale otherwise (e.g. "fr-CA" -> "en")
 */
export function matchAvailableLocales(
  requestedLocale: Locale,
  availableLocales: Locale[]
): Locale {
  // 1) Parse the requested locale string using our regex
  const match = requestedLocale.match(LOCALE_REGEX);
  if (match) {
    const [locale, language] = match;

    // 2) Look for an exact match of the requested locale
    const exactMatch = availableLocales.find(
      (elem) =>
        elem.toLowerCase().replaceAll("_", "-") ===
        locale.toLowerCase().replaceAll("_", "-")
    );
    if (exactMatch) {
      return exactMatch;
    }

    // 3) Fallback to the {language} of the requested locale
    const languageMatch = availableLocales.find(
      (elem) =>
        elem.toLowerCase().replaceAll("_", "-") ===
        language.toLowerCase().replaceAll("_", "-")
    );
    if (languageMatch) {
      return languageMatch;
    }
  }

  // 4) Fallback to default locale
  return DEFAULT_LOCALE;
}

/**
 * Initialize the given i18n singleton by:
 * 1) Loading all static messages from locale files
 * 2) Detecting the user's locale
 * 3) Activating the best match for the user's locale
 */
export function initializeI18n(
  i18n: I18n,
  navigator: Partial<Navigator>,
  options?: Partial<FidesOptions>
): void {
  updateMessagesFromFiles(i18n);
  i18n.activate(DEFAULT_LOCALE);
}

/**
 * Factory function that returns a new I18n instance that is the *simplest*
 * possible implementation of an i18n library that meets our minimal
 * requirements as of February 2024.
 *
 * Note that this implementation is designed to be completely swapped out for
 * LinguiJS once we're ready to upgrade to the real thing!
 */
export function setupI18n(): I18n {
  // Currently active locale; default this to English
  let currentLocale: Locale = DEFAULT_LOCALE;

  // Messages catalog, which stores i18n-ized messages grouped by locale
  const allMessages: Record<Locale, Messages> = {};

  // Return a new I18n instance
  return {
    activate: (locale: Locale): void => {
      currentLocale = locale;
    },

    load: (locale: Locale, messages: Messages): void => {
      allMessages[locale] = messages;
    },

    t: (descriptorOrId: MessageDescriptor | string): string => {
      // Validate the input type for safety
      // NOTE: We throw TypeErrors for null/undefined here to match the behaviour of LinguiJS!
      if (typeof descriptorOrId === "undefined") {
        throw new TypeError("Unexpected type for descriptor or id!");
      }

      // Get the message id, either directly or from the descriptor
      let id: string;
      if (typeof descriptorOrId === "string") {
        id = descriptorOrId;
      } else if (typeof descriptorOrId === "object" && descriptorOrId.id) {
        id = descriptorOrId.id;
      } else {
        return "";
      }

      // Lookup the string in our messages catalog by locale & id
      if (
        currentLocale &&
        currentLocale in allMessages &&
        id &&
        id in allMessages[currentLocale]
      ) {
        return allMessages[currentLocale][id];
      }

      // No match found, return the id as a fallback
      return id;
    },
  };
}
