import {
  ArrowDownIcon,
  ArrowUpIcon,
  Badge,
  Checkbox,
  CheckboxProps,
  Flex,
  Text,
} from "@fidesui/react";
import { HeaderContext } from "@tanstack/react-table";
import { ReactNode } from "react";

export const DefaultCell = ({ value }: { value: string }) => (
  <Flex alignItems="center" height="100%">
    <Text fontSize="xs" lineHeight={4} fontWeight="normal">
      {value}
    </Text>
  </Flex>
);

export const BadgeCell = ({
  value,
  suffix,
}: {
  value: string | number;
  suffix?: string;
}) => (
  <Flex alignItems="center" height="100%" mr="2">
    <Badge
      textTransform="none"
      fontWeight="400"
      fontSize="xs"
      lineHeight={4}
      color="gray.600"
      px={2}
      py={1}
    >
      {value}
      {suffix ? ` ${suffix}` : null}
    </Badge>
  </Flex>
);

export const IndeterminateCheckboxCell = ({
  dataTestId,
  ...rest
}: CheckboxProps & { dataTestId?: string }) => (
  <Flex alignItems="center" justifyContent="center">
    <Checkbox
      data-testid={dataTestId || undefined}
      {...rest}
      colorScheme="purple"
    />
  </Flex>
);

type DefaultHeaderCellProps<T, V> = {
  value: V;
} & HeaderContext<T, V>;

export const DefaultHeaderCell = <T,>({
  value,
  column,
}: DefaultHeaderCellProps<T, string | number>) => {
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
