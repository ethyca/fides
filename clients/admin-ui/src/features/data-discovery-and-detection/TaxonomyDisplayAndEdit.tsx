import {
  Badge,
  Box,
  CloseIcon,
  EditIcon,
  IconButton,
  SmallAddIcon,
  Wrap,
} from "fidesui";
import { useCallback, useState } from "react";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { StagedResource } from "~/types/api";

import TaxonomySelectDropdown, {
  TaxonomySelectOption,
} from "../common/dropdown/TaxonomySelectDropdown";
import { useOutsideClick } from "../common/hooks";
import { useUpdateResourceCategoryMutation } from "./discovery-detection.slice";

interface TaxonomyDisplayAndEditProps {
  resource: StagedResource;
}

const TaxonomyDisplayAndEdit = ({ resource }: TaxonomyDisplayAndEditProps) => {
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

  if (!bestClassifiedCategory && !userCategories?.length) {
    return <Badge textTransform="none">None</Badge>;
  }

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
      {showUserCategories && (
        <>
          {userCategories.map((category) => (
            <Badge
              fontWeight="normal"
              textTransform="none"
              data-testid={`classification-${category}`}
              px={1.5}
              key={category}
            >
              {getDataCategoryDisplayName(category)}
              <IconButton
                onClick={() => handleRemoveCategory(category)}
                icon={<CloseIcon boxSize={2} />}
                size="2xs"
                mt={-0.5}
                ml={2}
                aria-label="Remove category"
              />
            </Badge>
          ))}
          <IconButton
            w="20px"
            h="20px"
            minW="20px"
            borderRadius="sm"
            icon={<SmallAddIcon />}
            onClick={() => setIsAdding(true)}
            data-testid="add-category-btn"
            aria-label="Add category"
          />
        </>
      )}

      {showClassificationResult && (
        <Badge
          fontWeight="normal"
          textTransform="none"
          px={1.5}
          onClick={() => setIsAdding(true)}
          cursor="pointer"
          data-testid={`classification-${bestClassifiedCategory}`}
        >
          {getDataCategoryDisplayName(bestClassifiedCategory)}{" "}
          <EditIcon ml={0.5} mt={-0.5} />
        </Badge>
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
export default TaxonomyDisplayAndEdit;
