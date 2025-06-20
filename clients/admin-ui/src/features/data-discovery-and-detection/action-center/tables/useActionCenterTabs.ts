import { useRouter } from "next/router";
import { useCallback, useState } from "react";

import { DiffStatus } from "~/types/api";

export enum ActionCenterTabHash {
  ATTENTION_REQUIRED = "#attention-required",
  RECENT_ACTIVITY = "#recent-activity",
  IGNORED = "#ignored",
}

const normalizeHash = (hash: string): ActionCenterTabHash => {
  const normalizedHash = hash.startsWith("#") ? hash : `#${hash}`;
  return normalizedHash as ActionCenterTabHash;
};

const useActionCenterTabs = ({
  systemId,
  initialHash,
}: {
  systemId?: string;
  initialHash?: string;
}) => {
  const router = useRouter();
  const getInitialTab = () => {
    return initialHash
      ? normalizeHash(initialHash)
      : ActionCenterTabHash.ATTENTION_REQUIRED;
  };

  const [activeTab, setActiveTab] =
    useState<ActionCenterTabHash>(getInitialTab());

  const onTabChange = useCallback(
    async (tab: ActionCenterTabHash) => {
      // Update local state first
      setActiveTab(tab);

      // Update URL if router is ready
      if (router.isReady) {
        const newQuery = { ...router.query };

        await router.replace(
          {
            pathname: router.pathname,
            query: newQuery,
            hash: tab,
          },
          undefined,
          { shallow: true },
        );
      }
    },
    [router],
  );

  const filterTabs = [
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
  ];

  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { diff_status, system } = filterTabs.find(
    (tab) => tab.hash === activeTab,
  )!.params;
  const actionsDisabled = diff_status.includes(DiffStatus.MONITORED);

  const activeParams = systemId ? { diff_status, system } : { diff_status };

  return {
    filterTabs,
    activeTab,
    onTabChange,
    activeParams,
    actionsDisabled,
  };
};

export default useActionCenterTabs;
