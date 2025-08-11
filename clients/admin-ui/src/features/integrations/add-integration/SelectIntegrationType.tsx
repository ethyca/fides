import { AntInput as Input, AntSelect as Select } from "fidesui";
import { useMemo, useState } from "react";

import { useFlags } from "~/features/common/features";
import FidesSpinner from "~/features/common/FidesSpinner";
import { useGetAllConnectionTypesQuery } from "~/features/connection-type";
import getIntegrationTypeInfo, {
  INTEGRATION_TYPE_LIST,
  IntegrationTypeInfo,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import SelectableIntegrationBox from "~/features/integrations/SelectableIntegrationBox";
import { getCategoryLabel } from "~/features/integrations/utils/categoryUtils";
import { ConnectionType } from "~/types/api";
import { ConnectionCategory } from "~/types/api/models/ConnectionCategory";

enum IntegrationCategoryFilter {
  ALL = "All",
  DATA_CATALOG = "DATA_CATALOG",
  DATA_WAREHOUSE = "DATA_WAREHOUSE",
  DATABASE = "DATABASE",
  IDENTITY_PROVIDER = "IDENTITY_PROVIDER",
  WEBSITE = "WEBSITE",
  CRM = "CRM",
  MANUAL = "MANUAL",
  MARKETING = "MARKETING",
  ANALYTICS = "ANALYTICS",
  ECOMMERCE = "ECOMMERCE",
  COMMUNICATION = "COMMUNICATION",
  CUSTOM = "CUSTOM",
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
    flags: { oktaMonitor },
  } = useFlags();

  // Fetch connection types for SAAS integration generation
  const { data: connectionTypesData } = useGetAllConnectionTypesQuery({});
  const connectionTypes = useMemo(
    () => connectionTypesData?.items || [],
    [connectionTypesData],
  );

  // Generate dynamic integration list including all SAAS integrations
  const allIntegrationTypes = useMemo(() => {
    const staticIntegrations = INTEGRATION_TYPE_LIST;

    // Generate SAAS integrations from connection types (excluding those already in static list)
    const existingSaasTypes = new Set(
      staticIntegrations
        .filter(
          (integration) =>
            integration.placeholder.connection_type === ConnectionType.SAAS,
        )
        .map((integration) => integration.placeholder.saas_config?.type),
    );

    const dynamicSaasIntegrations = connectionTypes
      .filter(
        (ct) => ct.type === "saas" && !existingSaasTypes.has(ct.identifier),
      )
      .map((ct) =>
        getIntegrationTypeInfo(
          ConnectionType.SAAS,
          ct.identifier,
          connectionTypes,
        ),
      );

    return [...staticIntegrations, ...dynamicSaasIntegrations];
  }, [connectionTypes]);

  // Get available categories based on flags
  const availableCategories = useMemo(() => {
    return Object.values(IntegrationCategoryFilter).filter(
      (tab) =>
        tab !== IntegrationCategoryFilter.IDENTITY_PROVIDER || oktaMonitor,
    );
  }, [oktaMonitor]);

  // Filter integrations based on search and category
  const filteredTypes = useMemo(() => {
    let filtered = allIntegrationTypes;

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
    filtered = filtered.filter((i) => {
      if (!oktaMonitor && i.placeholder.connection_type === "okta") {
        return false;
      }
      return true;
    });

    // Sort integrations alphabetically by display name
    return filtered.sort((a, b) => {
      const nameA = a.placeholder.name || "";
      const nameB = b.placeholder.name || "";
      return nameA.localeCompare(nameB);
    });
  }, [searchTerm, selectedCategory, oktaMonitor, allIntegrationTypes]);

  const handleCategoryChange = (value: IntegrationCategoryFilter) => {
    setIsFiltering(true);
    setSelectedCategory(value);
    setTimeout(() => setIsFiltering(false), 100);
  };

  const categoryOptions = availableCategories
    .map((category) => {
      if (category === IntegrationCategoryFilter.ALL) {
        return { label: category, value: category };
      }
      // Map filter enum values to ConnectionCategory enum values
      const connectionCategory = category as unknown as ConnectionCategory;
      return {
        label: getCategoryLabel(connectionCategory),
        value: category,
      };
    })
    .sort((a, b) => {
      // Keep "All" at the top, then sort alphabetically
      if (a.label === "All") {
        return -1;
      }
      if (b.label === "All") {
        return 1;
      }
      return a.label.localeCompare(b.label);
    });

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
                integrationTypeInfo={i}
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
