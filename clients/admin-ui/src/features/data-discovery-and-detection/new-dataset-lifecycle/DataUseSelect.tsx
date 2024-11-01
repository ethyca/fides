import { OptionProps, Options, Select } from "chakra-react-select";
import { Box, HStack, Tag, Text } from "fidesui";

import {
  TaxonomySelectDropdownProps,
  TaxonomySelectOption,
} from "~/features/common/dropdown/DataCategorySelect";
import { SELECT_STYLES } from "~/features/common/form/inputs";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { sentenceCase } from "~/features/common/utils";

const DataUseOption = ({
  data,
  setValue,
}: OptionProps<TaxonomySelectOption>) => {
  const { getPrimaryKey, getDataUseByKey } = useTaxonomies();
  const primaryKey = getPrimaryKey(data.value, 2);
  const primaryDataUse = getDataUseByKey(primaryKey);
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
          {sentenceCase(primaryDataUse?.name || "")}
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

const DataUseSelect = ({
  onChange,
  menuIsOpen,
  showDisabled = false,
}: TaxonomySelectDropdownProps) => {
  const { getDataUseDisplayName, getDataUses } = useTaxonomies();

  const getActiveDataUses = () => getDataUses().filter((du) => du.active);

  const dataUses = showDisabled ? getDataUses() : getActiveDataUses();

  const options: Options<TaxonomySelectOption> = dataUses.map((dataUse) => ({
    value: dataUse.fides_key,
    label: getDataUseDisplayName(dataUse.fides_key),
    description: dataUse.description || "",
  }));

  return (
    <Select
      placeholder="Select a data use..."
      onChange={onChange as any}
      options={options}
      size="sm"
      menuPosition="absolute"
      autoFocus
      isSearchable
      menuPlacement="auto"
      components={{
        Option: DataUseOption,
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

export default DataUseSelect;
