import {
  ChakraBox as Box,
  ChakraCheckbox as Checkbox,
  ChakraFlex as Flex,
  ChakraText as Text,
  Tag,
} from "fidesui";
import { ReactNode } from "react";

export const HeaderCheckboxRow = ({
  title,
  allSelected,
  numSelected,
  onToggleAll,
  children,
}: {
  title: string;
  allSelected: boolean;
  numSelected: number;
  onToggleAll: () => void;
  children?: ReactNode;
}) => (
  <Flex justifyContent="space-between" mb={4}>
    <Box>
      <Checkbox
        colorScheme="complimentary"
        size="md"
        isChecked={allSelected}
        isIndeterminate={!allSelected && numSelected > 0}
        onChange={onToggleAll}
        mr={3}
        data-testid="select-all"
      >
        <Text fontWeight="semibold" fontSize="md">
          {title}
        </Text>
      </Checkbox>
      <Tag color="minos" className="w-fit" data-testid="num-selected-badge">
        {numSelected} selected
      </Tag>
    </Box>
    {children}
  </Flex>
);
