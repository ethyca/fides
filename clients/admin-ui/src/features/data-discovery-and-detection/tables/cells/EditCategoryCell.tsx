import { AntTag as Tag, Box, Icons } from "fidesui";
import { useState } from "react";

import DataCategorySelect from "~/features/common/dropdown/DataCategorySelect";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import TaxonomyCellContainer from "~/features/data-discovery-and-detection/tables/cells/TaxonomyCellContainer";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";

import { useUpdateResourceCategoryMutation } from "../../discovery-detection.slice";

interface EditCategoryCellProps {
  resource: DiscoveryMonitorItem;
}

const EditCategoryCell = ({ resource }: EditCategoryCellProps) => {
  const [isAdding, setIsAdding] = useState(false);
  const { getDataCategoryDisplayName } = useTaxonomies();
  const [updateResourceCategoryMutation] = useUpdateResourceCategoryMutation();

  const bestClassifiedCategory = resource.classifications?.length
    ? resource.classifications[0].label
    : null;

  const userCategories = resource.user_assigned_data_categories ?? [];

  const noCategories = !bestClassifiedCategory && !userCategories?.length;

  const hasSubfields = resource.sub_field_urns?.length;

  const handleAddCategory = (value: string) => {
    updateResourceCategoryMutation({
      staged_resource_urn: resource.urn,
      monitor_config_id: resource.monitor_config_id!,
      user_assigned_data_categories: [...userCategories, value],
    });
  };

  const handleRemoveCategory = (category: string) => {
    updateResourceCategoryMutation({
      staged_resource_urn: resource.urn,
      monitor_config_id: resource.monitor_config_id!,
      user_assigned_data_categories:
        userCategories?.filter((c) => c !== category) ?? [],
    });
  };

  const showUserCategories = !isAdding && !!userCategories.length;

  const showClassificationResult =
    !isAdding && !!bestClassifiedCategory && !userCategories.length;

  return (
    <TaxonomyCellContainer data-testid="edit-category-cell">
      {noCategories && (
        <>
          <Tag data-testid="no-classifications" color="white">
            None
          </Tag>
          {/* resources with child fields can't have data categories */}
          {!hasSubfields && (
            <Tag
              onClick={() => setIsAdding(true)}
              addable
              data-testid="taxonomy-add-btn"
              aria-label="Add category"
            />
          )}
        </>
      )}

      {showUserCategories && (
        <>
          {userCategories.map((category) => (
            <Tag
              key={category}
              data-testid={`user-classification-${category}`}
              color="white"
              closable
              onClose={() => handleRemoveCategory(category)}
              closeButtonLabel="Remove category"
            >
              {getDataCategoryDisplayName(category)}
            </Tag>
          ))}
          <Tag
            onClick={() => setIsAdding(true)}
            addable
            data-testid="taxonomy-add-btn"
            aria-label="Add category"
          />
        </>
      )}

      {showClassificationResult && (
        <Tag
          onClick={() => setIsAdding(true)}
          color="white"
          data-testid={`classification-${bestClassifiedCategory}`}
          hasSparkle
        >
          {getDataCategoryDisplayName(bestClassifiedCategory)}
          <Icons.Edit size={10} />
        </Tag>
      )}

      {isAdding && (
        <Box
          // eslint-disable-next-line tailwindcss/no-custom-classname
          className="select-wrapper"
          position="absolute"
          zIndex={10}
          top="0"
          left="0"
          width="100%"
          height="max"
          bgColor="#fff"
        >
          <DataCategorySelect
            selectedTaxonomies={userCategories}
            onChange={(o) => {
              setIsAdding(false);
              handleAddCategory(o);
            }}
            onBlur={() => setIsAdding(false)}
            open
          />
        </Box>
      )}
    </TaxonomyCellContainer>
  );
};
export default EditCategoryCell;
