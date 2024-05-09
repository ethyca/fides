import { Badge, Box, HStack, Text } from "@fidesui/react";
import { OptionProps, Options, Select } from "chakra-react-select";

import useTaxonomies from "../hooks/useTaxonomies";

interface TaxonomySelectDropdownProps {
  taxonomyKey: string;
  onChange: (selectedOption: TaxonomySelectOption) => void;
  menuIsOpen?: boolean;
}

export interface TaxonomySelectOption {
  value: string;
  label: string;
  description: string;
}

const Option = ({ data, setValue }: OptionProps<TaxonomySelectOption>) => {
  const { getPrimaryKey, getDataCategoryByKey } = useTaxonomies();
  const primaryKey = getPrimaryKey(data.value, 2);
  const primaryCategory = getDataCategoryByKey(primaryKey);

  return (
    <Box
      onClick={() => setValue(data, "select-option")}
      cursor="pointer"
      borderBottomColor="gray.100"
      borderBottomWidth={1}
      paddingX={3}
      paddingY={1.5}
      _hover={{
        backgroundColor: "gray.100",
      }}
      data-testid={`option-${data.value}`}
    >
      <HStack gap={0} alignItems="flex-start">
        <Badge paddingX={1} paddingY={0} bgColor="gray.300" fontSize="xx-small">
          {primaryCategory?.name}
        </Badge>
        <Text fontSize="xs" whiteSpace="normal">
          : {data.description}
        </Text>
      </HStack>
      <Text fontSize="xs" color="gray.500">
        {data.value}
      </Text>
    </Box>
  );
};

const TaxonomySelectDropdown: React.FC<TaxonomySelectDropdownProps> = ({
  taxonomyKey,
  onChange,
  menuIsOpen,
}) => {
  const { getDataCategoryDisplayName, getDataCategories } = useTaxonomies();
  const dataCategories = getDataCategories();

  const options: Options<TaxonomySelectOption> = dataCategories.map(
    (category) => ({
      value: category.fides_key,
      // Actually, it's a react node because it contains a <strong> element, bit the library handles it
      label: getDataCategoryDisplayName(category.fides_key) as string,
      description: category.description || "",
    })
  );

  return (
    <Select
      placeholder="Select a category"
      defaultValue={{ value: taxonomyKey, description: "", label: "" }}
      onChange={onChange as any}
      options={options}
      size="sm"
      menuPosition="absolute"
      menuPlacement="auto"
      components={{
        Option,
      }}
      menuIsOpen={menuIsOpen}
      chakraStyles={{
        menuList: (baseStyles) => ({
          ...baseStyles,
          paddingTop: 0,
          paddingBottom: 0,
        }),
      }}
    />
  );
};
export default TaxonomySelectDropdown;
