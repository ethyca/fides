import {
  ArrowDownIcon,
  ArrowUpIcon,
  Button,
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
import { EnableCell } from "common/table/cells";
import { useRouter } from "next/router";
import { ReactNode } from "react";
import { Column, useSortBy, useTable } from "react-table";

import Restrict from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

import EmptyState from "./EmptyState";


type Props<T extends object> = {
  columns: Column<T>[];
  data: T[];
  userCanUpdate: boolean;
  redirectRoute: string;
  createScope: ScopeRegistryEnum;
  addButtonText: string;
  testId?: string;
};

export const FidesTable = <T extends object>({
  columns,
  data,
  userCanUpdate,
  redirectRoute,
  createScope,
  addButtonText,
  testId,
}: Props<T>) => {
  const router = useRouter();

  const tableInstance = useTable({ columns, data }, useSortBy);

  const { getTableProps, getTableBodyProps, headerGroups, rows, prepareRow } =
    tableInstance;

  if (data.length === 0) {
    return <EmptyState />;
  }
  console.log(testId)
  return (
    <TableContainer>
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
                      {cell.column.Cell === EnableCell
                        ? cell.render("Cell", {
                            // @ts-ignore
                            onToggle: cell.column.onToggle,
                          })
                        : cell.render("Cell")}
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
                <Button
                  size="xs"
                  colorScheme="primary"
                  data-testid={`add-${testId}-btn`}
                >
                  {addButtonText}
                </Button>
              </Restrict>
            </Td>
          </Tr>
        </Tfoot>
      </Table>
    </TableContainer>
  );
};
