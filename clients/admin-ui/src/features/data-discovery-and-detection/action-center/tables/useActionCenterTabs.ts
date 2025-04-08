import { useRouter } from "next/router";
import { useCallback, useState } from "react";

import { DiffStatus } from "~/types/api";

const ACTION_CENTER_TABLE_TABS = {
  ATTENTION_REQUIRED: {
    index: 0,
    hash: "#attention-required",
  },
  RECENT_ACTIVITY: {
    index: 1,
    hash: "#recent-activity",
  },
  IGNORED: {
    index: 2,
    hash: "#ignored",
  },
};

const getTabFromHash = (hash: string) => {
  const normalizedHash = hash.startsWith("#") ? hash : `#${hash}`;
  return Object.values(ACTION_CENTER_TABLE_TABS).find(
    (tab) => tab.hash === normalizedHash,
  );
};

const getTabFromIndex = (index: number) => {
  return Object.values(ACTION_CENTER_TABLE_TABS).find(
    (tab) => tab.index === index,
  );
};

const useActionCenterTabs = ({
  systemId,
  initialHash,
}: {
  systemId?: string;
  initialHash?: string;
}) => {
  const router = useRouter();
  const getInitialTabIndex = () => {
    return initialHash
      ? getTabFromHash(initialHash)?.index
      : ACTION_CENTER_TABLE_TABS.ATTENTION_REQUIRED.index;
  };

  const [filterTabIndex, setFilterTabIndex] = useState(getInitialTabIndex());

  const onTabChange = useCallback(
    async (index: number) => {
      // Update local state first
      setFilterTabIndex(index);

      // Update URL if router is ready
      if (router.isReady) {
        const tab = getTabFromIndex(index);
        if (tab) {
          const newQuery = { ...router.query };

          await router.replace(
            {
              pathname: router.pathname,
              query: newQuery,
              hash: tab.hash,
            },
            undefined,
            { shallow: true },
          );
        }
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
    },
    {
      label: "Recent activity",
      params: {
        diff_status: [DiffStatus.MONITORED],
      },
    },
    {
      label: "Ignored",
      params: {
        diff_status: [DiffStatus.MUTED],
        system: systemId,
      },
    },
  ];

  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { diff_status, system } = filterTabs[filterTabIndex!].params;
  const actionsDisabled = diff_status.includes(DiffStatus.MONITORED);

  const activeParams = systemId ? { diff_status, system } : { diff_status };

  return {
    filterTabs,
    filterTabIndex,
    onTabChange,
    activeParams,
    actionsDisabled,
  };
};

export default useActionCenterTabs;
