import { setupI18n } from "./setupI18n";

/**
 * Declare some generic i18n types that should be compatible with most i18n
 * libraries. These are specifically modelled after LinguiJS, though!
 *
 * (see https://lingui.dev/ref/core#i18n)
 */

// Basic definition of a Locale string (e.g. "en" or "en-GB")
type Locale = string;

/**
 * Basic definition of a i18n messages dictionary. This works for a simple example like:
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
 * Minimum interface required for the global "i18n" object
 */
interface I18n {
  /**
   * "Activate" the user's chosen locale, which should cause future calls to
   * t(...) to return strings localized in the chosen locale
   */
  activate(locale: Locale): void;

  /**
   * "Load" a message dictionary for a particular locale. This can be either a
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
 * 1) import { i18n } from "@lingui/core"
 * 2) Delete the call to setupI18n()
 * 3) Delete our setupI18n.ts file entirely!
 */

const i18n: I18n = setupI18n();

export { type Locale, type Messages, type MessageDescriptor, type I18n };

export { i18n, setupI18n };
