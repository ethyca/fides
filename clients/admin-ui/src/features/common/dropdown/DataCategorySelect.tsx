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

export const DataCategoryOption = ({
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
      <HStack gap={1} alignItems="center">
        <Tag
          paddingX={2}
          paddingY={0}
          fontWeight={600}
          colorScheme="gray"
          fontSize="xs"
        >
          {sentenceCase(primaryCategory?.name || "")}
        </Tag>
        <Text fontSize="sm" whiteSpace="normal">
          : {data.value}
        </Text>
      </HStack>
      <Text
        fontSize="xs"
        lineHeight="18px"
        mt={1}
        color="gray.500"
        whiteSpace="normal"
      >
        {data.description}
      </Text>
    </Box>
  );
};

export interface TaxonomySelectDropdownProps {
  onChange: (selectedOption: TaxonomySelectOption) => void;
  menuIsOpen?: boolean;
  showDisabled?: boolean;
}
const DataCategorySelect = ({
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
      placeholder="Select a category..."
      onChange={onChange as any}
      options={options}
      size="sm"
      menuPosition="absolute"
      autoFocus
      isSearchable
      menuPlacement="auto"
      components={{
        Option: DataCategoryOption,
      }}
      menuIsOpen={menuIsOpen}
      chakraStyles={{
        ...(SELECT_STYLES as Options<TaxonomySelectOption>),
        control: (baseStyles) => ({ ...baseStyles, border: "none" }),
        menuList: (baseStyles) => ({
          ...baseStyles,
          paddingTop: 0,
          paddingBottom: 0,
          mt: 10,
          position: "fixed",
          overflowX: "hidden",
          maxWidth: "lg",
        }),
      }}
    />
  );
};
export default DataCategorySelect;
