/* eslint-disable object-shorthand */
import type { Language, Locale, Messages } from "..";
/**
 * Statically load the default (English) locale dictionary from the ./locales directory.
 *
 * Other locale translations are provided dynamically by the experience API at
 * runtime. Only English is bundled as a fallback for static strings (e.g. GPC
 * labels) to keep the bundle size small.
 *
 * NOTE: To add a new static locale to the language selector, add it to the
 * LOCALE_LANGUAGE_MAP below.
 */
import en from "./en/messages.json";

export const STATIC_MESSAGES: Partial<Record<Locale, Messages>> = {
  en: en,
};

export const LOCALE_LANGUAGE_MAP: Language[] = [
  { locale: "ar", label_en: "Arabic", label_original: "العَرَبِيَّة" },
  { locale: "bg", label_en: "Bulgarian", label_original: "български език" },
  { locale: "bs", label_en: "Bosnian", label_original: "Bosanski Jezik" },
  { locale: "ca", label_en: "Catalan", label_original: "català" },
  { locale: "cs", label_en: "Czech", label_original: "český jazyk" },
  { locale: "da", label_en: "Danish", label_original: "Dansk" },
  { locale: "de", label_en: "German", label_original: "Deutsch" },
  { locale: "el", label_en: "Greek", label_original: "ελληνικά" },
  { locale: "en", label_en: "English", label_original: "English" },
  { locale: "es", label_en: "Spanish", label_original: "Español" },
  {
    locale: "es-MX",
    label_en: "Spanish (Mexico)",
    label_original: "Español - MX",
  },
  {
    locale: "es-US",
    label_en: "Spanish (United States)",
    label_original: "Español - US",
  },
  { locale: "et", label_en: "Estonian", label_original: "Eesti" },
  { locale: "eu", label_en: "Basque", label_original: "euskara" },
  { locale: "fi", label_en: "Finnish", label_original: "Suomi" },
  { locale: "fr", label_en: "French", label_original: "Français" },
  {
    locale: "fr-CA",
    label_en: "French (Canada)",
    label_original: "Français - CA",
  },
  { locale: "gl", label_en: "Galician", label_original: "Galego" },
  { locale: "hi-IN", label_en: "Hindi (India)", label_original: "हिन्दी" },
  { locale: "hr", label_en: "Croatian", label_original: "Hrvatski Jezik" },
  { locale: "hu", label_en: "Hungarian", label_original: "magyar" },
  { locale: "it", label_en: "Italian", label_original: "Italiano" },
  { locale: "ja", label_en: "Japanese", label_original: "日本語" },
  { locale: "lt", label_en: "Lithuanian", label_original: "lietuvių kalba" },
  { locale: "lv", label_en: "Latvian", label_original: "latviešu valoda" },
  { locale: "mt", label_en: "Maltese", label_original: "Malti" },
  { locale: "nl", label_en: "Dutch", label_original: "Nederlands" },
  { locale: "no", label_en: "Norwegian", label_original: "Norsk" },
  { locale: "pl", label_en: "Polish", label_original: "Polski" },
  {
    locale: "pt-BR",
    label_en: "Portuguese (Brazil)",
    label_original: "Português - BR",
  },
  {
    locale: "pt-PT",
    label_en: "Portuguese (Portugal)",
    label_original: "Português - PT",
  },
  { locale: "ro", label_en: "Romanian", label_original: "limba română" },
  { locale: "ru", label_en: "Russian", label_original: "русский язык" },
  { locale: "sk", label_en: "Slovak", label_original: "slovenčina" },
  { locale: "sl", label_en: "Slovenian", label_original: "Slovenski Jezik" },
  {
    locale: "sr-Cyrl",
    label_en: "Serbian (Cyrillic)",
    label_original: "српски",
  },
  { locale: "sr-Latn", label_en: "Serbian (Latin)", label_original: "Srpski" },
  { locale: "sv", label_en: "Swedish", label_original: "Sverige" },
  { locale: "tr", label_en: "Turkish", label_original: "Türkçe" },
  { locale: "uk", label_en: "Ukrainian", label_original: "українська мова" },
  {
    locale: "zh",
    label_en: "Chinese (Simplified)",
    label_original: "简体中文",
  },
  {
    locale: "zh-Hant",
    label_en: "Chinese (Traditional)",
    label_original: "繁體中文",
  },
];
