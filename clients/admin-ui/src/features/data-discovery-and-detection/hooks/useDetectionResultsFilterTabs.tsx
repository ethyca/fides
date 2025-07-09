import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";
import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import { DiffStatus } from "~/types/api";

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

const useDetectionResultsFilterTabs = () => {
  const { activeTab, onTabChange } = useURLHashedTabs({
    tabKeys: Object.values(DetectionResultFilterTabs),
  });

  return {
    filterTabs: Object.values(tabMap),
    activeTabKey: activeTab,
    onTabChange,
    activeDiffFilters: tabMap[activeTab as DetectionResultFilterTabs]?.filters,
    activeChildDiffFilters:
      tabMap[activeTab as DetectionResultFilterTabs]?.childFilters,
    activeChangeTypeOverride:
      tabMap[activeTab as DetectionResultFilterTabs]?.changeTypeOverride,
  };
};
export default useDetectionResultsFilterTabs;
