import { useMemo } from "react";

import { nFormatter } from "~/features/common/utils";

import { MONITOR_UPDATE_NAMES, MONITOR_UPDATES_TO_IGNORE } from "./constants";
import { MonitorAggregatedResults } from "./types";

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
          update[1] > 0 &&
          !MONITOR_UPDATES_TO_IGNORE.includes(
            update[0] as keyof MonitorAggregatedResults["updates"],
          ),
      )
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map((update) => {
        return `${nFormatter(update[1])} ${MONITOR_UPDATE_NAMES.get(update[0] as keyof MonitorAggregatedResults["updates"])}${isAssetList && update[1] !== 1 ? "s" : ""}`;
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

  // TODO: Eventually this will get more complex, but for now we wrap it in a simple span to make the return type a JSX.Element and not a string, to appease the TypeScript linter. (same thing above for assets)
  return <span>{datastoreUpdatesString}</span>;
};
