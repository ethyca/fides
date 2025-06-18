import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";

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

  const availableTabs = useMemo(
    () => ({
      request: true,
      manualTask: flags.alphaNewManualDSR,
    }),
    [flags.alphaNewManualDSR],
  );

  const defaultTab = useMemo((): PrivacyRequestTabKey => {
    return flags.alphaNewManualDSR
      ? PRIVACY_REQUEST_TABS.MANUAL_TASK
      : PRIVACY_REQUEST_TABS.REQUEST;
  }, [flags.alphaNewManualDSR]);

  const parseHashFromUrl = useCallback(
    (url: string): PrivacyRequestTabKey | null => {
      const hashParts = url.split("#");
      if (hashParts.length < 2) {
        return null;
      }

      const hash = hashParts[1];
      const validTabs = Object.values(PRIVACY_REQUEST_TABS) as string[];

      return validTabs.includes(hash) ? (hash as PrivacyRequestTabKey) : null;
    },
    [],
  );

  const updateUrlHash = useCallback(
    (tabKey: PrivacyRequestTabKey) => {
      const newUrl = `${router.pathname}#${tabKey}`;
      router.replace(newUrl, undefined, { shallow: true });
    },
    [router],
  );

  useEffect(() => {
    if (!router.isReady) {
      return;
    }

    const hashTab = parseHashFromUrl(router.asPath);

    if (hashTab) {
      const isTabAvailable =
        hashTab === PRIVACY_REQUEST_TABS.REQUEST ||
        (hashTab === PRIVACY_REQUEST_TABS.MANUAL_TASK &&
          availableTabs.manualTask);

      if (isTabAvailable) {
        setActiveTab(hashTab);
        return;
      }
    }

    setActiveTab(defaultTab);
    updateUrlHash(defaultTab);
  }, [
    router.isReady,
    router.asPath,
    router.pathname,
    defaultTab,
    availableTabs,
    parseHashFromUrl,
    updateUrlHash,
  ]);

  const handleTabChange = useCallback(
    (tabKey: string) => {
      const validTabs = Object.values(PRIVACY_REQUEST_TABS) as string[];
      if (!validTabs.includes(tabKey)) {
        console.warn(`Invalid tab key: ${tabKey}`);
        return;
      }

      const typedTabKey = tabKey as PrivacyRequestTabKey;
      setActiveTab(typedTabKey);
      updateUrlHash(typedTabKey);
    },
    [updateUrlHash],
  );

  return {
    activeTab,
    handleTabChange,
    availableTabs,
    defaultTab,
  };
};
