import { AntInput as Input, AntSelect as Select } from "fidesui";
import { useMemo, useState } from "react";

import { useFlags } from "~/features/common/features";
import FidesSpinner from "~/features/common/FidesSpinner";
import {
  INTEGRATION_TYPE_LIST,
  IntegrationTypeInfo,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import SelectableIntegrationBox from "~/features/integrations/SelectableIntegrationBox";

enum IntegrationCategoryFilter {
  ALL = "All",
  DATA_CATALOG = "Data Catalog",
  DATA_WAREHOUSE = "Data Warehouse",
  DATABASE = "Database",
  IDENTITY_PROVIDER = "Identity Provider",
  WEBSITE = "Website",
  CRM = "CRM",
  MANUAL = "Manual",
}

type Props = {
  selectedIntegration?: IntegrationTypeInfo;
  onSelectIntegration: (type: IntegrationTypeInfo | undefined) => void;
  onDetailClick: (type: IntegrationTypeInfo) => void;
};

const SelectIntegrationType = ({
  selectedIntegration,
  onSelectIntegration,
  onDetailClick,
}: Props) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] =
    useState<IntegrationCategoryFilter>(IntegrationCategoryFilter.ALL);
  const [isFiltering, setIsFiltering] = useState(false);

  const {
    flags: { oktaMonitor, alphaNewManualDSR },
  } = useFlags();

  // Get available categories based on flags
  const availableCategories = useMemo(() => {
    return Object.values(IntegrationCategoryFilter).filter(
      (tab) =>
        (tab !== IntegrationCategoryFilter.IDENTITY_PROVIDER || oktaMonitor) &&
        (tab !== IntegrationCategoryFilter.MANUAL || alphaNewManualDSR),
    );
  }, [oktaMonitor, alphaNewManualDSR]);

  // Filter integrations based on search and category
  const filteredTypes = useMemo(() => {
    let filtered = INTEGRATION_TYPE_LIST;

    // Filter by category
    if (selectedCategory !== IntegrationCategoryFilter.ALL) {
      filtered = filtered.filter(
        // @ts-ignore -- all non-ALL values of IntegrationCategoryFilter are
        // valid values for ConnectionCategory
        (i) => i.category === (selectedCategory as ConnectionCategory),
      );
    }

    // Filter by search term (name only)
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter((i) =>
        (i.placeholder.name || "").toLowerCase().includes(searchLower),
      );
    }

    // Apply flag-based filtering
    return filtered.filter((i) => {
      if (!oktaMonitor && i.placeholder.connection_type === "okta") {
        return false;
      }
      // DEFER (ENG-675): Remove this once the alpha feature is released
      if (
        !alphaNewManualDSR &&
        i.placeholder.connection_type === "manual_webhook"
      ) {
        return false;
      }
      return true;
    });
  }, [searchTerm, selectedCategory, oktaMonitor, alphaNewManualDSR]);

  const handleCategoryChange = (value: IntegrationCategoryFilter) => {
    setIsFiltering(true);
    setSelectedCategory(value);
    setTimeout(() => setIsFiltering(false), 100);
  };

  const categoryOptions = availableCategories.map((category) => ({
    label: category,
    value: category,
  }));

  return (
    <>
      <div className="mb-4 mt-3 flex items-center justify-between gap-4">
        <Input
          placeholder="Search by name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-64"
          allowClear
        />
        <Select
          value={selectedCategory}
          onChange={handleCategoryChange}
          options={categoryOptions}
          className="w-48"
          placeholder="Select category"
          data-testid="category-filter-select"
        />
      </div>

      {isFiltering ? (
        <FidesSpinner />
      ) : (
        <div className="grid grid-cols-3 gap-6">
          {filteredTypes.map((i) => (
            <div key={i.placeholder.key}>
              <SelectableIntegrationBox
                integration={i.placeholder}
                selected={
                  selectedIntegration?.placeholder.key === i.placeholder.key
                }
                onClick={() => {
                  // Toggle selection: if already selected, deselect; otherwise select
                  const isAlreadySelected =
                    selectedIntegration?.placeholder.key === i.placeholder.key;
                  onSelectIntegration(isAlreadySelected ? undefined : i);
                }}
                onDetailsClick={() => onDetailClick(i)}
                onUnfocus={() => onSelectIntegration(undefined)}
              />
            </div>
          ))}
        </div>
      )}
    </>
  );
};

export default SelectIntegrationType;
