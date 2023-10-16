import {
  ArrowDownIcon,
  ArrowUpIcon,
  Box,
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
import React, { MutableRefObject, ReactNode, useEffect, useMemo } from "react";
import {
  useReactTable,
  getSortedRowModel,
  getCoreRowModel,
  getFilteredRowModel,
  flexRender,
  RowModel,
  ColumnDef,
  Table as TableInstance,
  InitialTableState,
} from "@tanstack/react-table";

import GlobalFilter from "~/features/datamap/datamap-table/filters/global-accordion-filter/global-accordion-filter";

type Props<T> = {
  tableInstance: TableInstance<T>;
  showSearchBar?: boolean;
  searchBarPlaceHolder?: string;
  searchBarRightButton?: ReactNode;
  footer?: ReactNode;
  onRowClick?: (row: T) => void;
  customHooks?: Array<(hooks: any) => void>;
};

export function FidesTableV2<T>({
  tableInstance,
  showSearchBar,
  searchBarPlaceHolder,
  searchBarRightButton,
  footer,
  onRowClick,
}: Props<T>) {
  return (
    <Box height="inherit">
      <TableContainer
        height="inherit"
        overflowY="auto"
        border="1px solid"
        boxSizing="border-box"
        borderColor="gray.200"
        borderRadius="6px 6px 0px 0px"
      >
        <Table fontSize="sm">
          <Thead position="sticky" top="0" backgroundColor="gray.50">
            {tableInstance.getHeaderGroups().map((headerGroup) => {
              return (
                <Tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => {
                    let sortIcon: ReactNode = null;
                    if (header.column.getIsSorted()) {
                      sortIcon =
                        header.column.getAutoSortDir() === "desc" ? (
                          <ArrowDownIcon color="gray.500" />
                        ) : (
                          <ArrowUpIcon color="gray.500" />
                        );
                    }

                    return (
                      <Th
                        key={header.id}
                        colSpan={header.colSpan}
                        textTransform="none"
                        fontSize="sm"
                        p={4}
                        data-testid={`column-${header.id}`}
                      >
                        <Text
                          _hover={{ backgroundColor: "gray.100" }}
                          p={1}
                          borderRadius="4px"
                          pr={sortIcon ? 0 : 3.5}
                        >
                          {flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                          {sortIcon}
                        </Text>
                      </Th>
                    );
                  })}
                </Tr>
              );
            })}
          </Thead>
          <Tbody>
            {tableInstance.getRowModel().rows.map((row) => {
              // @ts-ignore
              const rowName = row.original.name;
              return (
                <Tr
                  key={row.id}
                  _hover={
                    onRowClick
                      ? { backgroundColor: "gray.50", cursor: "pointer" }
                      : undefined
                  }
                  data-testid={`row-${rowName ?? row.id}`}
                >
                  {row.getVisibleCells().map((cell) => {
                    return (
                      <Td
                        key={cell.id}
                        p={5}
                        verticalAlign="baseline"
                        onClick={
                          cell.column.columnDef.header !== "Enable" &&
                          onRowClick
                            ? () => {
                                onRowClick(row.original);
                              }
                            : undefined
                        }
                      >
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )}
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
    </Box>
  );
}
