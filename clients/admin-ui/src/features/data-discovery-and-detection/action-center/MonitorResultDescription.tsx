import { useMemo } from "react";

import { nFormatter } from "~/features/common/utils";

import {
  MONITOR_UPDATE_NAMES,
  MONITOR_UPDATE_ORDER,
  MONITOR_UPDATES_TO_IGNORE,
} from "./constants";
import { MonitorUpdates } from "./types";

type MonitorUpdateKey = keyof MonitorUpdates;

export const MonitorResultDescription = ({
  updates,
  isAssetList,
}: {
  updates: MonitorUpdates;
  isAssetList?: boolean;
}) => {
  const getMonitorUpdateName = (key: string) => {
    return MONITOR_UPDATE_NAMES.get(key as MonitorUpdateKey);
  };
  const updateStrings = useMemo(() => {
    if (!updates) {
      return [];
    }
    return Object.entries(updates)
      .filter(
        ([key, count]) =>
          count > 0 &&
          !MONITOR_UPDATES_TO_IGNORE.includes(key as MonitorUpdateKey),
      )
      .sort((a, b) => {
        const indexA = MONITOR_UPDATE_ORDER.indexOf(a[0] as MonitorUpdateKey);
        const indexB = MONITOR_UPDATE_ORDER.indexOf(b[0] as MonitorUpdateKey);
        // Handle keys not in order array by placing them at the end
        if (indexA === -1 && indexB === -1) {
          return 0;
        }
        if (indexA === -1) {
          return 1;
        }
        if (indexB === -1) {
          return -1;
        }
        return indexA - indexB;
      })
      .map(([key, count]) => {
        return `${nFormatter(count)} ${getMonitorUpdateName(key)}${isAssetList && count !== 1 ? "s" : ""}`;
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
