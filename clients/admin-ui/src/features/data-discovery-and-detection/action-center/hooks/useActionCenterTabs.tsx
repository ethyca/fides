import { useMemo } from "react";

import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";
import { ReadOnlyNonEmptyArray } from "~/features/common/utils/array";
import { DiffStatus } from "~/types/api";

export type ActionCenterTabHash = "attention-required" | "added" | "ignored";

const ACTION_CENTER_TAB_HASHES: ReadOnlyNonEmptyArray<ActionCenterTabHash> = [
  "attention-required",
  "added",
  "ignored",
] as const;

type ActionCenterTab = {
  label: "Attention required" | "Added" | "Ignored";
  params: {
    diff_status: Array<DiffStatus>;
    system?: string;
  };
  hash: ActionCenterTabHash;
};

type ActionCenterTabs = [ActionCenterTab, ActionCenterTab, ActionCenterTab];

const useActionCenterTabs = (systemId?: string) => {
  const { activeTab, onTabChange } = useURLHashedTabs({
    tabKeys: ACTION_CENTER_TAB_HASHES,
  });

  const filterTabs: ActionCenterTabs = useMemo(
    () => [
      {
        label: "Attention required",
        params: {
          diff_status: [DiffStatus.ADDITION],
          system: systemId,
        },
        hash: "attention-required",
      },
      {
        label: "Added",
        params: {
          diff_status: [DiffStatus.MONITORED],
        },
        hash: "added",
      },
      {
        label: "Ignored",
        params: {
          diff_status: [DiffStatus.MUTED],
          system: systemId,
        },
        hash: "ignored",
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
