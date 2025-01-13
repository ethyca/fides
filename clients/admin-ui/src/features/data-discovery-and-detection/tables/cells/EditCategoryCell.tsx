import {
  AntButton as Button,
  AntButtonProps as ButtonProps,
  Box,
  CloseIcon,
  EditIcon,
  SmallAddIcon,
  Text,
  Wrap,
} from "fidesui";
import { useState } from "react";

import { TaxonomySelect } from "~/features/common/dropdown/TaxonomySelect";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { SparkleIcon } from "~/features/common/Icon/SparkleIcon";
import ClassificationCategoryBadge from "~/features/data-discovery-and-detection/ClassificationCategoryBadge";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";

import { useUpdateResourceCategoryMutation } from "../../discovery-detection.slice";

const AddCategoryButton = (props: ButtonProps) => (
  <Button
    size="small"
    icon={<SmallAddIcon mb="1px" />}
    className="max-h-[20px] max-w-[20px]  border-gray-200 bg-white"
    data-testid="add-category-btn"
    aria-label="Add category"
    {...props}
  />
);

interface EditCategoryCellProps {
  resource: DiscoveryMonitorItem;
}

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
          <ClassificationCategoryBadge data-testid="no-classifications">
            None
          </ClassificationCategoryBadge>
          {/* resources with child fields can't have data categories */}
          {!hasSubfields && (
            <AddCategoryButton onClick={() => setIsAdding(true)} />
          )}
        </>
      )}

      {showUserCategories && (
        <>
          {userCategories.map((category) => (
            <ClassificationCategoryBadge
              classification={getDataCategoryDisplayName(category)}
              key={category}
              data-testid={`user-classification-${category}`}
            >
              <div className="flex items-center gap-1.5">
                <Text>{getDataCategoryDisplayName(category)}</Text>
                <Button
                  onClick={() => handleRemoveCategory(category)}
                  icon={<CloseIcon boxSize={2} mt={-0.5} />}
                  size="small"
                  type="text"
                  className="ml-1 max-h-4 max-w-4"
                  aria-label="Remove category"
                />
              </div>
            </ClassificationCategoryBadge>
          ))}
          <AddCategoryButton onClick={() => setIsAdding(true)} />
        </>
      )}

      {showClassificationResult && (
        <ClassificationCategoryBadge
          onClick={() => setIsAdding(true)}
          cursor="pointer"
          data-testid={`classification-${bestClassifiedCategory}`}
        >
          <div className="flex items-center gap-1.5">
            <SparkleIcon mt={0.5} />
            {getDataCategoryDisplayName(bestClassifiedCategory)}
            <EditIcon />
          </div>
        </ClassificationCategoryBadge>
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
