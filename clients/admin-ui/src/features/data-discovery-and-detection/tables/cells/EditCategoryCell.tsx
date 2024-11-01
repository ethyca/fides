import {
  AntButton as Button,
  AntButtonProps as ButtonProps,
  Box,
  CloseIcon,
  EditIcon,
  SmallAddIcon,
} from "fidesui";
import { useCallback, useState } from "react";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { SparkleIcon } from "~/features/common/Icon/SparkleIcon";
import TaxonomyBadge from "~/features/data-discovery-and-detection/ClassificationCategoryBadge";
import TaxonomyAddButton from "~/features/data-discovery-and-detection/tables/cells/TaxonomyAddButton";
import TaxonomyCellContainer from "~/features/data-discovery-and-detection/tables/cells/TaxonomyCellContainer";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";

import DataCategorySelect, {
  TaxonomySelectOption,
} from "../../../common/dropdown/DataCategorySelect";
import { useOutsideClick } from "../../../common/hooks";
import { useUpdateResourceCategoryMutation } from "../../discovery-detection.slice";

const AddCategoryButton = (props: ButtonProps) => (
  <Button
    size="small"
    icon={<SmallAddIcon mb="1px" />}
    className=" max-h-[20px] max-w-[20px] rounded-sm border-gray-200 bg-white hover:!bg-gray-100"
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
    <TaxonomyCellContainer ref={ref}>
      {noCategories && (
        <>
          <TaxonomyBadge data-testid="no-classifications">None</TaxonomyBadge>
          {/* resources with child fields can't have data categories */}
          {!hasSubfields && (
            <AddCategoryButton onClick={() => setIsAdding(true)} />
          )}
        </>
      )}

      {showUserCategories && (
        <>
          {userCategories.map((category) => (
            <TaxonomyBadge
              key={category}
              data-testid={`user-classification-${category}`}
            >
              {getDataCategoryDisplayName(category)}
              <Button
                onClick={() => handleRemoveCategory(category)}
                icon={<CloseIcon boxSize={2} mt={-0.5} />}
                size="small"
                type="text"
                className="ml-1 max-h-4 max-w-4"
                aria-label="Remove category"
              />
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
          <DataCategorySelect onChange={handleAddCategory} menuIsOpen />
        </Box>
      )}
    </TaxonomyCellContainer>
  );
};
export default EditCategoriesCell;
