import { useState } from "react";

import { DiffStatus } from "~/types/api";

interface DiscoveryResultsFilterTabsProps {
  initialFilterTabIndex?: number;
}

const useDiscoveryResultsFilterTabs = ({
  initialFilterTabIndex = 0,
}: DiscoveryResultsFilterTabsProps) => {
  const [filterTabIndex, setFilterTabIndex] = useState(initialFilterTabIndex);

  const filterTabs = [
    {
      label: "Action Required",
      filters: [DiffStatus.ADDITION, DiffStatus.REMOVAL],
    },
    {
      label: "Classifying",
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
export default useDiscoveryResultsFilterTabs;
