import { useState } from "react";

import { IntegrationTypeInfo } from "~/features/integrations/add-integration/allIntegrationTypes";

export enum IntegrationFilterTabs {
  ALL = "All",
  DATABASE = "Database",
  DATA_CATALOG = "Data Catalog",
  DATA_WAREHOUSE = "Data Warehouse",
  WEBSITE = "Website",
}

const useIntegrationFilterTabs = (integrationTypes?: IntegrationTypeInfo[]) => {
  const tabs = Object.values(IntegrationFilterTabs);

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
