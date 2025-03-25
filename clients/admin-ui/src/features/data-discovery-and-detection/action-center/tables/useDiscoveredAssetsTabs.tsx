import { useRouter } from "next/router";
import { useCallback, useState } from "react";

import { DiffStatus } from "~/types/api";

const DISCOVERED_ASSETS_TABLE_TABS = {
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
  return Object.values(DISCOVERED_ASSETS_TABLE_TABS).find(
    (tab) => tab.hash === normalizedHash,
  );
};

const getTabFromIndex = (index: number) => {
  return Object.values(DISCOVERED_ASSETS_TABLE_TABS).find(
    (tab) => tab.index === index,
  );
};

export const useDiscoveredAssetsTabs = ({ systemId }: { systemId: string }) => {
  const router = useRouter();
  const getInitialTabIndex = () => {
    const hash: string = router.asPath.split("#")[1];
    return hash
      ? getTabFromHash(hash)?.index
      : DISCOVERED_ASSETS_TABLE_TABS.ATTENTION_REQUIRED.index;
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

  return {
    filterTabs,
    filterTabIndex,
    onTabChange,
    activeParams: filterTabs[filterTabIndex!].params,
  };
};

export default useDiscoveredAssetsTabs;
