import { useState } from "react";

import { IntegrationTypeInfo } from "~/features/integrations/add-integration/allIntegrationTypes";

export enum IntegrationFilterTabs {
  ALL = "All",
  DATABASE = "Database",
  DATA_WAREHOUSE = "Data Warehouse",
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

  const filteredTypes =
    integrationTypes?.filter(
      (i) =>
        currentTab === IntegrationFilterTabs.ALL ||
        (i.category as string) === (currentTab as string)
    ) ?? [];

  return {
    tabs,
    tabIndex,
    isFiltering,
    onChangeFilter,
    filteredTypes,
  };
};

export default useIntegrationFilterTabs;
