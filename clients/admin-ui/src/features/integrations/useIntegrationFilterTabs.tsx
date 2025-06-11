import { useState } from "react";

import { useFlags } from "~/features/common/features/features.slice";
import { IntegrationTypeInfo } from "~/features/integrations/add-integration/allIntegrationTypes";

export enum IntegrationFilterTabs {
  ALL = "All",
  CRM = "CRM",
  DATA_CATALOG = "Data Catalog",
  DATABASE = "Database",
  DATA_WAREHOUSE = "Data Warehouse",
  IDENTITY_PROVIDER = "Identity Provider",
  WEBSITE = "Website",
  MANUAL = "Manual",
}

const useIntegrationFilterTabs = (integrationTypes?: IntegrationTypeInfo[]) => {
  const { flags } = useFlags();
  const tabs = Object.values(IntegrationFilterTabs).filter(
    (tab) =>
      (tab !== IntegrationFilterTabs.IDENTITY_PROVIDER || flags.oktaMonitor) &&
      (tab !== IntegrationFilterTabs.MANUAL || flags.alphaNewManualIntegration), // DEFER (ENG-675): Remove this once the alpha feature is released
  );

  const [tabIndex, setTabIndex] = useState(0);
  const currentTab = tabs[tabIndex];

  const [isFiltering, setIsFiltering] = useState(false);

  const onChangeFilter = (newIndex: number) => {
    setIsFiltering(true);
    setTabIndex(newIndex);
    setTimeout(() => setIsFiltering(false), 100);
  };

  const anyFiltersApplied = currentTab !== IntegrationFilterTabs.ALL;

  const filteredTypes =
    integrationTypes?.filter(
      (i) =>
        !anyFiltersApplied || (i.category as string) === (currentTab as string),
    ) ?? [];

  return {
    tabs,
    tabIndex,
    anyFiltersApplied,
    isFiltering,
    onChangeFilter,
    filteredTypes,
  };
};

export default useIntegrationFilterTabs;
