import countries from "i18n-iso-countries";
import english from "i18n-iso-countries/langs/en.json";

countries.registerLocale(english);

export const COUNTRY_NAMES = countries.getNames("en", { select: "official" });
export const COUNTRY_OPTIONS = Object.keys(COUNTRY_NAMES).map(
  (countryCode) => ({
    value: countries.alpha2ToAlpha3(countryCode),
    label: COUNTRY_NAMES[countryCode],
  }),
);
