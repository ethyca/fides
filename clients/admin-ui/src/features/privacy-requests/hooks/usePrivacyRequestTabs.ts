import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useHasPermission } from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

export const PRIVACY_REQUEST_TABS = {
  REQUEST: "request",
  MANUAL_TASK: "manual-tasks",
} as const;

export type PrivacyRequestTabKey =
  (typeof PRIVACY_REQUEST_TABS)[keyof typeof PRIVACY_REQUEST_TABS];

export const usePrivacyRequestTabs = () => {
  const router = useRouter();

  const hasPrivacyRequestReadScope = useHasPermission([
    ScopeRegistryEnum.PRIVACY_REQUEST_READ,
  ]);
  const hasManualTaskReadScope = useHasPermission([
    ScopeRegistryEnum.MANUAL_FIELD_READ_OWN,
    ScopeRegistryEnum.MANUAL_FIELD_READ_ALL,
  ]);
  const availableTabs = useMemo(
    () => ({
      request: hasPrivacyRequestReadScope,
      manualTask: hasManualTaskReadScope,
    }),
    [hasPrivacyRequestReadScope, hasManualTaskReadScope],
  );
  const [activeTab, setActiveTab] = useState<PrivacyRequestTabKey>(
    availableTabs.request
      ? PRIVACY_REQUEST_TABS.REQUEST
      : PRIVACY_REQUEST_TABS.MANUAL_TASK,
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
    // Ensure the router is ready before reading query params to avoid initial undefined values
    if (!router.isReady) {
      return;
    }

    const queryTab = parseTabFromQuery();

    if (queryTab) {
      const isTabAvailable =
        queryTab === PRIVACY_REQUEST_TABS.REQUEST ||
        (queryTab === PRIVACY_REQUEST_TABS.MANUAL_TASK &&
          availableTabs.manualTask);

      if (isTabAvailable) {
        setActiveTab(queryTab);
      }
    }
  }, [
    router.isReady,
    router.query,
    availableTabs,
    parseTabFromQuery,
    updateUrlTab,
  ]);

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
