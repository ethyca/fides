import { useMemo } from "react";

import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";

export enum TopLevelActionCenterTabHash {
  ATTENTION_REQUIRED = "attention-required",
  IN_PROGRESS = "in-progress",
}

const useTopLevelActionCenterTabs = () => {
  const { activeTab, onTabChange } = useURLHashedTabs({
    tabKeys: Object.values(TopLevelActionCenterTabHash),
  });

  const tabs = useMemo(
    () => [
      {
        label: "Attention required",
        hash: TopLevelActionCenterTabHash.ATTENTION_REQUIRED,
      },
      {
        label: "In progress",
        hash: TopLevelActionCenterTabHash.IN_PROGRESS,
      },
    ],
    [],
  );

  return {
    tabs,
    activeTab,
    onTabChange,
  };
};

export default useTopLevelActionCenterTabs;
