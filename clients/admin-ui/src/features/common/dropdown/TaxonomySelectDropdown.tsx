import { OptionProps, Options, Select } from "chakra-react-select";
import { Box, HStack, Tag, Text } from "fidesui";

import { SELECT_STYLES } from "~/features/common/form/inputs";
import { sentenceCase } from "~/features/common/utils";

import useTaxonomies from "../hooks/useTaxonomies";

export interface TaxonomySelectOption {
  value: string;
  label: string | JSX.Element;
  description: string;
}

const TaxonomyOption = ({
  data,
  setValue,
}: OptionProps<TaxonomySelectOption>) => {
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
      <HStack gap={0} alignItems="center">
        <Tag
          paddingX={2}
          paddingY={0}
          fontWeight={600}
          colorScheme="gray"
          fontSize="xs"
          mr={1}
        >
          {sentenceCase(primaryCategory?.name || "")}
        </Tag>
        <Text fontSize="sm" whiteSpace="normal">
          : {data.value}
        </Text>
      </HStack>
      <Text fontSize="xs" color="gray.500">
        {data.description}
      </Text>
    </Box>
  );
};

interface TaxonomySelectDropdownProps {
  onChange: (selectedOption: TaxonomySelectOption) => void;
  menuIsOpen?: boolean;
  showDisabled?: boolean;
}
const TaxonomySelectDropdown = ({
  onChange,
  menuIsOpen,
  showDisabled = false,
}: TaxonomySelectDropdownProps) => {
  const { getDataCategoryDisplayName, getDataCategories } = useTaxonomies();

  const getActiveDataCategories = () =>
    getDataCategories().filter((c) => c.active);

  const dataCategories = showDisabled
    ? getDataCategories()
    : getActiveDataCategories();

  const options: Options<TaxonomySelectOption> = dataCategories.map(
    (category) => ({
      value: category.fides_key,
      label: getDataCategoryDisplayName(category.fides_key),
      description: category.description || "",
    }),
  );

  return (
    <Select
      placeholder="Select a category"
      onChange={onChange as any}
      options={options}
      size="sm"
      menuPosition="absolute"
      autoFocus
      isSearchable
      menuPlacement="auto"
      components={{
        Option: TaxonomyOption,
      }}
      menuIsOpen={menuIsOpen}
      chakraStyles={{
        ...(SELECT_STYLES as Options<TaxonomySelectOption>),
        menuList: (baseStyles) => ({
          ...baseStyles,
          paddingTop: 0,
          paddingBottom: 0,
          position: "fixed",
          overflowX: "hidden",
          maxWidth: "lg",
        }),
      }}
    />
  );
};
export default TaxonomySelectDropdown;
