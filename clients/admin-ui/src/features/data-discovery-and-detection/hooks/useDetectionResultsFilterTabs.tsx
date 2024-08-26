import { useState } from "react";

import { DiffStatus } from "~/types/api";

interface DetectionResultFiltersTabsProps {
  initialFilterTabIndex?: number;
}

const useDetectionResultsFilterTabs = ({
  initialFilterTabIndex = 0,
}: DetectionResultFiltersTabsProps) => {
  const [filterTabIndex, setFilterTabIndex] = useState(initialFilterTabIndex);

  const filterTabs = [
    {
      label: "Action Required",
      filters: [DiffStatus.ADDITION, DiffStatus.REMOVAL],
    },
    {
      label: "Monitored",
      filters: [DiffStatus.MONITORED],
    },
    {
      label: "Unmonitored",
      filters: [DiffStatus.MUTED],
    },
  ];

  return {
    filterTabs,
    filterTabIndex,
    setFilterTabIndex,
    activeDiffFilters: filterTabs[filterTabIndex].filters,
  };
};
export default useDetectionResultsFilterTabs;
