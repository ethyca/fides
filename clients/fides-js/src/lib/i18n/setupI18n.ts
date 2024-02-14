import type { I18n, Locale, Messages, MessageDescriptor } from "./index";

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
