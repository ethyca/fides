/* eslint-disable object-shorthand */
import type { Locale, Messages } from "../../../i18n";
/**
 * Statically load all the pre-localized dictionaries from the ./locales directory.
 *
 * NOTE: This process isn't automatic. To add a new static locale, follow these steps:
 * 1) Add the static import of the new ./{locale}/messages-tcf.json file
 * 2) Add the locale to the STATIC_MESSAGES_TCF object below
 */
import ar from "./ar/messages-tcf.json";
import bg from "./bg/messages-tcf.json";
import bs from "./bs/messages-tcf.json";
import ca from "./ca/messages-tcf.json";
import cs from "./cs/messages-tcf.json";
import da from "./da/messages-tcf.json";
import de from "./de/messages-tcf.json";
import el from "./el/messages-tcf.json";
import en from "./en/messages-tcf.json";
import es from "./es/messages-tcf.json";
import esMX from "./es-MX/messages-tcf.json";
import et from "./et/messages-tcf.json";
import eu from "./eu/messages-tcf.json";
import fi from "./fi/messages-tcf.json";
import fr from "./fr/messages-tcf.json";
import frCA from "./fr-CA/messages-tcf.json";
import gl from "./gl/messages-tcf.json";
import hiIN from "./hi-IN/messages-tcf.json";
import hr from "./hr/messages-tcf.json";
import hu from "./hu/messages-tcf.json";
import it from "./it/messages-tcf.json";
import ja from "./ja/messages-tcf.json";
import lt from "./lt/messages-tcf.json";
import lv from "./lv/messages-tcf.json";
import mt from "./mt/messages-tcf.json";
import nl from "./nl/messages-tcf.json";
import no from "./no/messages-tcf.json";
import pl from "./pl/messages-tcf.json";
import ptBR from "./pt-BR/messages-tcf.json";
import ptPT from "./pt-PT/messages-tcf.json";
import ro from "./ro/messages-tcf.json";
import ru from "./ru/messages-tcf.json";
import sk from "./sk/messages-tcf.json";
import sl from "./sl/messages-tcf.json";
import srCyrl from "./sr-Cyrl/messages-tcf.json";
import srLatn from "./sr-Latn/messages-tcf.json";
import sv from "./sv/messages-tcf.json";
import tr from "./tr/messages-tcf.json";
import uk from "./uk/messages-tcf.json";
import zh from "./zh/messages-tcf.json";

export const STATIC_MESSAGES_TCF: Record<Locale, Messages> = {
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
