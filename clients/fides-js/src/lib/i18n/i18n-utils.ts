import {
  ExperienceConfig,
  ExperienceConfigTranslation,
  FidesOptions,
  PrivacyExperience,
  PrivacyNotice,
  PrivacyNoticeTranslation,
} from "../consent-types";
import { debugLog } from "../consent-utils";
import type { I18n, Locale, Messages, MessageDescriptor } from "./index";
import { DEFAULT_LOCALE, LOCALE_REGEX } from "./i18n-constants";
import { STATIC_MESSAGES } from "./locales";
import { GVLTranslations } from "../tcf/types";

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
 * Helper function to extract all the translated messages from the "gvl_translations"
 * API response. Returns an object that maps locales -> messages, e.g.
 * {
 *   "en": {
 *     "exp.tcf.purposes.1.name": "Store and/or access information on a device",
 *     "exp.tcf.purposes.1.description": "description": "Cookies, device or similar...",
 *     "exp.tcf.purposes.1.illustrations.0": "Most purposes explained in this...",
 *   },
 *   "es": {
 *     ...
 *   }
 * }
 *
 * This allows convenient access to any translated message from all points in
 * the TCF code by using the well-worn GVL IDs as locators. However, note that
 * the "illustrations" array can be a bit awkward to use as a flattened list of
 * messages - we need to make sure we carefully look up illustrations using
 * their zero-based index (e.g. i18n.t("exp.tcf.purposes.1.illustrations.0")
 */
function extractMessagesFromGVLTranslations(
  gvl_translations: GVLTranslations,
  locales: Locale[]
): Record<Locale, Messages> {
  // Extract translations, but only those that match the given "locales" list;
  // this avoids loading translations that will be unused when the experience
  // itself is not available in most languages
  const extracted: Record<Locale, Messages> = {};
  locales.forEach((locale) => {
    // DEFER (PROD-1811): prefer a case-insensitive locale match
    const gvlTranslation = gvl_translations[locale] as any;
    if (gvlTranslation) {
      const messages: Messages = {};

      const recordTypes = [
        "purposes",
        "specialPurposes",
        "features",
        "specialFeatures",
        "stacks",
        "dataCategories",
      ];
      recordTypes.forEach((type) => {
        const records = gvlTranslation[type] || {};
        Object.keys(records).forEach((id) => {
          const record = records[id];
          const prefix = `exp.tcf.${type}.${id}`;
          messages[`${prefix}.name`] = record.name;
          messages[`${prefix}.description`] = record.description;
          if (record.illustrations && record.illustrations.length > 0) {
            record.illustrations.forEach((illustration: string, i: number) => {
              messages[`${prefix}.illustrations.${i}`] = illustration;
            });
          }
        });
      });

      // Combine these extracted messages with all the other locales
      extracted[locale] = { ...messages, ...extracted[locale] };
    }
  });
  return extracted;
}

/**
 * Load the statically-compiled messages from source into the message catalog.
 */
export function loadMessagesFromFiles(i18n: I18n): Locale[] {
  Object.keys(STATIC_MESSAGES).forEach((locale) => {
    i18n.load(locale, STATIC_MESSAGES[locale]);
  });
  return Object.keys(STATIC_MESSAGES);
}

/**
 * Parse the provided PrivacyExperience object and load all translated strings
 * into the message catalog. Extracts translations from two sources:
 * 1) experience.experience_config
 * 2) experience.gvl_translations
 *
 * Returns a list of locales that exist in *both* these sources, discarding any
 * locales that exist in one but not the other. This is done to encourage only
 * using locales with "full" translation catalogs.
 *
 * NOTE: We don't extract any messages from the PrivacyNotices and their linked
 * translations. This is because notices are dynamic and their list of available
 * translations isn't guaranteed to match the overall experience config; since
 * there's too much uncertainty there, it's best to handle selecting the "best"
 * translation and displaying it within the UI components themselves.
 *
 * See `selectBestNoticeTranslation` below for how that selection is done based
 * on the i18n locale.
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
  let availableLocales: Locale[] = Object.keys(allMessages);

  // Extract messages from gvl_translations, filtering to only locales that
  // exist in experience_config above
  if (experience?.gvl_translations) {
    const extracted: Record<Locale, Messages> =
      extractMessagesFromGVLTranslations(
        experience.gvl_translations,
        availableLocales
      );
    // Filter the locales further to include only those that existed in
    // gvl_translations as well
    availableLocales = Object.keys(extracted);

    // Combine extracted messages with those from experience_config above
    Object.keys(extracted).forEach((locale) => {
      allMessages[locale] = {
        ...extracted[locale],
        ...allMessages[locale],
      };
    });
  }

  // Load all the extracted messages into the i18n module
  availableLocales.forEach((locale) => {
    i18n.load(locale, allMessages[locale]);
  });

  // Return all the locales we extracted & updated
  return availableLocales;
}

/**
 * Get the currently active locale.
 */
export function getCurrentLocale(i18n: I18n): Locale {
  return i18n.locale;
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
  return i18n.t(id) !== "" && i18n.t(id) !== id;
}

/**
 * Helper function to select the "best" translation from a notice, based on the
 * current locale. This searches through the available translations for the
 * given notice and selects the best match in this order:
 * 1) Look for an exact match for current locale
 * 2) Fallback to default locale, if an exact match isn't found
 * 3) Fallback to first translation in the list, if the default locale isn't found
 *
 * NOTE: We use this "best" translation instead of relying directly on
 * the i18n module because we can't guarantee a notice will have a translation
 * that matches the PrivacyExperience - it's completely possible to, for
 * example, configure an experience with Spanish translations but forget to
 * translate all the linked notices!
 *
 * Since we can't provide that guarantee, instead we rely on the UI components
 * (e.g. NoticeOverlay) to pick the "best" translation to show for each notice
 * and handle that state.
 */
export function selectBestNoticeTranslation(
  i18n: I18n,
  notice: PrivacyNotice
): PrivacyNoticeTranslation | null {
  // Defensive checks
  if (!notice || !notice.translations) {
    return null;
  }

  // 1) Look for an exact match for the current locale
  const currentLocale = getCurrentLocale(i18n);
  const matchTranslation = notice.translations.find(
    (e) => e.language === currentLocale
  );
  if (matchTranslation) {
    return matchTranslation;
  }

  // 2) Fallback to default locale, if an exact match isn't found
  const defaultTranslation = notice.translations.find(
    (e) => e.language === DEFAULT_LOCALE
  );
  if (defaultTranslation) {
    return defaultTranslation;
  }

  // 3) Fallback to first translation in the list, if the default locale isn't found
  return notice.translations[0] || null;
}

/**
 * Helper function to select the "best" translation from the given
 * ExperienceConfig, based on the current locale. This is used to ensure that
 * our reporting APIs (notices served & save preferences) are given the right
 * history IDs to use based on which locale is selected by the i18n module.
 *
 * NOTE: Unlike with notices, an "exact match" should occur 99% of the time,
 * since our i18n module selects the current locale from this list of available
 * translations! However, we do need to handle the edge case where our API might
 * miss default English translations in the future...
 */
export function selectBestExperienceConfigTranslation(
  i18n: I18n,
  experience: ExperienceConfig
): ExperienceConfigTranslation | null {
  // Defensive checks
  if (!experience || !experience.translations) {
    return null;
  }

  // 1) Look for an exact match for the current locale
  const currentLocale = getCurrentLocale(i18n);
  const matchTranslation = experience.translations.find(
    (e) => e.language === currentLocale
  );
  if (matchTranslation) {
    return matchTranslation;
  }

  // 2) Fallback to default locale, if an exact match isn't found
  const defaultTranslation = experience.translations.find(
    (e) => e.language === DEFAULT_LOCALE
  );
  if (defaultTranslation) {
    return defaultTranslation;
  }

  // 3) Fallback to first translation in the list, if the default locale isn't found
  return experience.translations[0] || null;
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

    get locale() {
      return currentLocale;
    },

    load: (locale: Locale, messages: Messages): void => {
      allMessages[locale] = { ...allMessages[locale], ...messages };
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
