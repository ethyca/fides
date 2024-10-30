import {
  ComponentType,
  ExperienceConfig,
  ExperienceConfigMinimal,
  ExperienceConfigTranslation,
  FidesExperienceTranslationOverrides,
  FidesInitOptions,
  PrivacyExperience,
  PrivacyExperienceMinimal,
  PrivacyNotice,
  PrivacyNoticeTranslation,
} from "../consent-types";
import { GVLTranslations } from "../tcf/types";
import {
  DEFAULT_LOCALE,
  DEFAULT_MODAL_LINK_LABEL,
  LOCALE_REGEX,
} from "./i18n-constants";
import type {
  I18n,
  Language,
  Locale,
  MessageDescriptor,
  Messages,
} from "./index";
import { LOCALE_LANGUAGE_MAP, STATIC_MESSAGES } from "./locales";

/**
 * Performs an equality comparison between two locales.
 *
 * Returns true if the two locale strings are:
 * 1) an exact string match: areLocalesEqual("en-US", "en-US") === true
 * 2) string match, different case: areLocalesEqual("en-US", "EN-us") === true
 * 3) string match, either '_' or '-' separator: areLocalesEqual("en-US", "EN_us") === true
 *
 * Returns false otherwise.
 */
export function areLocalesEqual(a: Locale, b: Locale): boolean {
  return (
    a.toLowerCase().replaceAll("_", "-") ===
    b.toLowerCase().replaceAll("_", "-")
  );
}

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
  experienceConfig: ExperienceConfig | ExperienceConfigMinimal,
  experienceTranslationOverrides?: Partial<FidesExperienceTranslationOverrides>,
): Record<Locale, Messages> {
  const extracted: Record<Locale, Messages> = {};
  const EXPERIENCE_TRANSLATION_FIELDS = [
    "accept_button_label",
    "acknowledge_button_label",
    "banner_description",
    "banner_title",
    "description",
    "purpose_header",
    "privacy_policy_link_label",
    "privacy_policy_url",
    "privacy_preferences_link_label",
    "reject_button_label",
    "save_button_label",
    "title",
    "modal_link_label",
  ] as const;
  if (experienceConfig.translations) {
    experienceConfig.translations.forEach(
      // For each translation, extract each of the translated fields
      (translation: ExperienceConfigTranslation) => {
        const locale = translation.language;
        // We only override experience translations if the override_language matches current locale
        let localeHasOverride = false;
        if (experienceTranslationOverrides?.override_language) {
          // If translation overrides exist for this language, we will need to apply them below
          localeHasOverride = areLocalesEqual(
            experienceTranslationOverrides.override_language,
            locale,
          );
        }
        const messages: Messages = {};
        EXPERIENCE_TRANSLATION_FIELDS.forEach((key) => {
          let overrideValue: string | null | undefined = null;
          if (experienceTranslationOverrides && localeHasOverride) {
            overrideValue =
              key in experienceTranslationOverrides
                ? experienceTranslationOverrides[
                    key as keyof FidesExperienceTranslationOverrides
                  ]
                : null;
          }
          const message = translation[key];
          if (typeof message === "string") {
            messages[`exp.${key}`] = overrideValue || message;
          }
        });

        // Combine these extracted messages with all the other locales
        extracted[locale] = { ...messages, ...extracted[locale] };
      },
    );
  } else {
    // For backwards-compatibility, when "translations" doesn't exist, default to the "en" locale
    const locale = DEFAULT_LOCALE;
    const messages: Messages = {};
    EXPERIENCE_TRANSLATION_FIELDS.forEach((key) => {
      // @ts-expect-error EXPERIENCE_TRANSLATION_FIELDS is a const array
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
 * Helper function to extract the default locale from a PrivacyExperience API
 * response. Returns the first experience_config.translations' locale where the
 * translation has is_default === true.
 */
// eslint-disable-next-line consistent-return
export function extractDefaultLocaleFromExperience(
  experience: Partial<PrivacyExperience>,
): Locale | undefined {
  if (experience?.experience_config?.translations) {
    const { translations } = experience.experience_config;
    const defaultTranslation = translations.find(
      (translation) => translation.is_default,
    );
    return defaultTranslation?.language;
  }
}

/**
 * Helper function to extract all the translated messages from the GVL translations
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
  gvlTranslations: GVLTranslations,
  locales: Locale[],
): Record<Locale, Messages> {
  // Extract translations, but only those that match the given "locales" list;
  // this avoids loading translations that will be unused when the experience
  // itself is not available in most languages
  const extracted: Record<Locale, Messages> = {};
  locales.forEach((locale) => {
    // Lookup the locale in the GVL using a case-insensitive match
    const gvlLocaleMatch = Object.keys(gvlTranslations).find((gvlLocale) =>
      areLocalesEqual(gvlLocale, locale),
    );
    if (gvlLocaleMatch) {
      const gvlTranslation = gvlTranslations[gvlLocaleMatch] as any;
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

      // Combine these extracted messages with all the other messages
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
 * into the message catalog.
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
  experience: Partial<PrivacyExperience | PrivacyExperienceMinimal>,
  experienceTranslationOverrides?: Partial<FidesExperienceTranslationOverrides>,
) {
  const allMessages: Record<Locale, Messages> = {};
  const availableLocales: Locale[] = experience.available_locales?.length
    ? experience.available_locales
    : [DEFAULT_LOCALE];

  // Extract messages from experience_config.translations
  if (experience?.experience_config) {
    const config = experience.experience_config;
    const extracted: Record<Locale, Messages> =
      extractMessagesFromExperienceConfig(
        config,
        experienceTranslationOverrides,
      );
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
}

/**
 *
 */
export function loadGVLMessagesFromExperience(
  i18n: I18n,
  experience: Partial<PrivacyExperience>,
) {
  if (!experience.gvl) {
    return;
  }
  const { locale } = i18n;
  const gvlTranslations: GVLTranslations = {};
  gvlTranslations[locale] = experience.gvl;
  const extracted: Record<Locale, Messages> =
    extractMessagesFromGVLTranslations(gvlTranslations, [locale]);
  i18n.load(locale, extracted[locale]);
}

/**
 * Parse the provided GVLTranslations object and load all translated strings
 * into the message catalog.
 */
export function loadMessagesFromGVLTranslations(
  i18n: I18n,
  gvlTranslations: GVLTranslations,
  locales: Locale[],
) {
  const extracted: Record<Locale, Messages> =
    extractMessagesFromGVLTranslations(gvlTranslations, locales);
  locales.forEach((locale) => {
    i18n.load(locale, extracted[locale]);
  });
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
  fidesLocaleOverride?: string | undefined,
  defaultLocale: Locale = DEFAULT_LOCALE,
): Locale {
  const browserLocale = navigator?.language;
  return fidesLocaleOverride || browserLocale || defaultLocale;
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
  availableLocales: Locale[],
  defaultLocale: Locale = DEFAULT_LOCALE,
): Locale {
  // 1) Parse the requested locale string using our regex
  const match = requestedLocale.match(LOCALE_REGEX);
  if (match) {
    const [locale, language] = match;

    // 2) Look for an exact match of the requested locale
    const exactMatch = availableLocales.find((elem) =>
      areLocalesEqual(elem, locale),
    );
    if (exactMatch) {
      return exactMatch;
    }

    // 3) Fallback to the {language} of the requested locale
    const languageMatch = availableLocales.find((elem) =>
      areLocalesEqual(elem, language),
    );
    if (languageMatch) {
      return languageMatch;
    }
  }

  // 4) Fallback to default locale
  return defaultLocale;
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
  notice: PrivacyNotice,
): PrivacyNoticeTranslation | null {
  // Defensive checks
  if (!notice || !notice.translations) {
    return null;
  }

  // 1) Look for an exact match for the current locale
  const currentLocale = getCurrentLocale(i18n);
  const matchTranslation = notice.translations.find((e) =>
    areLocalesEqual(e.language, currentLocale),
  );
  if (matchTranslation) {
    return matchTranslation;
  }

  // 2) Fallback to default locale, if an exact match isn't found
  const defaultTranslation = notice.translations.find((e) =>
    areLocalesEqual(e.language, i18n.getDefaultLocale()),
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
  experienceConfig: Partial<ExperienceConfig>,
): ExperienceConfigTranslation | null {
  // Defensive checks
  if (!experienceConfig || !experienceConfig.translations) {
    return null;
  }

  // 1) Look for an exact match for the current locale
  const currentLocale = getCurrentLocale(i18n);
  const matchTranslation = experienceConfig.translations.find((e) =>
    areLocalesEqual(e.language, currentLocale),
  );
  if (matchTranslation) {
    return matchTranslation;
  }

  // 2) Fallback to default locale, if an exact match isn't found
  const defaultTranslation = experienceConfig.translations.find((e) =>
    areLocalesEqual(e.language, i18n.getDefaultLocale()),
  );
  if (defaultTranslation) {
    return defaultTranslation;
  }

  // 3) Fallback to first translation in the list, if the default locale isn't found
  return experienceConfig.translations[0] || null;
}

/**
 * Initialize the given i18n singleton by:
 * 1) Loading all static messages from locale files
 * 2) Loading all dynamic messages from experience API
 * 3) Setting the default locale based on the experience API
 * 4) Detecting the user's browser locale
 * 5) Activating the best match for the user's locale based on:
 *   a) user's browser locale
 *   b) available locales from the experience API
 *   c) default locale from the experience API
 */
export function initializeI18n(
  i18n: I18n,
  navigator: Partial<Navigator>,
  experience: Partial<PrivacyExperience>,
  options?: Partial<FidesInitOptions>,
  experienceTranslationOverrides?: Partial<FidesExperienceTranslationOverrides>,
): void {
  // Extract & update all the translated messages from both our static files and the experience API
  loadMessagesFromFiles(i18n);
  const availableLocales: Locale[] = experience.available_locales?.length
    ? experience.available_locales
    : [DEFAULT_LOCALE];
  loadMessagesFromExperience(i18n, experience, experienceTranslationOverrides);
  fidesDebugger(
    `Loaded Fides i18n with available locales (${availableLocales.length}) = ${availableLocales}`,
  );

  // Set the list of available languages for the user to choose from
  const availableLanguages = LOCALE_LANGUAGE_MAP.filter((lang) =>
    availableLocales.includes(lang.locale),
  );

  // move default locale first
  const indexOfDefault = availableLanguages.findIndex((lang) =>
    areLocalesEqual(lang.locale, i18n.getDefaultLocale()),
  );
  if (indexOfDefault > 0) {
    availableLanguages.unshift(availableLanguages.splice(indexOfDefault, 1)[0]);
  }
  i18n.setAvailableLanguages(availableLanguages);
  fidesDebugger(
    `Loaded Fides i18n with available languages`,
    availableLanguages,
  );

  // Extract the default locale from the experience API, or fallback to DEFAULT_LOCALE
  const defaultLocale: Locale =
    extractDefaultLocaleFromExperience(experience) || DEFAULT_LOCALE;
  i18n.setDefaultLocale(defaultLocale);
  fidesDebugger(
    `Setting Fides i18n default locale = ${i18n.getDefaultLocale()}`,
  );

  // Detect the user's locale, unless it's been *explicitly* disabled in the experience config
  let userLocale = defaultLocale;
  if (experience.experience_config?.auto_detect_language === false) {
    fidesDebugger("Auto-detection of Fides i18n user locale disabled!");
  } else {
    userLocale = detectUserLocale(
      navigator,
      options?.fidesLocale,
      defaultLocale,
    );
    fidesDebugger(`Detected Fides i18n user locale = ${userLocale}`);
  }

  // Match the user locale to the "best" available locale from the experience API
  const bestLocale = matchAvailableLocales(
    userLocale,
    availableLocales || [],
    i18n.getDefaultLocale(),
  );

  // If best locale's language wasn't returned--but is available from the server
  // (eg. a cached version of the minimal TCF)-- we need to initialize with a language
  // that was returned to later get the best one, as possible (eg. full TCF response).
  // Otherwise, we can simply initialize with the best locale.
  const isBestLocaleInTranslations: boolean =
    !!experience.experience_config?.translations?.find(
      (translation) => translation.language === bestLocale,
    );
  if (!isBestLocaleInTranslations) {
    const bestTranslation = selectBestExperienceConfigTranslation(
      i18n,
      experience.experience_config!,
    );
    const bestAvailableLocale = bestTranslation?.language || bestLocale;
    i18n.activate(bestTranslation?.language || bestLocale);
    fidesDebugger(
      `Initialized Fides i18n with available translations = ${bestAvailableLocale}`,
    );
  } else {
    i18n.activate(bestLocale);
    fidesDebugger(
      `Initialized Fides i18n with best locale match = ${bestLocale}`,
    );
  }

  // Now that we've activated the best locale, load the GVL messages if needed.
  // First load default language messages from the experience's GVL to avoid
  // delay in rendering the overlay. If a translation is needed, it will be
  // loaded in the background.
  if (
    experience.experience_config?.component === ComponentType.TCF_OVERLAY &&
    !!experience.gvl
  ) {
    loadGVLMessagesFromExperience(i18n, experience);
  }
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
  // Available language maps
  let availableLanguages: Language[] = [];

  // Default locale; default this to English
  let defaultLocale: Locale = DEFAULT_LOCALE;

  // Currently active locale; default this to English
  let currentLocale: Locale = DEFAULT_LOCALE;

  // Messages catalog, which stores i18n-ized messages grouped by locale
  const allMessages: Record<Locale, Messages> = {};

  // Return a new I18n instance
  return {
    setAvailableLanguages(languages: Language[]) {
      availableLanguages = languages;
    },

    get availableLanguages() {
      return availableLanguages;
    },

    activate: (locale: Locale): void => {
      currentLocale = locale;
    },

    getDefaultLocale: (): Locale => defaultLocale,

    setDefaultLocale: (locale: Locale): void => {
      defaultLocale = locale;
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

/**
 * Determines the appropriate modal link text based on
 * localization settings and language translations.
 */
export const localizeModalLinkText = (
  disableLocalization: boolean,
  i18n: I18n,
  effectiveExperience?: Partial<PrivacyExperience | PrivacyExperienceMinimal>,
): string => {
  let modalLinkText = DEFAULT_MODAL_LINK_LABEL;
  if (!disableLocalization) {
    if (i18n.t("exp.modal_link_label") !== "exp.modal_link_label") {
      modalLinkText = i18n.t("exp.modal_link_label");
    }
  } else {
    const defaultLocale = i18n.getDefaultLocale();
    const defaultTranslation =
      effectiveExperience?.experience_config?.translations.find(
        (t) => t.language === defaultLocale,
      );
    if (defaultTranslation?.modal_link_label) {
      modalLinkText = defaultTranslation.modal_link_label;
    }
  }
  return modalLinkText;
};
