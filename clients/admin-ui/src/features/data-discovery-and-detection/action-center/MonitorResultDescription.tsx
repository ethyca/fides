import { useMemo } from "react";

import { nFormatter } from "~/features/common/utils";
import { ConnectionType } from "~/types/api";

import { MonitorUpdateNames } from "./constants";
import { MonitorAggregatedResults } from "./types";

const MonitorUpdatesToIgnore = [
  "classified_low_confidence",
  "classified_high_confidence",
  "classified_manually",
];

export const MonitorResultDescription = ({
  updates,
  monitorType,
}: {
  updates: MonitorAggregatedResults["updates"];
  monitorType: ConnectionType;
}) => {
  const isWebMonitor =
    monitorType === ConnectionType.TEST_WEBSITE ||
    monitorType === ConnectionType.WEBSITE;
  const updateStrings = useMemo(() => {
    if (!updates) {
      return [];
    }
    return Object.entries(updates)
      .filter((update) => update[1] > 0)
      .filter((update) => !MonitorUpdatesToIgnore.includes(update[0]))
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map((update) => {
        return `${nFormatter(update[1])} ${MonitorUpdateNames[update[0] as keyof MonitorAggregatedResults["updates"]]}${!isWebMonitor || update[1] === 1 ? "" : "s"}`;
      });
  }, [updates, isWebMonitor]);

  if (!updates) {
    return null;
  }

  if (isWebMonitor) {
    const webUpdatesString = updateStrings.join(", ");

    // TODO: see below
    return <span>{webUpdatesString} detected.</span>;
  }

  const datastoreUpdatesString = updateStrings.join(", ");

  // TODO: Eventually this will get more complex, but for now we wrap it in a simple span to make the return type a JSX.Element and not a string, to appease the TypeScript linter. (same thing above for the web updates string)
  return <span>{datastoreUpdatesString}</span>;
};
