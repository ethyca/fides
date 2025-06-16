import { useRouter } from "next/router";
import { useCallback, useState } from "react";

import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import { DiffStatus } from "~/types/api";

interface DetectionResultFiltersTabsProps {
  initialActiveTabKey?: DetectionResultFilterTabs;
}

export enum DetectionResultFilterTabs {
  ACTION_REQUIRED = "action-required",
  MONITORED = "monitored",
  UNMONITORED = "unmonitored",
}

export interface FilterTab {
  label: string;
  key: string;
  filters: DiffStatus[];
  childFilters: DiffStatus[];
  changeTypeOverride?: ResourceChangeType;
}

const tabMap: Record<DetectionResultFilterTabs, FilterTab> = {
  [DetectionResultFilterTabs.ACTION_REQUIRED]: {
    label: "Action Required",
    key: DetectionResultFilterTabs.ACTION_REQUIRED,
    filters: [DiffStatus.ADDITION, DiffStatus.REMOVAL],
    childFilters: [DiffStatus.ADDITION, DiffStatus.REMOVAL],
  },
  [DetectionResultFilterTabs.MONITORED]: {
    label: "Monitored",
    key: DetectionResultFilterTabs.MONITORED,
    filters: [DiffStatus.MONITORED],
    childFilters: [],
    changeTypeOverride: ResourceChangeType.MONITORED,
  },
  [DetectionResultFilterTabs.UNMONITORED]: {
    label: "Unmonitored",
    key: DetectionResultFilterTabs.UNMONITORED,
    filters: [DiffStatus.MUTED],
    childFilters: [],
    changeTypeOverride: ResourceChangeType.MUTED,
  },
};

const useDetectionResultsFilterTabs = ({
  initialActiveTabKey = DetectionResultFilterTabs.ACTION_REQUIRED,
}: DetectionResultFiltersTabsProps) => {
  const router = useRouter();
  const [activeTabKey, setActiveTabKey] =
    useState<DetectionResultFilterTabs>(initialActiveTabKey);

  const onTabChange = useCallback(
    async (tab: DetectionResultFilterTabs) => {
      setActiveTabKey(tab);

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

  return {
    filterTabs: Object.values(tabMap),
    activeTabKey,
    onTabChange,
    activeDiffFilters: tabMap[activeTabKey]?.filters,
    activeChildDiffFilters: tabMap[activeTabKey]?.childFilters,
    activeChangeTypeOverride: tabMap[activeTabKey]?.changeTypeOverride,
  };
};
export default useDetectionResultsFilterTabs;
