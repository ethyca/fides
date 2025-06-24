import { AntInput as Input, AntSelect as Select } from "fidesui";
import { useMemo, useState } from "react";

import { useFlags } from "~/features/common/features";
import FidesSpinner from "~/features/common/FidesSpinner";
import {
  INTEGRATION_TYPE_LIST,
  IntegrationTypeInfo,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import SelectableIntegrationBox from "~/features/integrations/SelectableIntegrationBox";
import { IntegrationFilterTabHash } from "~/features/integrations/useIntegrationFilterTabs";

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
  const [selectedCategory, setSelectedCategory] = useState<string>(
    IntegrationFilterTabHash.ALL,
  );
  const [isFiltering, setIsFiltering] = useState(false);

  const {
    flags: { oktaMonitor, alphaNewManualIntegration },
  } = useFlags();

  // Get available categories based on flags
  const availableCategories = useMemo(() => {
    return Object.values(IntegrationFilterTabHash).filter(
      (tab) =>
        (tab !== IntegrationFilterTabHash.IDENTITY_PROVIDER || oktaMonitor) &&
        (tab !== IntegrationFilterTabHash.MANUAL || alphaNewManualIntegration),
    );
  }, [oktaMonitor, alphaNewManualIntegration]);

  // Filter integrations based on search and category
  const filteredTypes = useMemo(() => {
    let filtered = INTEGRATION_TYPE_LIST;

    // Filter by category
    if (selectedCategory !== IntegrationFilterTabHash.ALL) {
      filtered = filtered.filter((i) => i.category === selectedCategory);
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
        !alphaNewManualIntegration &&
        i.placeholder.connection_type === "manual_webhook"
      ) {
        return false;
      }
      return true;
    });
  }, [searchTerm, selectedCategory, oktaMonitor, alphaNewManualIntegration]);

  const handleCategoryChange = (value: string) => {
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
