import { useRouter } from "next/router";
import { useCallback, useEffect, useState } from "react";

import { useFlags } from "~/features/common/features";

export const PRIVACY_REQUEST_TABS = {
  REQUEST: "request",
  MANUAL_TASK: "manual-task",
} as const;

export type PrivacyRequestTabKey =
  (typeof PRIVACY_REQUEST_TABS)[keyof typeof PRIVACY_REQUEST_TABS];

export const usePrivacyRequestTabs = () => {
  const router = useRouter();
  const { flags } = useFlags();
  const [activeTab, setActiveTab] = useState<PrivacyRequestTabKey>(
    PRIVACY_REQUEST_TABS.REQUEST,
  );

  // Determine default tab based on flag
  const getDefaultTab = useCallback((): PrivacyRequestTabKey => {
    if (flags.alphaNewManualDSR) {
      return PRIVACY_REQUEST_TABS.MANUAL_TASK;
    }
    return PRIVACY_REQUEST_TABS.REQUEST;
  }, [flags.alphaNewManualDSR]);

  // Initialize tab from URL hash or default
  useEffect(() => {
    if (router.isReady) {
      const hash = router.asPath.split("#")[1];
      if (
        hash &&
        Object.values(PRIVACY_REQUEST_TABS).includes(
          hash as PrivacyRequestTabKey,
        )
      ) {
        setActiveTab(hash as PrivacyRequestTabKey);
      } else {
        const defaultTab = getDefaultTab();
        setActiveTab(defaultTab);
        // Update URL with default tab
        router.replace(`${router.pathname}#${defaultTab}`, undefined, {
          shallow: true,
        });
      }
    }
  }, [router.isReady, router.pathname, router.asPath, getDefaultTab]);

  // Update URL when tab changes
  const handleTabChange = useCallback(
    (tabKey: PrivacyRequestTabKey) => {
      setActiveTab(tabKey);
      router.replace(`${router.pathname}#${tabKey}`, undefined, {
        shallow: true,
      });
    },
    [router],
  );

  return {
    activeTab,
    handleTabChange,
    availableTabs: {
      request: true,
      manualTask: flags.alphaNewManualDSR,
    },
  };
};
