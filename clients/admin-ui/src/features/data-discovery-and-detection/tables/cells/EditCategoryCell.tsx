import {
  Box,
  ButtonProps,
  CloseIcon,
  EditIcon,
  IconButton,
  SmallAddIcon,
  Wrap,
} from "fidesui";
import { useCallback, useState } from "react";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { SparkleIcon } from "~/features/common/Icon/SparkleIcon";
import ClassificationCategoryBadge from "~/features/data-discovery-and-detection/ClassificationCategoryBadge";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";

import TaxonomySelectDropdown, {
  TaxonomySelectOption,
} from "../../../common/dropdown/TaxonomySelectDropdown";
import { useOutsideClick } from "../../../common/hooks";
import { useUpdateResourceCategoryMutation } from "../../discovery-detection.slice";

const AddCategoryButton = (props: ButtonProps) => (
  <IconButton
    variant="outline"
    w="20px"
    h="20px"
    minW="20px"
    borderRadius="sm"
    icon={<SmallAddIcon />}
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

  const handleClickOutside = useCallback(() => {
    setIsAdding(false);
  }, []);
  const { ref } = useOutsideClick(handleClickOutside);

  const bestClassifiedCategory = resource.classifications?.length
    ? resource.classifications[0].label
    : null;

  const userCategories = resource.user_assigned_data_categories ?? [];

  const noCategories = !bestClassifiedCategory && !userCategories?.length;

  const hasSubfields = resource.sub_field_urns?.length;

  const handleAddCategory = (option: TaxonomySelectOption) => {
    updateResourceCategoryMutation({
      staged_resource_urn: resource.urn,
      monitor_config_id: resource.monitor_config_id!,
      user_assigned_data_categories: [...userCategories, option.value],
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
      ref={ref}
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
              {getDataCategoryDisplayName(category)}
              <IconButton
                variant="ghost"
                onClick={() => handleRemoveCategory(category)}
                icon={<CloseIcon boxSize={2} />}
                size="2xs"
                ml={1}
                aria-label="Remove category"
              />
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
          <SparkleIcon mt={0.5} />
          {getDataCategoryDisplayName(bestClassifiedCategory)}
          <EditIcon />
        </ClassificationCategoryBadge>
      )}

      {isAdding && (
        <Box
          className="select-wrapper"
          position="absolute"
          zIndex={10}
          top="0"
          left="0"
          width="100%"
          height="max"
          bgColor="#fff"
        >
          <TaxonomySelectDropdown onChange={handleAddCategory} menuIsOpen />
        </Box>
      )}
    </Wrap>
  );
};
export default EditCategoriesCell;
