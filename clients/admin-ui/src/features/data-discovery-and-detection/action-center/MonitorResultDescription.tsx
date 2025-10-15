import { useMemo } from "react";

import { nFormatter } from "~/features/common/utils";

import { MonitorUpdateNames } from "./constants";
import { MonitorAggregatedResults } from "./types";

const MonitorUpdatesToIgnore = [
  "classified_low_confidence",
  "classified_high_confidence",
  "classified_manually",
];

export const MonitorResultDescription = ({
  updates,
  isAssetList,
}: {
  updates: MonitorAggregatedResults["updates"];
  isAssetList?: boolean;
}) => {
  const updateStrings = useMemo(() => {
    if (!updates) {
      return [];
    }
    return Object.entries(updates)
      .filter(
        (update) =>
          update[1] > 0 && !MonitorUpdatesToIgnore.includes(update[0]),
      )
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map((update) => {
        return `${nFormatter(update[1])} ${MonitorUpdateNames[update[0] as keyof MonitorAggregatedResults["updates"]]}${!isAssetList || update[1] === 1 ? "" : "s"}`;
      });
  }, [updates, isAssetList]);

  if (!updates) {
    return null;
  }

  if (isAssetList) {
    const assetListString = updateStrings.join(", ");

    // TODO: see below
    return <span>{assetListString} detected.</span>;
  }

  const datastoreUpdatesString = updateStrings.join(", ");

  // TODO: Eventually this will get more complex, but for now we wrap it in a simple span to make the return type a JSX.Element and not a string, to appease the TypeScript linter. (same thing above for the web updates string)
  return <span>{datastoreUpdatesString}</span>;
};
