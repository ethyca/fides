/* eslint-disable object-shorthand */
import type { Locale, Messages } from "../../../i18n";
/**
 * Statically load the default (English) TCF-specific locale dictionary.
 *
 * Other locale translations are provided dynamically by the experience API at
 * runtime. Only English is bundled as a fallback to keep the bundle size small.
 */
import en from "./en/messages-tcf.json";

export const STATIC_MESSAGES_TCF: Partial<Record<Locale, Messages>> = {
  en: en,
};
