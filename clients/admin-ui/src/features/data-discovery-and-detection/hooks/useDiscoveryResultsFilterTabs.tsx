import { useMemo, useState } from "react";

import { DiffStatus } from "~/types/api";

interface DiscoveryResultsFilterTabsProps {
  initialFilterTabIndex?: number;
}

export enum DiscoveryResultsFilterTabsIndexEnum {
  ACTION_REQUIRED = 0,
  UNMONITORED = 1,
}

const useDiscoveryResultsFilterTabs = ({
  initialFilterTabIndex = 0,
}: DiscoveryResultsFilterTabsProps) => {
  const [filterTabIndex, setFilterTabIndex] = useState(initialFilterTabIndex);

  const filterTabs = useMemo(
    () => [
      {
        label: "Action Required",
        filters: [
          DiffStatus.CLASSIFICATION_ADDITION,
          DiffStatus.CLASSIFICATION_UPDATE,
        ],
        childFilters: [
          DiffStatus.CLASSIFICATION_ADDITION,
          DiffStatus.CLASSIFICATION_UPDATE,
        ],
      },
      {
        label: "In progress",
        filters: [DiffStatus.CLASSIFYING, DiffStatus.CLASSIFICATION_QUEUED],
        childFilters: [
          DiffStatus.CLASSIFYING,
          DiffStatus.CLASSIFICATION_QUEUED,
        ],
      },
      {
        label: "Unmonitored",
        filters: [DiffStatus.MUTED],
        childFilters: [],
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
  };
};
export default useDiscoveryResultsFilterTabs;
