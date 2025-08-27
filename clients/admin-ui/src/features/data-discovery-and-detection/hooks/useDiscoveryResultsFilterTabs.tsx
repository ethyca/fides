import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";
import { FilterTab } from "~/features/data-discovery-and-detection/hooks/useDetectionResultsFilterTabs";
import { DiffStatus } from "~/types/api";

export enum DiscoveryResultFilterTabs {
  ACTION_REQUIRED = "action-required",
  IN_PROGRESS = "in-progress",
  UNMONITORED = "unmonitored",
}

const TAB_MAP: Record<DiscoveryResultFilterTabs, FilterTab> = {
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

const useDiscoveryResultsFilterTabs = () => {
  const { activeTab, onTabChange } = useURLHashedTabs({
    tabKeys: Object.values(DiscoveryResultFilterTabs),
  });

  return {
    filterTabs: Object.values(TAB_MAP),
    activeTab,
    onTabChange,
    activeDiffFilters: TAB_MAP[activeTab as DiscoveryResultFilterTabs]?.filters,
    activeChildDiffFilters:
      TAB_MAP[activeTab as DiscoveryResultFilterTabs]?.childFilters,
  };
};
export default useDiscoveryResultsFilterTabs;
