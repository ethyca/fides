import { useRouter } from "next/router";
import { useCallback, useState } from "react";

import { FilterTab } from "~/features/data-discovery-and-detection/hooks/useDetectionResultsFilterTabs";
import { DiffStatus } from "~/types/api";

interface DiscoveryResultsFilterTabsProps {
  initialActiveTabKey?: DiscoveryResultFilterTabs;
}

export enum DiscoveryResultFilterTabs {
  ACTION_REQUIRED = "action-required",
  IN_PROGRESS = "in-progress",
  UNMONITORED = "unmonitored",
}

const tabMap: Record<DiscoveryResultFilterTabs, FilterTab> = {
  [DiscoveryResultFilterTabs.ACTION_REQUIRED]: {
    label: "Action Required",
    key: DiscoveryResultFilterTabs.ACTION_REQUIRED,
    filters: [
      DiffStatus.CLASSIFICATION_ADDITION,
      DiffStatus.CLASSIFICATION_UPDATE,
    ],
    childFilters: [
      DiffStatus.CLASSIFICATION_ADDITION,
      DiffStatus.CLASSIFICATION_UPDATE,
    ],
  },
  [DiscoveryResultFilterTabs.IN_PROGRESS]: {
    label: "In progress",
    key: "in-progress",
    filters: [DiffStatus.CLASSIFYING, DiffStatus.CLASSIFICATION_QUEUED],
    childFilters: [DiffStatus.CLASSIFYING, DiffStatus.CLASSIFICATION_QUEUED],
  },
  [DiscoveryResultFilterTabs.UNMONITORED]: {
    label: "Unmonitored",
    key: DiscoveryResultFilterTabs.UNMONITORED,
    filters: [DiffStatus.MUTED],
    childFilters: [],
  },
};

const useDiscoveryResultsFilterTabs = ({
  initialActiveTabKey = DiscoveryResultFilterTabs.ACTION_REQUIRED,
}: DiscoveryResultsFilterTabsProps) => {
  const [activeTabKey, setActiveTabKey] = useState(initialActiveTabKey);

  const router = useRouter();

  const onTabChange = useCallback(
    async (tab: DiscoveryResultFilterTabs) => {
      setActiveTabKey(tab);

      if (router.isReady) {
        await router.replace(
          {
            pathname: router.pathname,
            query: router.query,
            hash: tab,
          },
          undefined,
          { shallow: true },
        );
      }
    },
    [router],
  );

  return {
    filterTabs: Object.values(tabMap),
    activeTabKey,
    onTabChange,
    activeDiffFilters: tabMap[activeTabKey]?.filters,
    activeChildDiffFilters: tabMap[activeTabKey]?.childFilters,
  };
};
export default useDiscoveryResultsFilterTabs;
