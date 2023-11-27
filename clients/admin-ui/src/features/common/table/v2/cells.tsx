import {
  ArrowDownIcon,
  ArrowUpIcon,
  Box,
  Checkbox,
  Flex,
  Text,
} from "@fidesui/react";
import { HeaderContext } from "@tanstack/react-table";
import { HTMLProps, ReactNode, useState } from "react";

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
  manualDisable?: boolean;
  dataTestId?: string;
} & HTMLProps<HTMLInputElement>;

export const IndeterminateCheckboxCell = ({
  indeterminate,
  initialValue,
  manualDisable,
  dataTestId,
  ...rest
}: IndeterminateCheckboxCellProps) => {
  const [initialCheckBoxValue] = useState(initialValue);

  return (
    <Flex alignItems="center" justifyContent="center">
      <Box backgroundColor="white">
        <Checkbox
          data-testid={dataTestId || undefined}
          isChecked={initialCheckBoxValue || rest.checked}
          isDisabled={initialCheckBoxValue || manualDisable}
          onChange={rest.onChange}
          isIndeterminate={!rest.checked && indeterminate}
          colorScheme="purple"
        />
      </Box>
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
      fontSize="xs"
      lineHeight={4}
      fontWeight="medium"
      pr={sortIcon ? 0 : 3.5}
      onClick={column.getToggleSortingHandler()}
    >
      {value}
      {sortIcon}
    </Text>
  );
};
