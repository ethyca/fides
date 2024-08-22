import { useState } from "react";

import { DiffStatus } from "~/types/api";

const useDetectionResultFilterTabs = () => {
  const [tabIndex, setTabIndex] = useState(0);

  const tabs = [
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
    tabs,
    tabIndex,
    setTabIndex,
    activeDiffFilters: tabs[tabIndex].filters,
  };
};
export default useDetectionResultFilterTabs;
