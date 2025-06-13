import {
  AntButton as Button,
  AntInput as Input,
  AntSelect as Select,
  Flex,
  Spacer,
} from "fidesui";
import { useMemo, useState } from "react";

import { useFlags } from "~/features/common/features";
import FidesSpinner from "~/features/common/FidesSpinner";
import {
  INTEGRATION_TYPE_LIST,
  IntegrationTypeInfo,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import IntegrationBox from "~/features/integrations/IntegrationBox";
import { IntegrationFilterTabs } from "~/features/integrations/useIntegrationFilterTabs";

type Props = {
  onCancel: () => void;
  onDetailClick: (type: IntegrationTypeInfo) => void;
};

const SelectIntegrationType = ({ onCancel, onDetailClick }: Props) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>(
    IntegrationFilterTabs.ALL,
  );
  const [isFiltering, setIsFiltering] = useState(false);

  const {
    flags: { oktaMonitor, alphaNewManualIntegration },
  } = useFlags();

  // Get available categories based on flags
  const availableCategories = useMemo(() => {
    return Object.values(IntegrationFilterTabs).filter(
      (tab) =>
        (tab !== IntegrationFilterTabs.IDENTITY_PROVIDER || oktaMonitor) &&
        (tab !== IntegrationFilterTabs.MANUAL || alphaNewManualIntegration),
    );
  }, [oktaMonitor, alphaNewManualIntegration]);

  // Filter integrations based on search and category
  const filteredTypes = useMemo(() => {
    let filtered = INTEGRATION_TYPE_LIST;

    // Filter by category
    if (selectedCategory !== IntegrationFilterTabs.ALL) {
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
      <div className="mb-4 flex items-center justify-between gap-4">
        <Input.Search
          placeholder="Search by name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onSearch={setSearchTerm}
          className="w-64"
          allowClear
          enterButton
        />
        <Select
          value={selectedCategory}
          onChange={handleCategoryChange}
          options={categoryOptions}
          className="w-48"
          placeholder="Select category"
        />
      </div>

      {isFiltering ? (
        <FidesSpinner />
      ) : (
        <div className="grid grid-cols-3 gap-6">
          {filteredTypes.map((i) => (
            <IntegrationBox
              integration={i.placeholder}
              key={i.placeholder.key}
              otherButtons={
                <Button onClick={() => onDetailClick(i)}>Details</Button>
              }
            />
          ))}
        </div>
      )}
      <Flex>
        <Spacer />
        <Button onClick={onCancel}>Cancel</Button>
      </Flex>
    </>
  );
};

export default SelectIntegrationType;
