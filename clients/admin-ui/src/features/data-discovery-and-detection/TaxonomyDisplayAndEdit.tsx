import { Badge, Box, EditIcon } from "@fidesui/react";
import { Options } from "chakra-react-select";
import { useState } from "react";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { StagedResource } from "~/types/api";
import TaxonomySelectDropdown, {
  TaxonomySelectOption,
} from "../common/dropdown/TaxonomySelectDropdown";

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

  const handleCategoryChange = (option: TaxonomySelectOption) => {
    updateResourceCategoryMutation({
      staged_resource_urn: resource.urn,
      monitor_config_id: resource.monitor_config_id!,
      user_assigned_data_categories: [option.value],
    });
  };

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
          <TaxonomySelectDropdown
            taxonomyKey={fidesLangKey}
            onChange={handleCategoryChange}
            menuIsOpen={true}
          />
        </Box>
      )}
    </Box>
  );
};
export default TaxonomyDisplayAndEdit;
