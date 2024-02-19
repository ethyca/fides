import { FidesOptions, PrivacyExperience } from "../consent-types";
import type { I18n, Locale, Messages, MessageDescriptor } from "./index";
import { i18n } from "./index";

/**
 * Initialize the global i18n object with the statically defined messages from
 * local files.
 */
export function initializeI18n(): void {
  i18n.activate("en");
}

/**
 * Load the statically-compiled messages from source into the message dictionary.
 */
export function updateMessagesFromFiles(): void {
}

/**
 * Parse the provided PrivacyExperience object and load all translated strings
 * into the message dictionary.
 */
export function updateMessagesFromExperience(experience: PrivacyExperience): void {
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

  // Messages dictionary, which stores i18n-ized messages grouped by locale
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

      // Lookup the string in our messages dictionary by locale & id
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
