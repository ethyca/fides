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
import React, { ReactNode, useMemo } from "react";
import {
  Column,
  Hooks,
  useGlobalFilter,
  useSortBy,
  useTable,
} from "react-table";

import GlobalFilter from "~/features/datamap/datamap-table/filters/global-accordion-filter/global-accordion-filter";

interface FidesObject {
  id?: string;
  name?: string;
}

type Props<T extends FidesObject> = {
  columns: Column<T>[];
  data: T[];
  showSearchBar?: boolean;
  searchBarPlaceHolder?: string;
  footer?: ReactNode;
  onRowClick?: (row: T) => void;
  customHooks?: Array<(hooks: Hooks<T>) => void>;
};

export const FidesTable = <T extends FidesObject>({
  columns,
  data,
  showSearchBar,
  searchBarPlaceHolder,
  footer,
  onRowClick,
  customHooks,
}: Props<T>) => {
  const plugins = useMemo(() => {
    if (customHooks) {
      return [useGlobalFilter, useSortBy, ...customHooks];
    }
    return [useGlobalFilter, useSortBy];
  }, [customHooks]);

  const tableInstance = useTable({ columns, data }, ...plugins);

  const { getTableProps, getTableBodyProps, headerGroups, rows, prepareRow } =
    tableInstance;

  return (
    <TableContainer>
      {showSearchBar ? (
        <Flex flexGrow={1} marginBottom={3}>
          <GlobalFilter
            globalFilter={tableInstance.state.globalFilter}
            setGlobalFilter={tableInstance.setGlobalFilter}
            placeholder={searchBarPlaceHolder}
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
            const rowName = row.original.name;
            const rowId = row.original.id;
            return (
              <Tr
                key={rowKey}
                {...rowProps}
                _hover={
                  onRowClick
                    ? { backgroundColor: "gray.50", cursor: "pointer" }
                    : undefined
                }
                data-testid={`row-${rowName ?? rowId}`}
              >
                {row.cells.map((cell) => {
                  const { key: cellKey, ...cellProps } = cell.getCellProps();
                  return (
                    <Td
                      key={cellKey}
                      {...cellProps}
                      p={5}
                      verticalAlign="baseline"
                      width={cell.column.width}
                      onClick={
                        cell.column.Header !== "Enable" && onRowClick
                          ? () => {
                              onRowClick(row.original);
                            }
                          : undefined
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
