import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";
import { ReadOnlyNonEmptyArray } from "~/features/common/utils/array";
import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import { DiffStatus } from "~/types/api";

export type DetectionResultFilterTab =
  | "action-required"
  | "monitored"
  | "unmonitored";

const DETECTION_RESULT_FILTER_TABS: ReadOnlyNonEmptyArray<DetectionResultFilterTab> =
  ["action-required", "monitored", "unmonitored"] as const;

export interface FilterTab<T> {
  label: string;
  key: T;
  filters: DiffStatus[];
  childFilters: DiffStatus[];
  changeTypeOverride?: ResourceChangeType;
}

const TAB_MAP: Record<
  DetectionResultFilterTab,
  FilterTab<DetectionResultFilterTab>
> = {
  "action-required": {
    label: "Action Required",
    key: "action-required",
    filters: [DiffStatus.ADDITION, DiffStatus.REMOVAL],
    childFilters: [DiffStatus.ADDITION, DiffStatus.REMOVAL],
  },
  monitored: {
    label: "Monitored",
    key: "monitored",
    filters: [DiffStatus.MONITORED],
    childFilters: [],
    changeTypeOverride: ResourceChangeType.MONITORED,
  },
  unmonitored: {
    label: "Unmonitored",
    key: "unmonitored",
    filters: [DiffStatus.MUTED],
    childFilters: [],
    changeTypeOverride: ResourceChangeType.MUTED,
  },
};

const useDetectionResultsFilterTabs = () => {
  const { activeTab, onTabChange } = useURLHashedTabs({
    tabKeys: DETECTION_RESULT_FILTER_TABS,
  });

  return {
    filterTabs: Object.values(TAB_MAP),
    activeTabKey: activeTab,
    onTabChange,
    activeDiffFilters: TAB_MAP[activeTab].filters,
    activeChildDiffFilters: TAB_MAP[activeTab].childFilters,
    activeChangeTypeOverride: TAB_MAP[activeTab].changeTypeOverride,
  };
};
export default useDetectionResultsFilterTabs;
