import { useRouter } from "next/router";
import { useState } from "react";

import { useFlags } from "~/features/common/features/features.slice";
import { IntegrationTypeInfo } from "~/features/integrations/add-integration/allIntegrationTypes";

enum IntegrationFilterTabHash {
  ALL = "all",
  CRM = "crm",
  DATABASE = "database",
  DATA_CATALOG = "data-catalog",
  DATA_WAREHOUSE = "data-warehouse",
  IDENTITY_PROVIDER = "identity-provider",
  WEBSITE = "website",
  MANUAL = "manual",
}

const TAB_HASHES = Object.values(IntegrationFilterTabHash);

const TAB_HASH_LABEL_MAP: Record<IntegrationFilterTabHash, string> = {
  [IntegrationFilterTabHash.ALL]: "All",
  [IntegrationFilterTabHash.CRM]: "CRM",
  [IntegrationFilterTabHash.DATABASE]: "Database",
  [IntegrationFilterTabHash.DATA_CATALOG]: "Data Catalog",
  [IntegrationFilterTabHash.DATA_WAREHOUSE]: "Data Warehouse",
  [IntegrationFilterTabHash.IDENTITY_PROVIDER]: "Identity Provider",
  [IntegrationFilterTabHash.WEBSITE]: "Website",
  [IntegrationFilterTabHash.MANUAL]: "Manual",
};

const CHANGE_FILTER_DELAY = 300;

interface UseIntegrationFilterTabsProps {
  integrationTypes?: IntegrationTypeInfo[];
  useHashing?: boolean;
}

const useIntegrationFilterTabs = ({
  integrationTypes,
  useHashing,
}: UseIntegrationFilterTabsProps) => {
  const router = useRouter();
  const initialHash = router.asPath.split("#")[1] as IntegrationFilterTabHash;
  const initialTab = TAB_HASHES.includes(initialHash)
    ? initialHash
    : IntegrationFilterTabHash.ALL;

  const { flags } = useFlags();
  const tabItems = TAB_HASHES.filter(
    (tab) =>
      (tab !== IntegrationFilterTabHash.IDENTITY_PROVIDER ||
        flags.oktaMonitor) &&
      (tab !== IntegrationFilterTabHash.MANUAL ||
        flags.alphaNewManualIntegration), // DEFER (ENG-675): Remove this once the alpha feature is released
  ).map((t) => ({
    key: t,
    label: TAB_HASH_LABEL_MAP[t],
  }));

  const [activeKey, setActiveKey] = useState<IntegrationFilterTabHash>(
    initialTab ?? IntegrationFilterTabHash.ALL,
  );

  const [isUpdatingFilter, setIsUpdatingFilter] = useState(false);

  const onChangeFilter = async (newKey: string) => {
    setIsUpdatingFilter(true);

    if (router.isReady && useHashing) {
      await router.replace(
        {
          pathname: router.pathname,
          query: { ...router.query },
          hash: newKey,
        },
        undefined,
        { shallow: true },
      );
    }

    setActiveKey(newKey as IntegrationFilterTabHash);
    setTimeout(() => setIsUpdatingFilter(false), CHANGE_FILTER_DELAY);
  };

  const anyFiltersApplied = activeKey !== IntegrationFilterTabHash.ALL;

  const filteredTypes =
    integrationTypes?.filter(
      (i) =>
        !anyFiltersApplied ||
        (i.category as string) === TAB_HASH_LABEL_MAP[activeKey],
    ) ?? [];

  return {
    tabItems,
    activeKey,
    anyFiltersApplied,
    isUpdatingFilter,
    onChangeFilter,
    filteredTypes,
  };
};

export default useIntegrationFilterTabs;
