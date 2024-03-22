/* eslint-disable object-shorthand */
import type { Locale, Messages, Language } from "..";

/**
 * Statically load all the pre-localized dictionaries from the ./locales directory.
 *
 * NOTE: This process isn't automatic. To add a new static locale, follow these steps:
 * 1) Add the static import of the new ./{locale}/messages.json file
 * 2) Add the locale to the LOCALES object below
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
  { locale: "ar", english: "Arabic", original: "العَرَبِيَّة" },
  { locale: "bg", english: "Bulgarian", original: "български език" },
  { locale: "bs", english: "Bosnian", original: "Bosanski Jezik" },
  { locale: "ca", english: "Catalan Spanish", original: "català" },
  { locale: "cs", english: "Czech", original: "český jazyk" },
  { locale: "da", english: "Danish", original: "Dansk" },
  { locale: "de", english: "German", original: "Deutsch" },
  { locale: "el", english: "Greek", original: "ελληνικά" },
  { locale: "en", english: "English", original: "English" },
  { locale: "es", english: "European Spanish", original: "Español" },
  { locale: "es-MX", english: "Mexican Spanish", original: "Español - MX" },
  { locale: "et", english: "Estonian", original: "Eesti" },
  { locale: "eu", english: "Basque Spanish", original: "euskara" },
  { locale: "fi", english: "Finnish", original: "Suomi" },
  { locale: "fl", english: "Filipino", original: "Pilipino" },
  { locale: "fr", english: "European French", original: "Français" },
  { locale: "fr-CA", english: "French Canadian", original: "Français - CA" },
  { locale: "gl", english: "Galician", original: "Galego" },
  { locale: "hi-IN", english: "Indian Hindi", original: "हिन्दी" },
  { locale: "hr", english: "Croatian", original: "Hrvatski Jezik" },
  { locale: "hu", english: "Hungarian", original: "magyar" },
  { locale: "hy", english: "Armenian", original: "Հայերեն" },
  { locale: "it", english: "Italian", original: "Italiano" },
  { locale: "ja", english: "Japanese", original: "日本語" },
  { locale: "lt", english: "Lithuanian", original: "lietuvių kalba" },
  { locale: "lv", english: "Latvian", original: "latviešu valoda" },
  { locale: "mt", english: "Maltese", original: "Malti" },
  { locale: "nl", english: "Dutch", original: "Nederlands" },
  { locale: "no", english: "Norwegian", original: "Norsk" },
  {
    locale: "pt-BR",
    english: "Brazilian Portuguese",
    original: "Português - BR",
  },
  {
    locale: "pt-PT",
    english: "Portugal Portuguese",
    original: "Português - PT",
  },
  { locale: "ro", english: "Romanian", original: "limba română" },
  { locale: "ru", english: "Russian", original: "русский язык" },
  { locale: "sk", english: "Slovak", original: "slovenčina" },
  { locale: "sl", english: "Slovenian", original: "Slovenski Jezik" },
  { locale: "sr-Cyrl", english: "Cyrillic Serbian", original: "српски" },
  { locale: "sr-Latn", english: "Latin Serbian", original: "Srpski" },
  { locale: "sv", english: "Swedish", original: "Sverige" },
  { locale: "tr", english: "Turkish", original: "Türkçe" },
  { locale: "uk", english: "Ukrainian", original: "українська мова" },
  { locale: "zh", english: "Chinese (Mandarin)", original: "中文" },
];
