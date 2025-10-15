import { useMemo } from "react";

import { nFormatter } from "~/features/common/utils";
import { DatastoreMonitorUpdates, WebMonitorUpdates } from "~/types/api";

import { MonitorUpdateNames } from "./constants";
import { MonitorAggregatedResults } from "./types";

const MONITOR_UPDATES_TO_IGNORE = [
  "classified_low_confidence",
  "classified_high_confidence",
  "classified_manually",
] as const satisfies readonly (
  | keyof DatastoreMonitorUpdates
  | keyof WebMonitorUpdates
)[];

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
          !MONITOR_UPDATES_TO_IGNORE.includes(
            update[0] as keyof MonitorAggregatedResults["updates"],
          ),
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

  // TODO: Eventually this will get more complex, but for now we wrap it in a simple span to make the return type a JSX.Element and not a string, to appease the TypeScript linter. (same thing above for assets)
  return <span>{datastoreUpdatesString}</span>;
};
