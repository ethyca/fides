import {
  AntButton as Button,
  AntButtonProps as ButtonProps,
  Box,
  CloseIcon,
  EditIcon,
  SmallAddIcon,
  Wrap,
} from "fidesui";
import { useState } from "react";

import { TaxonomySelect } from "~/features/common/dropdown/TaxonomySelect";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { SparkleIcon } from "~/features/common/Icon/SparkleIcon";
import TaxonomyBadge from "~/features/data-discovery-and-detection/ClassificationCategoryBadge";
import TaxonomyAddButton from "~/features/data-discovery-and-detection/tables/cells/TaxonomyAddButton";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";

import { useUpdateResourceCategoryMutation } from "../../discovery-detection.slice";

interface EditCategoryCellProps {
  resource: DiscoveryMonitorItem;
}

const DeleteCategoryButton = ({ onClick }: { onClick: () => void }) => (
  <Button
    onClick={onClick}
    icon={<CloseIcon boxSize={2} mt={-0.5} />}
    size="small"
    type="text"
    className="ml-1 max-h-4 max-w-4"
    aria-label="Remove category"
  />
);

const EditCategoriesCell = ({ resource }: EditCategoryCellProps) => {
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
    <Wrap
      py={2}
      alignItems="center"
      position="relative"
      width="100%"
      gap={2}
      overflowX="auto"
    >
      {noCategories && (
        <>
          <TaxonomyBadge data-testid="no-classifications">None</TaxonomyBadge>
          {/* resources with child fields can't have data categories */}
          {!hasSubfields && (
            <TaxonomyAddButton onClick={() => setIsAdding(true)} />
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
          <TaxonomyAddButton onClick={() => setIsAdding(true)} />
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
          <TaxonomySelect
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
    </Wrap>
  );
};
export default EditCategoriesCell;
