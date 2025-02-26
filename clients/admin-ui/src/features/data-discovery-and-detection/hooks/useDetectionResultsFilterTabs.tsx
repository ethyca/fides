import { useMemo, useState } from "react";

import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import { DiffStatus } from "~/types/api";

interface DetectionResultFiltersTabsProps {
  initialFilterTabIndex?: number;
}

const useDetectionResultsFilterTabs = ({
  initialFilterTabIndex = 0,
}: DetectionResultFiltersTabsProps) => {
  const [filterTabIndex, setFilterTabIndex] = useState(initialFilterTabIndex);

  const filterTabs = useMemo(
    () => [
      {
        label: "Action Required",
        filters: [DiffStatus.ADDITION, DiffStatus.REMOVAL],
        childFilters: [DiffStatus.ADDITION, DiffStatus.REMOVAL],
      },
      {
        label: "Monitored",
        filters: [DiffStatus.MONITORED],
        childFilters: [],
        changeTypeOverride: ResourceChangeType.MONITORED,
      },
      {
        label: "Unmonitored",
        filters: [DiffStatus.MUTED],
        childFilters: [],
        changeTypeOverride: ResourceChangeType.MUTED,
      },
    ],
    [],
  );

  return {
    filterTabs,
    filterTabIndex,
    setFilterTabIndex,
    activeDiffFilters: filterTabs[filterTabIndex].filters,
    activeChildDiffFilters: filterTabs[filterTabIndex].childFilters,
    activeChangeTypeOverride: filterTabs[filterTabIndex].changeTypeOverride,
  };
};
export default useDetectionResultsFilterTabs;
