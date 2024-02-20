import { FidesOptions, PrivacyExperience } from "../consent-types";
import type { I18n, Locale, Messages, MessageDescriptor } from "./index";

/**
 * General-purpose regex used to validate a locale, as defined in RFC-5646
 * (see https://datatracker.ietf.org/doc/html/rfc5646)
 * 
 * For our purposes we only handle locales that are simple {language}-{region} codes like:
 *   "en-GB",
 *   "fr",
 *   "es-ES"
 * 
 * In theory there are much more complex locales available, and we'll always end
 * up falling back to the parent language prefix.
 */
export const SIMPLIFIED_LOCALE_REGEX = /^([A-Za-z]{2,3})(?:[_-]([A-Za-z]{2,3}))?$/

/**
 * Statically load all the pre-localized dictionaries from the ./locales directory.
 * 
 * NOTE: This process isn't automatic. To add a new static locale, follow these steps:
 * 1) Update the STATIC_LOCALE_FILES const with the locale
 * 2) Add the static import of the new ./locales/{locale}/messages.json file
 * 3) Add the locale to the updateMessagesFromFiles() function below
 */
export const STATIC_LOCALE_FILES = ["en", "fr"];
import messagesEn from "./locales/en/messages.json";
import messagesFr from "./locales/fr/messages.json";

/**
 * Initialize the given i18n singleton by:
 * 1) Loading all static messages from locale files
 * 2) Detecting the user's locale
 * 3) Activating the best match for the user's locale
 */
export function initializeI18n(i18n: I18n, navigator: Partial<Navigator>, options?: Partial<FidesOptions>): void {
  updateMessagesFromFiles(i18n);
  i18n.activate("en");
}

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
export function updateMessagesFromExperience(i18n: I18n, experience: PrivacyExperience): void {
  console.warn("updateMessagesFromExperience not implemented!");
}

/**
 * Detect the user's preferred locale from the browser or any overrides.
 */
export function detectUserLocale(navigator: Partial<Navigator>, options?: Partial<FidesOptions>): Locale {
  return "en";
}

/**
 * Match the user's preferred locale to the best match from the given locales.
 */
export function matchAvailableLocales(requestedLocale: Locale, availableLocales: Locale[]): Locale {
  return availableLocales[0];
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
  let currentLocale: Locale = "en";

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
