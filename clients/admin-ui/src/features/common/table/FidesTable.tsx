import {
  ArrowDownIcon,
  ArrowUpIcon,
  Button,
  Flex,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Tfoot,
  Th,
  Thead,
  Tr,
} from "@fidesui/react";
import NextLink from "next/link";
import { useRouter } from "next/router";
import React, { ReactNode } from "react";
import { Column, useGlobalFilter, useSortBy, useTable } from "react-table";
import { UrlObject } from "url";

import Restrict from "~/features/common/Restrict";
import GlobalFilter from "~/features/datamap/datamap-table/filters/global-accordion-filter/global-accordion-filter";
import { ScopeRegistryEnum } from "~/types/api";

type Props<T extends object> = {
  columns: Column<T>[];
  data: T[];
  userCanUpdate: boolean;
  redirectRoute: string;
  createScope: ScopeRegistryEnum;
  addButtonText: string;
  addButtonHref: string | UrlObject;
  testId: string;
  showSearchBar?: boolean;
};

export const FidesTable = <T extends object>({
  columns,
  data,
  userCanUpdate,
  redirectRoute,
  createScope,
  addButtonText,
  addButtonHref,
  testId,
  showSearchBar,
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
                // @ts-ignore
                router.push(`${redirectRoute}/${row.original.id}`);
              }
            };
            // @ts-ignore
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
                      {
                        // @ts-ignore
                        cell.column.onToggle
                          ? cell.render("Cell", {
                              // @ts-ignore
                              onToggle: cell.column.onToggle,
                            })
                          : cell.render("Cell")
                      }
                    </Td>
                  );
                })}
              </Tr>
            );
          })}
        </Tbody>
        <Tfoot backgroundColor="gray.50">
          <Tr>
            <Td colSpan={columns.length} px={4} py={3.5}>
              <Restrict scopes={[createScope]}>
                <NextLink href={addButtonHref}>
                  <Button
                    size="xs"
                    colorScheme="primary"
                    data-testid={`add-${testId}-btn`}
                  >
                    {addButtonText}
                  </Button>
                </NextLink>
              </Restrict>
            </Td>
          </Tr>
        </Tfoot>
      </Table>
    </TableContainer>
  );
};
