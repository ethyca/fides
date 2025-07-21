import { useMemo } from "react";

import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";
import { DiffStatus } from "~/types/api";

export enum ActionCenterTabHash {
  ATTENTION_REQUIRED = "attention-required",
  RECENT_ACTIVITY = "recent-activity",
  IGNORED = "ignored",
}

const useActionCenterTabs = (systemId?: string) => {
  const { activeTab, onTabChange } = useURLHashedTabs({
    tabKeys: Object.values(ActionCenterTabHash),
  });

  const filterTabs = useMemo(
    () => [
      {
        label: "Attention required",
        params: {
          diff_status: [DiffStatus.ADDITION],
          system: systemId,
        },
        hash: ActionCenterTabHash.ATTENTION_REQUIRED,
      },
      {
        label: "Recent activity",
        params: {
          diff_status: [DiffStatus.MONITORED],
        },
        hash: ActionCenterTabHash.RECENT_ACTIVITY,
      },
      {
        label: "Ignored",
        params: {
          diff_status: [DiffStatus.MUTED],
          system: systemId,
        },
        hash: ActionCenterTabHash.IGNORED,
      },
    ],
    [systemId],
  );

  const activeTabData = useMemo(
    () => filterTabs.find((tab) => tab.hash === activeTab) ?? filterTabs[0],
    [filterTabs, activeTab],
  );

  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { diff_status, system } = activeTabData.params;

  const actionsDisabled = useMemo(
    () => diff_status.includes(DiffStatus.MONITORED),
    [diff_status],
  );

  const activeParams = useMemo(
    () => (systemId ? { diff_status, system } : { diff_status }),
    [systemId, diff_status, system],
  );

  return {
    filterTabs,
    activeTab,
    onTabChange,
    activeParams,
    actionsDisabled,
  };
};

export default useActionCenterTabs;
