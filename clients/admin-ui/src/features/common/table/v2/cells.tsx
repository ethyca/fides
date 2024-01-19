import {
  ArrowDownIcon,
  ArrowUpIcon,
  Badge,
  Box,
  Checkbox,
  CheckboxProps,
  Flex,
  Text,
} from "@fidesui/react";
import { HeaderContext } from "@tanstack/react-table";
import { FC, ReactNode } from "react";

export const DefaultCell = ({
  value,
}: {
  value: string | undefined | number | boolean;
}) => (
  <Flex alignItems="center" height="100%">
    <Text fontSize="xs" lineHeight={4} fontWeight="normal">
      {value !== null && value !== undefined ? value.toString() : value}
    </Text>
  </Flex>
);

const FidesBadge: FC = ({ children }) => (
  <Badge
    textTransform="none"
    fontWeight="400"
    fontSize="xs"
    lineHeight={4}
    color="gray.600"
    px={2}
    py={1}
  >
    {children}
  </Badge>
);

export const BadgeCell = ({
  value,
  suffix,
}: {
  value: string | number;
  suffix?: string;
}) => (
  <Flex alignItems="center" height="100%" mr="2">
    <FidesBadge>
      {value}
      {suffix ? ` ${suffix}` : null}
    </FidesBadge>
  </Flex>
);

export const GroupCountBadgeCell = ({
  value,
  suffix,
  expand,
}: {
  value: string[] | string | undefined;
  suffix?: string;
  expand: boolean;
}) => {
  let badges = null;
  if (Array.isArray(value) || !value) {
    badges = expand ? (
      // @ts-ignore
      value.map((d) => (
        <Box px={1} key={d}>
          <FidesBadge>{d}</FidesBadge>
        </Box>
      ))
    ) : (
      <FidesBadge>
        {value ? value.length : 0}
        {suffix ? ` ${suffix}` : null}
      </FidesBadge>
    );
  } else {
    badges = <FidesBadge>{value}</FidesBadge>;
  }

  return (
    <Flex alignItems="center" height="100%" mr="2">
      {badges}
    </Flex>
  );
};

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
}: DefaultHeaderCellProps<
  T,
  string | number | string[] | undefined | boolean
>) => {
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
