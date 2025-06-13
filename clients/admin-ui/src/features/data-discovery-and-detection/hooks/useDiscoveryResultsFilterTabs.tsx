import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import { DiffStatus } from "~/types/api";

interface DiscoveryResultsFilterTabsProps {
  initialActiveTabKey?: string;
}

const useDiscoveryResultsFilterTabs = ({
  initialActiveTabKey = "action-required",
}: DiscoveryResultsFilterTabsProps) => {
  const [activeTabKey, setActiveTabKey] = useState(initialActiveTabKey);

  const router = useRouter();

  const onTabChange = useCallback(
    async (tab: string) => {
      setActiveTabKey(tab);

      if (router.isReady) {
        await router.replace(
          {
            pathname: router.pathname,
            query: { ...router.query, filterTab: tab },
          },
          undefined,
          { shallow: true },
        );
      }
    },
    [router],
  );

  const filterTabs = useMemo(
    () => [
      {
        label: "Action Required",
        key: "action-required",
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
        key: "in-progress",
        filters: [DiffStatus.CLASSIFYING, DiffStatus.CLASSIFICATION_QUEUED],
        childFilters: [
          DiffStatus.CLASSIFYING,
          DiffStatus.CLASSIFICATION_QUEUED,
        ],
      },
      {
        label: "Unmonitored",
        key: "unmonitored",
        filters: [DiffStatus.MUTED],
        childFilters: [],
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
  };
};
export default useDiscoveryResultsFilterTabs;
