import {
  ExperienceConfig,
  ExperienceConfigTranslation,
  FidesOptions,
  PrivacyExperience,
  PrivacyNotice,
  PrivacyNoticeTranslation,
  PrivacyNoticeWithPreference,
} from "../consent-types";
import { debugLog } from "../consent-utils";
import type { I18n, Locale, Messages, MessageDescriptor } from "./index";
import { DEFAULT_LOCALE, LOCALE_REGEX } from "./i18n-constants";

/**
 * Statically load all the pre-localized dictionaries from the ./locales directory.
 *
 * NOTE: This process isn't automatic. To add a new static locale, follow these steps:
 * 1) Add the static import of the new ./locales/{locale}/messages.json file
 * 2) Add the locale to the loadMessagesFromFiles() function below
 */
import messagesEn from "./locales/en/messages.json";
import messagesEs from "./locales/es/messages.json";
import messagesFr from "./locales/fr/messages.json";

/**
 * Helper function to extract all the translated messages from an
 * ExperienceConfig API response. Returns an object that maps locales -> messages, e.g.
 * {
 *   "en": {
 *     "exp.accept_button_label": "Accept",
 *     "exp.acknowledge_button_label": "OK",
 *     ...
 *   },
 *   "es": {
 *     ...
 *   }
 * }
 */
function extractMessagesFromExperienceConfig(
  experienceConfig: ExperienceConfig
): Record<Locale, Messages> {
  const extracted: Record<Locale, Messages> = {};
  const EXPERIENCE_TRANSLATION_FIELDS = [
    "accept_button_label",
    "acknowledge_button_label",
    "banner_description",
    "banner_title",
    "description",
    "privacy_policy_link_label",
    "privacy_policy_url",
    "privacy_preferences_link_label",
    "reject_button_label",
    "save_button_label",
    "title",
  ] as const;
  if (experienceConfig.translations) {
    experienceConfig.translations.forEach(
      // For each translation, extract each of the translated fields
      (translation: ExperienceConfigTranslation) => {
        const locale = translation.language;
        const messages: Messages = {};
        EXPERIENCE_TRANSLATION_FIELDS.forEach((key) => {
          const message = translation[key];
          if (typeof message === "string") {
            messages[`exp.${key}`] = message;
          }
        });

        // Combine these extracted messages with all the other locales
        extracted[locale] = { ...messages, ...extracted[locale] };
      }
    );
  } else {
    // For backwards-compatibility, when "translations" doesn't exist, look for
    // the fields on the ExperienceConfig itself
    const locale = DEFAULT_LOCALE;
    const messages: Messages = {};
    EXPERIENCE_TRANSLATION_FIELDS.forEach((key) => {
      const message = experienceConfig[key];
      if (typeof message === "string") {
        messages[`exp.${key}`] = message;
      }
    });

    // Combine these extracted messages with all the other locales
    extracted[locale] = { ...messages, ...extracted[locale] };
  }
  return extracted;
}

/**
 * Helper function to extract all the translated messages from a PrivacyNotice
 * API response.  Returns an object that maps locales -> messages, using the
 * PrivacyNotice's id to prefix each message like "exp.notices.{id}.title"
 *
 * For example, returns a message catalog like:
 * {
 *   "en": {
 *     "exp.notices.pri_123.title": "Advertising",
 *     "exp.notices.pri_123.description": "We perform advertising based on...",
 *     ...
 *   },
 *   "es": {
 *     ...
 *   }
 * }
 */
function extractMessagesFromNotice(
  notice: PrivacyNotice
): Record<Locale, Messages> {
  const extracted: Record<Locale, Messages> = {};
  const NOTICE_TRANSLATION_FIELDS = ["description", "title"] as const;
  if (notice?.translations) {
    notice.translations.forEach((translation: PrivacyNoticeTranslation) => {
      // For each translation, extract each of the translated fields
      const locale = translation.language;
      const messages: Messages = {};
      NOTICE_TRANSLATION_FIELDS.forEach((key) => {
        const message = translation[key];
        if (typeof message === "string") {
          messages[`exp.notices.${notice.id}.${key}`] = message;
        }
      });

      // Combine these extracted messages with all the other locales
      extracted[locale] = { ...messages, ...extracted[locale] };
    });
  } else {
    // For backwards-compatibility, when "translations" don't exist, look for
    // the fields on the PrivacyNotice itself
    const anyNotice = notice as any;
    const locale = DEFAULT_LOCALE;
    const messages: Messages = {};
    if (typeof anyNotice.description === "string") {
      messages[`exp.notices.${notice.id}.description`] = anyNotice.description;
    }
    // NOTE: for backwards-compatibility; we used to use "name" for the title :)
    if (typeof anyNotice.name === "string") {
      messages[`exp.notices.${notice.id}.title`] = anyNotice.name;
    }

    // Combine these extracted messages with all the other locales
    extracted[locale] = { ...messages, ...extracted[locale] };
  }
  return extracted;
}

/**
 * Load the statically-compiled messages from source into the message catalog.
 */
export function loadMessagesFromFiles(i18n: I18n): Locale[] {
  // NOTE: This doesn't automatically infer the list of locale files from
  // source, so you'll need to manually add any new locales here!
  i18n.load("en", messagesEn);
  i18n.load("es", messagesEs);
  i18n.load("fr", messagesFr);
  return ["en", "es", "fr"];
}

/**
 * Parse the provided PrivacyExperience object and load all translated strings
 * into the message catalog.
 */
export function loadMessagesFromExperience(
  i18n: I18n,
  experience: Partial<PrivacyExperience>
): Locale[] {
  const allMessages: Record<Locale, Messages> = {};

  // Extract messages from experience_config.translations
  if (experience?.experience_config) {
    const extracted: Record<Locale, Messages> =
      extractMessagesFromExperienceConfig(experience.experience_config);
    Object.keys(extracted).forEach((locale) => {
      allMessages[locale] = {
        ...extracted[locale],
        ...allMessages[locale],
      };
    });
  }

  // Extract messages from privacy_notices[].translations
  if (experience?.privacy_notices) {
    experience.privacy_notices.forEach(
      (notice: PrivacyNoticeWithPreference) => {
        const extracted: Record<Locale, Messages> =
          extractMessagesFromNotice(notice);
        Object.keys(extracted).forEach((locale) => {
          allMessages[locale] = {
            ...extracted[locale],
            ...allMessages[locale],
          };
        });
      }
    );
  }

  // Load all the extracted messages into the i18n module
  const updatedLocales: Locale[] = Object.keys(allMessages);
  updatedLocales.forEach((locale) => {
    i18n.load(locale, allMessages[locale]);
  });

  // Return all the locales we extracted & updated
  return updatedLocales;
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
 * Check if the given message exists in the current locale's catalog.
 */
export function messageExists(i18n: I18n, id: string): boolean {
  // NOTE: Our i18n library mirrors LinguiJS's implementation, which doesn't
  // expose a way to check for missing messages directly. However, it will
  // always return the "id" if no matching message exists, so we rely on that!
  // TODO (PROD-1597): use Lingui's missing message option
  return (i18n.t(id) !== "" && i18n.t(id) !== id);
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
  experience: Partial<PrivacyExperience>,
  options?: Partial<FidesOptions>
): void {
  // Extract & update all the translated messages from both our static files and the experience API
  loadMessagesFromFiles(i18n);
  const availableLocales = loadMessagesFromExperience(i18n, experience);
  debugLog(
    options?.debug,
    `Loaded Fides i18n with available locales = ${availableLocales}`
  );

  // Detect the user's locale, unless it's been *explicitly* disabled in the experience config
  let userLocale = DEFAULT_LOCALE;
  if (experience.experience_config?.auto_detect_language === false) {
    debugLog(
      options?.debug,
      "Auto-detection of Fides i18n user locale disabled!"
    );
  } else {
    userLocale = detectUserLocale(navigator, options);
    debugLog(options?.debug, `Detected Fides i18n user locale = ${userLocale}`);
  }

  // Match the user locale to the "best" available locale from the experience API and activate it!
  const bestLocale = matchAvailableLocales(userLocale, availableLocales);
  i18n.activate(bestLocale);
  debugLog(
    options?.debug,
    `Initialized fides-js i18n with best locale = ${bestLocale}`
  );
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
      allMessages[locale] = { ...messages, ...allMessages[locale] };
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
        // id is invalid; return an empty string
        return "";
      }

      // Lookup the string in our messages catalog by locale & id
      if (
        currentLocale &&
        currentLocale in allMessages &&
        id &&
        id in allMessages[currentLocale] &&
        allMessages[currentLocale][id]
      ) {
        return allMessages[currentLocale][id];
      }

      // No match found, return the id as a fallback
      return id;
    },
  };
}
