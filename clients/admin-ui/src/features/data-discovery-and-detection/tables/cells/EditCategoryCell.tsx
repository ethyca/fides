import { AntButton as Button, Box, CloseIcon, EditIcon } from "fidesui";
import { useState } from "react";

import DataCategorySelect from "~/features/common/dropdown/DataCategorySelect";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { SparkleIcon } from "~/features/common/Icon/SparkleIcon";
import TaxonomyAddButton from "~/features/data-discovery-and-detection/tables/cells/TaxonomyAddButton";
import TaxonomyCellContainer from "~/features/data-discovery-and-detection/tables/cells/TaxonomyCellContainer";
import TaxonomyBadge from "~/features/data-discovery-and-detection/TaxonomyBadge";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";

import { useUpdateResourceCategoryMutation } from "../../discovery-detection.slice";

interface EditCategoryCellProps {
  resource: DiscoveryMonitorItem;
}

const DeleteCategoryButton = ({ onClick }: { onClick: () => void }) => (
  <Button
    onClick={onClick}
    icon={<CloseIcon boxSize={2} />}
    size="small"
    type="text"
    className="max-h-4 max-w-4"
    aria-label="Remove category"
  />
);

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
    <TaxonomyCellContainer>
      {noCategories && (
        <>
          <TaxonomyBadge data-testid="no-classifications">None</TaxonomyBadge>
          {/* resources with child fields can't have data categories */}
          {!hasSubfields && (
            <TaxonomyAddButton
              onClick={() => setIsAdding(true)}
              aria-label="Add category"
            />
          )}
        </>
      )}

      {showUserCategories && (
        <>
          {userCategories.map((category) => (
            <TaxonomyBadge
              key={category}
              data-testid={`user-classification-${category}`}
              closeButton={
                <DeleteCategoryButton
                  onClick={() => handleRemoveCategory(category)}
                />
              }
            >
              {getDataCategoryDisplayName(category)}
            </TaxonomyBadge>
          ))}
          <TaxonomyAddButton
            onClick={() => setIsAdding(true)}
            aria-label="Add category"
          />
        </>
      )}

      {showClassificationResult && (
        <TaxonomyBadge
          onClick={() => setIsAdding(true)}
          cursor="pointer"
          data-testid={`classification-${bestClassifiedCategory}`}
        >
          <SparkleIcon mt={0.5} />
          {getDataCategoryDisplayName(bestClassifiedCategory)}
          <EditIcon />
        </TaxonomyBadge>
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
