import { iso31661, ISO31661Entry, iso31662, ISO31662Entry } from "iso-3166";

import type { LocationDisplayProps } from "./Location";

/**
 * @description transforms a single alpha chaaracter into a regional indicator that is used to compose a flag emoji
 * @param alpha: expects a single alpha character to be shifted to a regionalIndicator usesd to compose the assosicated emoji with an alpha2 code
 */
export const intoRegionalIndicator = (alpha: string) =>
  String.fromCodePoint(alpha.charCodeAt(0) + 127397);

/**
 * @description transforms a single alpha chaaracter into a regional indicator that is used to compose a flag emoji
 * @param alpha2: takes a valid iso-31661 alpha2 code and converts it into an associated flag emoji
 */
export const encodeIsoAlpha2ToFlag = (alpha2: string) =>
  `${intoRegionalIndicator(alpha2.charAt(0))}${intoRegionalIndicator(alpha2.charAt(1))}`;

/**
 * @description finds an entry for iso-31661 or iso-31662 codes
 * @param isoCode: string to mach against iso-31661 or iso-31662 entries
 */
export const isoStringToEntry = (
  isoCode: string,
): ISO31661Entry | ISO31662Entry | undefined => {
  const [country, region] = isoCode.toUpperCase().split(/[-,_]/);

  if (region) {
    return iso31662.find(({ code }) => code === [country, region].join("-"));
  }

  return iso31661.find(({ alpha2 }) => alpha2 === country);
};

/**
 * @description: creates a flag emoji from a valid iso string with a fallback
 * @param isoCode: expects a valid iso-31661 or iso-31662 code
 */
export const isoCodeToFlag = (isoCode?: string, fallback: string = "") =>
  isoCode ? encodeIsoAlpha2ToFlag(isoCode.split(/[-,_]/)[0] || "00") : fallback;

export const getIso31661LocationProps = (
  loc: ISO31661Entry,
  userTranslation: Intl.DisplayNames,
) => ({
  country: userTranslation.of(loc.alpha2) ?? loc.name,
  flag: encodeIsoAlpha2ToFlag(loc.alpha2),
});

export const getIso31662LocationProps = (
  loc: ISO31662Entry,
  userTranslation: Intl.DisplayNames,
) => ({
  country:
    userTranslation.of(loc.parent) ??
    iso31661.find((entry) => entry.alpha2 === loc.parent)?.name,
  region: loc.name,
  flag: encodeIsoAlpha2ToFlag(loc.parent),
});

export const isoEntryToLocationProps = (
  loc: ISO31661Entry | ISO31662Entry,
  userTranslation: Intl.DisplayNames,
) => {
  if (loc && "parent" in loc) {
    return getIso31662LocationProps(loc, userTranslation);
  }

  return getIso31661LocationProps(loc, userTranslation);
};

export const formatIsoLocation = ({
  isoEntry,
  showFlag,
  userTranslation = new Intl.DisplayNames(navigator.language, {
    type: "region",
  }),
}: LocationDisplayProps & { userTranslation?: Intl.DisplayNames }) => {
  const locationProps = isoEntryToLocationProps(isoEntry, userTranslation);

  return `${showFlag ? `${locationProps?.flag} ` : ""}${[
    locationProps?.country ?? null,
    "region" in locationProps ? locationProps.region : null,
  ]
    .flatMap((val) => (val ? [[val]] : []))
    .join(" / ")}`;
};
