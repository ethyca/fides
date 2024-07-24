import { setupI18n } from "./i18n-utils";

/**
 * Declare some generic i18n types that should be compatible with most i18n
 * libraries. These are specifically modelled after LinguiJS, though!
 *
 * (see https://lingui.dev/ref/core#i18n)
 */

// Basic definition of a Locale string (e.g. "en" or "en-GB")
type Locale = string;

/**
 * Basic definition of a i18n messages catalog. This works for a simple example like:
 * ```
 * {
 *   "en": {
 *     "experience.title": "Your Privacy Choices",
 *     "experience.accept_button_label": "Accept",
 *   },
 *   "fr": {
 *     "experience.title": "Vos choix en matière de confidentialité",
 *     "experience.accept_button_label": "Accepter",
 *   }
 * }
 * ```
 */
type Messages = Record<string, string>;

/**
 * Basic definition of a message descriptor, to be used by a translation helper
 * function to use when localizing strings, like:
 * ```
 * i18n.t({ id: "experience.title"}); // returns "Your Privacy Choices"
 * i18n.activate("fr");
 * i18n.t({ id: "experience.title"}); // returns "Vos choix en matière de confidentialité",
 * ```
 *
 * Note that a *real* i18n lib would also support providing dynamic values for
 * interpolation, but we're not doing that here - yet! For example:
 * ```
 * i18n.t({ id: "experience.greeting", values: { "username": "Sally" }}); // returns "Hello, Sally!"
 * ```
 */
type MessageDescriptor = {
  id: string;
};

/**
 * A simple type for a list of languages that can be used to populate a
 * language selector dropdown, for example.
 */
type Language = { locale: string; label_en: string; label_original: string };

/**
 * Minimum interface required for the global "i18n" object
 */
interface I18n {
  /**
   * "Activate" the user's chosen locale, which should cause future calls to
   * t(...) to return strings localized in the chosen locale
   */
  activate(locale: Locale): void;

  /**
   * Set the list of available languages for this session.
   */
  setAvailableLanguages(languages: Language[]): void;

  /**
   * Get the list of available languages for the user to choose from.
   */
  get availableLanguages(): Language[];

  /**
   * Get the current default locale for this session.
   *
   * WARN: LinguiJS does not support getting/setting the default locale, so
   * use this sparingly!
   */
  getDefaultLocale(): Locale;

  /**
   * Set the current default locale for this session.
   *
   * WARN: This does not affect the behaviour of t(), load(), or activate()!
   * To change the active locale and get different translations, use
   * activate(). This method should only be used to determine what a
   * "fallback" locale should be for the current user's session if the active
   * locale cannot be used.
   *
   * WARN: LinguiJS does not support getting/setting the default locale, so
   * use this sparingly!
   */
  setDefaultLocale(locale: Locale): void;

  /**
   * Get the currently active locale.
   */
  get locale(): Locale;

  /**
   * "Load" a message catalog for a particular locale. This can be either a
   * static object (e.g. "lib/i18n/locales/en/messages.js") or a dynamic
   * object received at runtime from an API.
   */
  load(locale: Locale, messages: Messages): void;

  /**
   * Lookup the localized string by id from the current locale.
   */
  t(id: string): string;

  /**
   * Lookup the localized string using a message descriptor with an "id"
   * property from the current locale.
   */
  t(descriptor: MessageDescriptor): string;
}

/**
 * Initialize a global i18n singleton for use in the application.
 *
 * DEFER: Swap this implementation for LinguiJS when ready by:
 * 1) Install dependencies: npm install --save @lingui/core && npm install --save-dev @rollup/plugin-replace
 * 2) Configure @rollup/plugin-replace in rollup.config.mjs with:
 *    replace({
 *      "process.env.NODE_ENV": JSON.stringify("production"),
 *      preventAssignment: true,
 *    }),
 * 3) In i8n/index.ts, replace the setupI18n import with: import { setupI18n } from "@lingui/core"
 * 4) Delete our implementation of "setupI18n" in i18n-utils.ts
 *
 * See draft PR for reference: https://github.com/ethyca/fides/pull/4599
 */

const i18n: I18n = setupI18n();

export {
  type I18n,
  type Language,
  type Locale,
  type MessageDescriptor,
  type Messages,
};

export { i18n };
export * from "./i18n-constants";
export * from "./i18n-utils";
