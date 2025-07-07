import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";

export const PRIVACY_REQUEST_TABS = {
  REQUEST: "request",
  MANUAL_TASK: "manual-tasks",
} as const;

export type PrivacyRequestTabKey =
  (typeof PRIVACY_REQUEST_TABS)[keyof typeof PRIVACY_REQUEST_TABS];

export const usePrivacyRequestTabs = () => {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<PrivacyRequestTabKey>(
    PRIVACY_REQUEST_TABS.REQUEST,
  );

  const availableTabs = useMemo(
    () => ({
      request: true,
      manualTask: true,
    }),
    [],
  );

  const parseTabFromQuery = useCallback((): PrivacyRequestTabKey | null => {
    const { tab } = router.query;
    if (!tab || typeof tab !== "string") {
      return null;
    }

    const validTabs = Object.values(PRIVACY_REQUEST_TABS) as string[];
    return validTabs.includes(tab) ? (tab as PrivacyRequestTabKey) : null;
  }, [router.query]);

  const updateUrlTab = useCallback(
    (tabKey: PrivacyRequestTabKey) => {
      router.replace(
        {
          pathname: router.pathname,
          query: {
            ...router.query,
            tab: tabKey,
          },
        },
        undefined,
        {
          shallow: true,
        },
      );
    },
    [router],
  );

  useEffect(() => {
    const queryTab = parseTabFromQuery();

    if (queryTab) {
      const isTabAvailable =
        queryTab === PRIVACY_REQUEST_TABS.REQUEST ||
        (queryTab === PRIVACY_REQUEST_TABS.MANUAL_TASK &&
          availableTabs.manualTask);

      if (isTabAvailable) {
        setActiveTab(queryTab);
        return;
      }
    }

    setActiveTab(PRIVACY_REQUEST_TABS.REQUEST);
    updateUrlTab(PRIVACY_REQUEST_TABS.REQUEST);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleTabChange = useCallback(
    (tabKey: string) => {
      const validTabs = Object.values(PRIVACY_REQUEST_TABS) as string[];
      if (!validTabs.includes(tabKey)) {
        return;
      }

      const typedTabKey = tabKey as PrivacyRequestTabKey;
      setActiveTab(typedTabKey);
      updateUrlTab(typedTabKey);
    },
    [updateUrlTab],
  );

  return {
    activeTab,
    handleTabChange,
    availableTabs,
  };
};
