import { useRouter } from "next/router";
import { useCallback, useEffect, useState } from "react";

interface UseURLHashedTabsProps {
  tabKeys: string[];
  initialTab?: string;
}

const normalizeHash = (hash: string): string => {
  const normalizedHash = hash.startsWith("#") ? hash.slice(1) : hash;
  return normalizedHash;
};

const useURLHashedTabs = ({ tabKeys, initialTab }: UseURLHashedTabsProps) => {
  const router = useRouter();

  const initialKey = router.asPath.split("#")[1];

  // Default to the first tab if no hash is present
  const defaultTab = initialKey || tabKeys[0];
  const [activeTab, setActiveTab] = useState<string>(defaultTab);

  // Sync active tab with URL hash when router becomes ready
  useEffect(() => {
    if (router.isReady) {
      const hashFromURL = router.asPath.split("#")[1];
      if (hashFromURL && tabKeys.includes(hashFromURL)) {
        // Use hash from URL if valid
        setActiveTab(hashFromURL);
      } else if (initialTab && tabKeys.includes(initialTab)) {
        // Fall back to initialTab if no valid hash
        setActiveTab(initialTab);
      }
    }
  }, [initialTab, tabKeys, router.isReady, router.asPath]);

  const onTabChange = useCallback(
    async (tab: string) => {
      if (!tabKeys.includes(tab)) {
        await router.replace({
          pathname: router.pathname,
          query: router.query,
          hash: undefined,
        });
        setActiveTab(tabKeys[0]);
        return;
      }

      if (router.isReady) {
        await router.replace(
          {
            pathname: router.pathname,
            query: router.query,
            hash: normalizeHash(tab),
          },
          undefined,
          { shallow: true },
        );
        setActiveTab(tab);
      }
    },
    [router, tabKeys],
  );

  return { activeTab, onTabChange, setActiveTab };
};

export default useURLHashedTabs;
