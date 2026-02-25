import { Flex, Input, PageSpinner, Select } from "fidesui";
import { ReactNode, useMemo, useState } from "react";

import { useFlags } from "~/features/common/features";
import { useGetAllConnectionTypesQuery } from "~/features/connection-type";
import getIntegrationTypeInfo, {
  INTEGRATION_TYPE_LIST,
  IntegrationTypeInfo,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import SelectableIntegrationBox from "~/features/integrations/SelectableIntegrationBox";
import { getCategoryLabel } from "~/features/integrations/utils/categoryUtils";
import { ConnectionType } from "~/types/api";
import { ConnectionCategory } from "~/types/api/models/ConnectionCategory";

type IntegrationCategoryFilter = ConnectionCategory | "ALL";

export const useIntegrationFilters = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] =
    useState<IntegrationCategoryFilter>("ALL");
  const [isFiltering, setIsFiltering] = useState(false);

  const {
    flags: { newIntegrationManagement, webMonitor },
  } = useFlags();

  const { data: connectionTypesData } = useGetAllConnectionTypesQuery({});
  const connectionTypes = useMemo(
    () => connectionTypesData?.items || [],
    [connectionTypesData],
  );

  const allIntegrationTypes = useMemo(() => {
    let staticIntegrations = INTEGRATION_TYPE_LIST;

    if (!newIntegrationManagement) {
      staticIntegrations = staticIntegrations.filter(
        (integration) =>
          integration.placeholder.connection_type !== ConnectionType.SAAS,
      );
    }

    const existingSaasTypes = new Set(
      staticIntegrations
        .filter(
          (integration) =>
            integration.placeholder.connection_type === ConnectionType.SAAS,
        )
        .map((integration) => integration.placeholder.saas_config?.type),
    );

    const dynamicSaasIntegrations = newIntegrationManagement
      ? connectionTypes
          .filter(
            (ct) => ct.type === "saas" && !existingSaasTypes.has(ct.identifier),
          )
          .map((ct) =>
            getIntegrationTypeInfo(
              ConnectionType.SAAS,
              ct.identifier,
              connectionTypes,
            ),
          )
      : [];

    return [...staticIntegrations, ...dynamicSaasIntegrations];
  }, [connectionTypes, newIntegrationManagement]);

  const availableCategories = useMemo(() => {
    const allCategories: IntegrationCategoryFilter[] = [
      "ALL",
      ...Object.values(ConnectionCategory).filter(
        (category) => !!webMonitor || category !== ConnectionCategory.WEBSITE,
      ),
    ];

    if (!newIntegrationManagement) {
      return allCategories.filter((category) => {
        if (category === "ALL") {
          return allIntegrationTypes.length > 0;
        }
        return allIntegrationTypes.some(
          (integration) => integration.category === category,
        );
      });
    }

    return allCategories;
  }, [newIntegrationManagement, webMonitor, allIntegrationTypes]);

  const filteredTypes = useMemo(() => {
    let filtered = allIntegrationTypes;

    if (selectedCategory !== "ALL") {
      filtered = filtered.filter((i) => i.category === selectedCategory);
    }

    if (!webMonitor) {
      filtered = filtered.filter(
        (i) => i.category !== ConnectionCategory.WEBSITE,
      );
    }

    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter((i) =>
        (i.placeholder.name || "").toLowerCase().includes(searchLower),
      );
    }

    return filtered.sort((a, b) => {
      const nameA = a.placeholder.name || "";
      const nameB = b.placeholder.name || "";
      return nameA.localeCompare(nameB);
    });
  }, [searchTerm, selectedCategory, webMonitor, allIntegrationTypes]);

  const handleCategoryChange = (value: IntegrationCategoryFilter) => {
    setIsFiltering(true);
    setSelectedCategory(value);
    setTimeout(() => setIsFiltering(false), 100);
  };

  const categoryOptions = availableCategories
    .map((category) => {
      if (category === "ALL") {
        return { label: "All", value: category };
      }
      return {
        label: getCategoryLabel(category),
        value: category,
      };
    })
    .sort((a, b) => {
      if (a.label === "All") {
        return -1;
      }
      if (b.label === "All") {
        return 1;
      }
      return a.label.localeCompare(b.label);
    });

  const filterBar: ReactNode = (
    <Flex align="center" justify="space-between" gap={16}>
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
        aria-label="Select a category"
        data-testid="category-filter-select"
      />
    </Flex>
  );

  return { filterBar, filteredTypes, isFiltering };
};

type Props = {
  filteredTypes: IntegrationTypeInfo[];
  isFiltering: boolean;
  onIntegrationClick: (type: IntegrationTypeInfo) => void;
  onDetailClick: (type: IntegrationTypeInfo) => void;
};

const SelectIntegrationType = ({
  filteredTypes,
  isFiltering,
  onIntegrationClick,
  onDetailClick,
}: Props) =>
  isFiltering ? (
    <PageSpinner />
  ) : (
    <div className="grid grid-cols-3 gap-6">
      {filteredTypes.map((i) => (
        <div key={i.placeholder.key}>
          <SelectableIntegrationBox
            integration={i.placeholder}
            integrationTypeInfo={i}
            onClick={() => onIntegrationClick(i)}
            onDetailsClick={() => onDetailClick(i)}
          />
        </div>
      ))}
    </div>
  );

export default SelectIntegrationType;
