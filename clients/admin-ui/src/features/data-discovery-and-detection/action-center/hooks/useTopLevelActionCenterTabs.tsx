import { useMemo } from "react";

import { useFeatures } from "~/features/common/features";
import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";

export enum TopLevelActionCenterTabHash {
  ATTENTION_REQUIRED = "attention-required",
  IN_PROGRESS = "in-progress",
}

const useTopLevelActionCenterTabs = () => {
  const { flags } = useFeatures();
  const hasFullActionCenter = !!flags.alphaFullActionCenter;

  const availableTabKeys = useMemo(() => {
    return hasFullActionCenter
      ? Object.values(TopLevelActionCenterTabHash)
      : [TopLevelActionCenterTabHash.ATTENTION_REQUIRED];
  }, [hasFullActionCenter]);

  const { activeTab, onTabChange } = useURLHashedTabs({
    tabKeys: availableTabKeys,
  });

  const tabs = useMemo(() => {
    const baseTabs = [
      {
        label: "Attention required",
        hash: TopLevelActionCenterTabHash.ATTENTION_REQUIRED,
      },
    ];
    if (hasFullActionCenter) {
      baseTabs.push({
        label: "Activity",
        hash: TopLevelActionCenterTabHash.IN_PROGRESS,
      });
    }
    return baseTabs;
  }, [hasFullActionCenter]);

  return {
    tabs,
    activeTab,
    onTabChange,
  };
};

export default useTopLevelActionCenterTabs;
