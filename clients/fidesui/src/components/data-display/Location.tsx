import { iso31661, ISO31661Entry, iso31662, ISO31662Entry } from "iso-3166";

export const intoRegionalIndicator = (alpha: string) =>
  `&#x${(alpha.charCodeAt(0) + 127397).toString(16)};`;

export const encodeIsoAphaToFlag = (alpha2: string) =>
  `${intoRegionalIndicator(alpha2.charAt(0))}${intoRegionalIndicator(alpha2.charAt(1))}`;

export const getIsoEntry = (
  isoCode: string,
): ISO31661Entry | ISO31662Entry | undefined => {
  const [country, region] = isoCode.toUpperCase().split(/[-,_]/);

  if (region) {
    return iso31662.find(({ code }) => code === [country, region].join("-"));
  }

  return country
    ? iso31661.find(({ alpha2 }) => alpha2 === country)
    : undefined;
};

export const IsoFlag = ({
  isoCode,
  fallback = "",
}: {
  isoCode?: string | null;
  fallback?: string;
}) => (
  <span
    /* eslint-disable-next-line react/no-danger */
    dangerouslySetInnerHTML={{
      __html: isoCode
        ? encodeIsoAphaToFlag(isoCode.split(/[-,_]/)[0] || "00")
        : fallback,
    }}
  />
);

export const isoEntryToFormattedText = (
  userTranslation: Intl.DisplayNames,
  loc: ISO31661Entry | ISO31662Entry,
) => {
  if (loc && "parent" in loc) {
    const locationProps = {
      country:
        userTranslation.of(loc.parent) ??
        iso31661.find((entry) => entry.alpha2 === loc.parent),
      region: loc.name,
    };

    return [locationProps?.country, locationProps?.region]
      .flatMap((val) => (val ? [[val]] : []))
      .join(" / ");
  }
  const locationProps = {
    country: userTranslation.of(loc.alpha2) ?? loc.name,
    flag: <IsoFlag isoCode={loc.alpha2} />,
  };

  return locationProps.country;
};

export type LocationDisplayProps = {
  isoCode: ISO31661Entry | ISO31662Entry;
  showFlag?: boolean;
};

export const formatIsoLocation = ({ isoCode }: LocationDisplayProps) => {
  const userTranslation = new Intl.DisplayNames(navigator.language, {
    type: "region",
  });

  const getLocationProps = (loc?: ISO31661Entry | ISO31662Entry) => {
    if (loc && "parent" in loc) {
      return {
        country:
          userTranslation.of(loc.parent) ??
          iso31661.find((entry) => entry.alpha2 === loc.parent),
        region: loc.name,
        flag: <IsoFlag isoCode={loc.parent} />,
      };
    }

    return loc?.alpha2
      ? {
          country: userTranslation.of(loc.alpha2) ?? loc.name,
          flag: <IsoFlag isoCode={loc.alpha2} />,
        }
      : null;
  };

  const locationProps = getLocationProps(isoCode);

  return [locationProps?.country ?? null, locationProps?.region ?? null]
    .flatMap((val) => (val ? [[val]] : []))
    .join(" / ");
};

export const useIsoLoacationDisplay = ({
  isoCode,
  showFlag = true,
}: LocationDisplayProps) => {
  const userTranslation = new Intl.DisplayNames(navigator.language, {
    type: "region",
  });

  const getLocationProps = (loc?: ISO31661Entry | ISO31662Entry) => {
    if (loc && "parent" in loc) {
      return {
        country:
          userTranslation.of(loc.parent) ??
          iso31661.find((entry) => entry.alpha2 === loc.parent),
        region: loc.name,
        flag: <IsoFlag isoCode={loc.parent} />,
      };
    }

    return loc?.alpha2
      ? {
          country: userTranslation.of(loc.alpha2) ?? loc.name,
          flag: <IsoFlag isoCode={loc.alpha2} />,
        }
      : null;
  };

  const locationProps = getLocationProps(isoCode);

  return {
    formattedString: [
      locationProps?.country ?? null,
      locationProps?.region ?? null,
    ]
      .flatMap((val) => (val ? [[val]] : []))
      .join(" / "),
    flag: showFlag && locationProps?.flag,
  };
};

export const LocationDisplay = ({
  isoCode,
  showFlag,
}: LocationDisplayProps) => {
  const { formattedString, flag } = useIsoLoacationDisplay({
    isoCode,
    showFlag,
  });

  return (
    <>
      {flag} {formattedString}
    </>
  );
};

export default LocationDisplay;
