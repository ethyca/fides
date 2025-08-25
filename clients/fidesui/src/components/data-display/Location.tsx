import { ISO31661Entry, ISO31662Entry } from "iso-3166";

import { isoEntryToLocationProps } from "./location.utils";

export type LocationDisplayProps = {
  isoEntry: ISO31661Entry | ISO31662Entry;
  showFlag?: boolean;
};

export const useIsoLocationDisplay = ({
  isoEntry,
  showFlag = true,
}: LocationDisplayProps) => {
  const userTranslation = new Intl.DisplayNames(navigator.language, {
    type: "region",
  });

  const locationProps = isoEntryToLocationProps(isoEntry, userTranslation);

  return `${showFlag ? `${locationProps?.flag} ` : ""}${[
    locationProps?.country ?? null,
    "region" in locationProps ? locationProps.region : null,
  ]
    .flatMap((val) => (val ? [[val]] : []))
    .join(" / ")}`;
};

export const LocationDisplay = ({
  isoEntry,
  showFlag,
}: LocationDisplayProps) => {
  const formattedString = useIsoLocationDisplay({ isoEntry, showFlag });

  return <span>{formattedString}</span>;
};

export default LocationDisplay;
