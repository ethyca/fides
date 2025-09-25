import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";
import { ReadOnlyNonEmptyArray } from "~/features/common/utils/array";
import { FilterTab } from "~/features/data-discovery-and-detection/hooks/useDetectionResultsFilterTabs";
import { DiffStatus } from "~/types/api";

export type DiscoveryResultFilterTab =
  | "action-required"
  | "in-progress"
  | "unmonitored";

const DISCOVERY_RESULT_FILTER_TABS: ReadOnlyNonEmptyArray<DiscoveryResultFilterTab> =
  ["action-required", "in-progress", "unmonitored"] as const;

const TAB_MAP: Record<
  DiscoveryResultFilterTab,
  FilterTab<DiscoveryResultFilterTab>
> = {
  "action-required": {
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
  "in-progress": {
    label: "In progress",
    key: "in-progress",
    filters: [DiffStatus.CLASSIFYING, DiffStatus.CLASSIFICATION_QUEUED],
    childFilters: [DiffStatus.CLASSIFYING, DiffStatus.CLASSIFICATION_QUEUED],
  },
  unmonitored: {
    label: "Unmonitored",
    key: "unmonitored",
    filters: [DiffStatus.MUTED],
    childFilters: [],
  },
};

const useDiscoveryResultsFilterTabs = () => {
  const { activeTab, onTabChange } = useURLHashedTabs({
    tabKeys: DISCOVERY_RESULT_FILTER_TABS,
  });

  return {
    filterTabs: Object.values(TAB_MAP),
    activeTab,
    onTabChange,
    activeDiffFilters: TAB_MAP[activeTab].filters,
    activeChildDiffFilters: TAB_MAP[activeTab].childFilters,
  };
};
export default useDiscoveryResultsFilterTabs;
