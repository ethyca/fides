import { useState } from "react";

import { useFlags } from "~/features/common/features/features.slice";
import { IntegrationTypeInfo } from "~/features/integrations/add-integration/allIntegrationTypes";

export enum IntegrationFilterTabLabel {
  ALL = "All",
  DATABASE = "Database",
  DATA_CATALOG = "Data Catalog",
  DATA_WAREHOUSE = "Data Warehouse",
  IDENTITY_PROVIDER = "Identity Provider",
  WEBSITE = "Website",
  MANUAL = "Manual",
}

const CHANGE_FILTER_DELAY = 300;

const useIntegrationFilterTabs = (integrationTypes?: IntegrationTypeInfo[]) => {
  const { flags } = useFlags();
  const tabItems = Object.values(IntegrationFilterTabLabel)
    .filter(
      (tab) =>
        (tab !== IntegrationFilterTabLabel.IDENTITY_PROVIDER ||
          flags.oktaMonitor) &&
        (tab !== IntegrationFilterTabLabel.MANUAL ||
          flags.alphaNewManualIntegration), // DEFER (ENG-675): Remove this once the alpha feature is released
    )
    .map((t) => ({
      key: t,
      label: t,
    }));

  const [activeKey, setActiveKey] = useState(IntegrationFilterTabLabel.ALL);

  const [isUpdatingFilter, setIsUpdatingFilter] = useState(false);

  const onChangeFilter = (newKey: string) => {
    setIsUpdatingFilter(true);
    setActiveKey(newKey as IntegrationFilterTabLabel);
    setTimeout(() => setIsUpdatingFilter(false), CHANGE_FILTER_DELAY);
  };

  const anyFiltersApplied = activeKey !== IntegrationFilterTabLabel.ALL;

  const filteredTypes =
    integrationTypes?.filter(
      (i) =>
        !anyFiltersApplied || (i.category as string) === (activeKey as string),
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
