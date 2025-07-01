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

  console.log(initialKey);

  const [activeTab, setActiveTab] = useState<string>(initialKey);

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
        setActiveTab(tabKeys[0]);
        await router.replace({
          pathname: router.pathname,
          query: router.query,
          hash: undefined,
        });
        return;
      }

      setActiveTab(tab);
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
      }
    },
    [router, tabKeys],
  );

  return { activeTab, onTabChange };
};

export default useURLHashedTabs;
