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
  const updateStrings = useMemo(() => {
    if (!updates) {
      return [];
    }
    return Object.entries(updates)
      .filter((update) => update[1] > 0)
      .filter((update) => !MonitorUpdatesToIgnore.includes(update[0]))
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map((update) => {
        return `${nFormatter(update[1])} ${MonitorUpdateNames[update[0] as keyof MonitorAggregatedResults["updates"]]}`;
      });
  }, [updates]);

  if (!updates) {
    return null;
  }

  if (
    monitorType === ConnectionType.TEST_WEBSITE ||
    monitorType === ConnectionType.WEBSITE
  ) {
    const webUpdatesString = updateStrings.join(", ");

    return <span>{webUpdatesString} detected.</span>;
  }

  const datastoreUpdatesString = updateStrings.join(", ");

  return <span>{datastoreUpdatesString}</span>;
};
