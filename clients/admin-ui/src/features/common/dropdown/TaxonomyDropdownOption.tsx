import { OptionProps } from "chakra-react-select";
import { Box, HStack, Tag, Text } from "fidesui";

import { sentenceCase } from "~/features/common/utils";

export interface TaxonomySelectOption {
  value: string;
  label: string | JSX.Element;
  description: string;
}

interface TaxonomyDropdownOptionProps
  extends OptionProps<TaxonomySelectOption> {
  tagValue?: string;
}

const TaxonomyDropdownOption = ({
  data,
  setValue,
  tagValue,
}: TaxonomyDropdownOptionProps) => (
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
      {tagValue ? (
        <>
          <Tag
            paddingX={2}
            paddingY={0}
            fontWeight={600}
            colorScheme="gray"
            fontSize="xs"
          >
            {sentenceCase(tagValue || "")}
          </Tag>
          <Text fontSize="sm" whiteSpace="normal">
            : {data.value}
          </Text>
        </>
      ) : (
        <Text fontSize="sm" whiteSpace="normal">
          {data.value}
        </Text>
      )}
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

TaxonomyDropdownOption.displayName = "TaxonomyDropdownOption";

export default TaxonomyDropdownOption;
