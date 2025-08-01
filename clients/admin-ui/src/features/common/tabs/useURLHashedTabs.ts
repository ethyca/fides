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

  // needed to prevent a race condition on some pages where activeTab is set
  // before the router is ready
  useEffect(() => {
    if (initialTab && tabKeys.includes(initialTab)) {
      setActiveTab(initialTab);
    }
  }, [initialTab, tabKeys, router.isReady]);

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

  return { activeTab, onTabChange };
};

export default useURLHashedTabs;
