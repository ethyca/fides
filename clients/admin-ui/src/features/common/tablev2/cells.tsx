import {
  Flex,
  Text,
  Checkbox,
  ArrowDownIcon,
  ArrowUpIcon,
} from "@fidesui/react";
import { useState, HTMLProps, ReactNode } from "react";
import { HeaderContext } from "@tanstack/react-table";

export const DefaultCell = ({ value }: { value: string }) => (
  <Flex alignItems="center" height="100%">
    <Text fontSize="xs" lineHeight={4} fontWeight="normal">
      {value}
    </Text>
  </Flex>
);

type IndeterminateCheckboxCellProps = {
  indeterminate?: boolean;
  initialValue?: boolean;
} & HTMLProps<HTMLInputElement>;

export const IndeterminateCheckboxCell = ({
  indeterminate,
  className = "",
  initialValue,
  ...rest
}: IndeterminateCheckboxCellProps) => {
  const [initialCheckBoxValue] = useState(initialValue);

  return (
    <Flex alignItems="center" justifyContent="center">
      <Checkbox
        isChecked={initialCheckBoxValue || rest.checked}
        isDisabled={initialCheckBoxValue}
        onChange={rest.onChange}
        isIndeterminate={!rest.checked && indeterminate}
        colorScheme="purple"
      />
    </Flex>
  );
};

type DefaultHeaderCellProps<T, V> = {
  value: V;
} & HeaderContext<T, V>;

export const DefaultHeaderCell = <T,>({
  value,
  column,
}: DefaultHeaderCellProps<T, string>) => {
  let sortIcon: ReactNode = null;
  if (column.getIsSorted()) {
    sortIcon =
      column.getAutoSortDir() === "desc" ? (
        <ArrowDownIcon color="gray.500" />
      ) : (
        <ArrowUpIcon color="gray.500" />
      );
  }

  return (
    <Text
      _hover={{ backgroundColor: "gray.100" }}
      borderRadius="4px"
      pr={sortIcon ? 0 : 3.5}
      onClick={column.getToggleSortingHandler()}
    >
      {value}
      {sortIcon}
    </Text>
  );
};
