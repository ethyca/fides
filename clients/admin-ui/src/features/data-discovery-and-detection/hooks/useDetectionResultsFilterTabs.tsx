import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import { DiffStatus } from "~/types/api";

interface DetectionResultFiltersTabsProps {
  initialActiveTabKey?: string;
}

const useDetectionResultsFilterTabs = ({
  initialActiveTabKey = "action-required",
}: DetectionResultFiltersTabsProps) => {
  const router = useRouter();
  const [activeTabKey, setActiveTabKey] = useState(initialActiveTabKey);

  const onTabChange = useCallback(
    async (tab: string) => {
      setActiveTabKey(tab);
      console.log("tab", tab);

      if (router.isReady) {
        await router.replace(
          {
            pathname: router.pathname,
            query: { ...router.query },
            hash: tab,
          },
          undefined,
          { shallow: true },
        );
      }
    },
    [router],
  );

  // TODO: why is onTabChange using the label and not the key?

  const filterTabs = useMemo(
    () => [
      {
        label: "Action Required",
        key: "action-required",
        filters: [DiffStatus.ADDITION, DiffStatus.REMOVAL],
        childFilters: [DiffStatus.ADDITION, DiffStatus.REMOVAL],
      },
      {
        label: "Monitored",
        key: "monitored",
        filters: [DiffStatus.MONITORED],
        childFilters: [],
        changeTypeOverride: ResourceChangeType.MONITORED,
      },
      {
        label: "Unmonitored",
        key: "unmonitored",
        filters: [DiffStatus.MUTED],
        childFilters: [],
        changeTypeOverride: ResourceChangeType.MUTED,
      },
    ],
    [],
  );

  return {
    filterTabs,
    activeTabKey,
    onTabChange,
    activeDiffFilters: filterTabs.find((tab) => tab.key === activeTabKey)
      ?.filters,
    activeChildDiffFilters: filterTabs.find((tab) => tab.key === activeTabKey)
      ?.childFilters,
    activeChangeTypeOverride: filterTabs.find((tab) => tab.key === activeTabKey)
      ?.changeTypeOverride,
  };
};
export default useDetectionResultsFilterTabs;
