import { Badge, Box, EditIcon } from "@fidesui/react";
import { Options, Select } from "chakra-react-select";
import { useState } from "react";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { StagedResource } from "~/types/api";

import { useUpdateResourceCategoryMutation } from "./discovery-detection.slice";

interface TaxonomyDisplayAndEditProps {
  fidesLangKey?: string;
  isEditable?: boolean;
  resource: StagedResource;
}

const TaxonomyDisplayAndEdit: React.FC<TaxonomyDisplayAndEditProps> = ({
  fidesLangKey,
  isEditable = false,
  resource,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const { getDataCategoryDisplayName, getDataCategories } = useTaxonomies();
  const [updateResourceCategoryMutation] = useUpdateResourceCategoryMutation();
  const dataCategories = getDataCategories();

  if (!fidesLangKey) {
    return <Badge textTransform="none">None</Badge>;
  }

  const handleClickBadge = () => {
    if (!isEditable) {
      return;
    }

    setIsEditing(true);
  };

  const categoryDisplayName = getDataCategoryDisplayName(
    resource.user_assigned_data_categories?.length
      ? resource.user_assigned_data_categories[0]
      : fidesLangKey
  );

  const handleCategoryChange = ({ value }) => {
    updateResourceCategoryMutation({
      staged_resource_urn: resource.urn,
      monitor_config_id: resource.monitor_config_id,
      user_assigned_data_categories: [value],
    });
  };

  const options: Options<{ value: string; label: string }> = dataCategories.map(
    (category) => ({
      value: category.fides_key,
      label: getDataCategoryDisplayName(category.fides_key),
    })
  );

  return (
    <Box
      display="flex"
      h="100%"
      alignItems="center"
      position="relative"
      width="100%"
    >
      <Badge
        fontWeight="normal"
        textTransform="none"
        onClick={handleClickBadge}
        cursor={isEditable ? "pointer" : "default"}
      >
        {categoryDisplayName} {isEditable && <EditIcon marginLeft={0.5} />}
      </Badge>

      {isEditing && (
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
          <Select
            placeholder="Select option"
            defaultValue={fidesLangKey}
            onChange={handleCategoryChange}
            options={options}
            size="sm"
            menuPosition="absolute"
            menuPlacement="auto"
          />
        </Box>
      )}
    </Box>
  );
};
export default TaxonomyDisplayAndEdit;
