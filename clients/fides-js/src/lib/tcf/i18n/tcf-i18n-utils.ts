/**
 * TCF-specific i18n utility functions. These are isolated to a separate file so
 * that Rollup can easily remove this code from the base fides.js bundle without
 * having to do any particularly difficult tree-shaking!
 */
import type { I18n, Locale, Messages, MessageDescriptor } from "../../i18n";
import { STATIC_MESSAGES_TCF } from "./locales";

/**
 * Load the TCF-specific statically-compiled messages from source into the
 * message catalog. See loadMessagesFromFiles in lib/i18n/i18n-utils.ts for the
 * identical implementation for the base bundle.
 */
export function loadTcfMessagesFromFiles(i18n: I18n): Locale[] {
  Object.keys(STATIC_MESSAGES_TCF).forEach((locale) => {
    i18n.load(locale, STATIC_MESSAGES_TCF[locale]);
  });
  return Object.keys(STATIC_MESSAGES_TCF);
}
