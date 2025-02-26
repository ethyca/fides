/* eslint-disable object-shorthand */
import type { Language, Locale, Messages } from "..";
/**
 * Statically load all the pre-localized dictionaries from the ./locales directory.
 *
 * NOTE: This process isn't automatic. To add a new static locale, follow these steps:
 * 1) Add the static import of the new ./{locale}/messages.json file
 * 2) Add the locale to the STATIC_MESSAGES object below
 * 3) Add the locale to the LOCALE_LANGUAGE_MAP object below
 */
import ar from "./ar/messages.json";
import bg from "./bg/messages.json";
import bs from "./bs/messages.json";
import ca from "./ca/messages.json";
import cs from "./cs/messages.json";
import da from "./da/messages.json";
import de from "./de/messages.json";
import el from "./el/messages.json";
import en from "./en/messages.json";
import es from "./es/messages.json";
import esMX from "./es-MX/messages.json";
import et from "./et/messages.json";
import eu from "./eu/messages.json";
import fi from "./fi/messages.json";
import fr from "./fr/messages.json";
import frCA from "./fr-CA/messages.json";
import gl from "./gl/messages.json";
import hiIN from "./hi-IN/messages.json";
import hr from "./hr/messages.json";
import hu from "./hu/messages.json";
import it from "./it/messages.json";
import ja from "./ja/messages.json";
import lt from "./lt/messages.json";
import lv from "./lv/messages.json";
import mt from "./mt/messages.json";
import nl from "./nl/messages.json";
import no from "./no/messages.json";
import pl from "./pl/messages.json";
import ptBR from "./pt-BR/messages.json";
import ptPT from "./pt-PT/messages.json";
import ro from "./ro/messages.json";
import ru from "./ru/messages.json";
import sk from "./sk/messages.json";
import sl from "./sl/messages.json";
import srCyrl from "./sr-Cyrl/messages.json";
import srLatn from "./sr-Latn/messages.json";
import sv from "./sv/messages.json";
import tr from "./tr/messages.json";
import uk from "./uk/messages.json";
import zh from "./zh/messages.json";

export const STATIC_MESSAGES: Record<Locale, Messages> = {
  ar: ar,
  bg: bg,
  bs: bs,
  ca: ca,
  cs: cs,
  da: da,
  de: de,
  el: el,
  en: en,
  es: es,
  "es-MX": esMX,
  et: et,
  eu: eu,
  fi: fi,
  fr: fr,
  "fr-CA": frCA,
  gl: gl,
  "hi-IN": hiIN,
  hr: hr,
  hu: hu,
  it: it,
  ja: ja,
  lt: lt,
  lv: lv,
  mt: mt,
  nl: nl,
  no: no,
  pl: pl,
  "pt-BR": ptBR,
  "pt-PT": ptPT,
  ro: ro,
  ru: ru,
  sk: sk,
  sl: sl,
  "sr-Cyrl": srCyrl,
  "sr-Latn": srLatn,
  sv: sv,
  tr: tr,
  uk: uk,
  zh: zh,
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
  { locale: "zh", label_en: "Chinese", label_original: "中文" },
];
