import { Badge, Box, EditIcon, Select } from "@fidesui/react";
import { useState } from "react";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import SelectDropdown from "~/features/common/dropdown/SelectDropdown";

interface TaxonomyDisplayAndEditProps {
  fidesLangKey?: string;
  isEditable?: boolean;
}

const TaxonomyDisplayAndEdit: React.FC<TaxonomyDisplayAndEditProps> = ({
  fidesLangKey,
  isEditable = false,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const { getDataCategoryDisplayName, getDataCategories } = useTaxonomies();
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

  const categoryDisplayName = getDataCategoryDisplayName(fidesLangKey);

  return (
    <Box display="flex" h="100%" alignItems="center" position="relative">
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
          zIndex={1}
          top="0"
          left="0"
          width="100%"
          height="max"
          bgColor="#fff"
        >
          <Select
            placeholder="Select option"
            value={fidesLangKey}
            height={35}
            onChange={() => {}}
          >
            {dataCategories.map((category) => (
              <option value={category.fides_key} key={category.fides_key}>
                {category.name}
              </option>
            ))}
          </Select>
        </Box>
      )}
    </Box>
  );
};
export default TaxonomyDisplayAndEdit;
