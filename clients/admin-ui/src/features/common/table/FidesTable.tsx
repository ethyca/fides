import {
  ArrowDownIcon,
  ArrowUpIcon,
  Flex,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from "@fidesui/react";
import { useRouter } from "next/router";
import React, { ReactNode } from "react";
import { Column, useGlobalFilter, useSortBy, useTable } from "react-table";

import GlobalFilter from "~/features/datamap/datamap-table/filters/global-accordion-filter/global-accordion-filter";

interface FidesObject {
  id?: string;
  name?: string;
}

type Props<T extends FidesObject> = {
  columns: Column<T>[];
  data: T[];
  userCanUpdate: boolean;
  redirectRoute: string;
  showSearchBar?: boolean;
  footer?: ReactNode;
};

export const FidesTable = <T extends FidesObject>({
  columns,
  data,
  userCanUpdate,
  redirectRoute,
  showSearchBar,
  footer,
}: Props<T>) => {
  const router = useRouter();

  const tableInstance = useTable({ columns, data }, useGlobalFilter, useSortBy);

  const { getTableProps, getTableBodyProps, headerGroups, rows, prepareRow } =
    tableInstance;

  return (
    <TableContainer>
      {showSearchBar ? (
        <Flex flexGrow={1} marginBottom={3}>
          <GlobalFilter
            globalFilter={tableInstance.state.globalFilter}
            setGlobalFilter={tableInstance.setGlobalFilter}
          />
        </Flex>
      ) : null}
      <Table
        {...getTableProps()}
        borderRadius="6px 6px 0px 0px"
        border="1px solid"
        borderColor="gray.200"
        fontSize="sm"
      >
        <Thead backgroundColor="gray.50">
          {headerGroups.map((headerGroup) => {
            const { key: headerRowKey, ...headerGroupProps } =
              headerGroup.getHeaderGroupProps();
            return (
              <Tr key={headerRowKey} {...headerGroupProps}>
                {headerGroup.headers.map((column) => {
                  const { key: columnKey, ...headerProps } =
                    column.getHeaderProps(column.getSortByToggleProps());
                  let sortIcon: ReactNode = null;
                  if (column.isSorted) {
                    sortIcon = column.isSortedDesc ? (
                      <ArrowDownIcon color="gray.500" />
                    ) : (
                      <ArrowUpIcon color="gray.500" />
                    );
                  }

                  return (
                    <Th
                      key={columnKey}
                      {...headerProps}
                      textTransform="none"
                      fontSize="sm"
                      p={4}
                      data-testid={`column-${column.Header}`}
                    >
                      <Text
                        _hover={{ backgroundColor: "gray.100" }}
                        p={1}
                        borderRadius="4px"
                        pr={sortIcon ? 0 : 3.5}
                      >
                        {column.render("Header")}
                        {sortIcon}
                      </Text>
                    </Th>
                  );
                })}
              </Tr>
            );
          })}
        </Thead>
        <Tbody {...getTableBodyProps()}>
          {rows.map((row) => {
            prepareRow(row);
            const { key: rowKey, ...rowProps } = row.getRowProps();
            const onClick = () => {
              if (userCanUpdate) {
                router.push(`${redirectRoute}/${row.original.id}`);
              }
            };
            const rowName = row.original.name;
            return (
              <Tr
                key={rowKey}
                {...rowProps}
                _hover={
                  userCanUpdate
                    ? { backgroundColor: "gray.50", cursor: "pointer" }
                    : undefined
                }
                data-testid={`row-${rowName}`}
              >
                {row.cells.map((cell) => {
                  const { key: cellKey, ...cellProps } = cell.getCellProps();

                  return (
                    <Td
                      key={cellKey}
                      {...cellProps}
                      p={5}
                      verticalAlign="baseline"
                      onClick={
                        cell.column.Header !== "Enable" ? onClick : undefined
                      }
                    >
                      {cell.render("Cell")}
                    </Td>
                  );
                })}
              </Tr>
            );
          })}
        </Tbody>
        {footer}
      </Table>
    </TableContainer>
  );
};
