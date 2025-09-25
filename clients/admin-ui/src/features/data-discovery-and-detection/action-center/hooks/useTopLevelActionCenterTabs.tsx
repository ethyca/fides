import { useMemo } from "react";

import { useFeatures } from "~/features/common/features";
import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";
import { ReadOnlyNonEmptyArray } from "~/features/common/utils/array";

type TopLevelActionCenterTabHash = "attention-required" | "in-progress";

export const TOP_LEVEL_ACTION_CENTER_TABS: ReadOnlyNonEmptyArray<TopLevelActionCenterTabHash> =
  ["attention-required", "in-progress"];

type TopLevelTab = { label: string; hash: TopLevelActionCenterTabHash };

const useTopLevelActionCenterTabs = () => {
  const { flags } = useFeatures();
  const hasFullActionCenter = !!flags.alphaFullActionCenter;

  const availableTabKeys = useMemo(() => {
    return hasFullActionCenter
      ? TOP_LEVEL_ACTION_CENTER_TABS
      : (["attention-required"] as const);
  }, [hasFullActionCenter]);

  const { activeTab, onTabChange } = useURLHashedTabs({
    tabKeys: availableTabKeys,
  });

  const tabs: ReadOnlyNonEmptyArray<TopLevelTab> = useMemo(() => {
    const ActivityTab: TopLevelTab = {
      label: "Activity",
      hash: "in-progress",
    } as const;
    return [
      {
        label: "Attention required",
        hash: "attention-required",
      },
      ...(hasFullActionCenter ? [ActivityTab] : []),
    ] as const;
  }, [hasFullActionCenter]);

  return {
    tabs,
    activeTab,
    onTabChange,
  };
};

export default useTopLevelActionCenterTabs;
