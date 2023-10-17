import {
  ArrowDownIcon,
  ArrowUpIcon,
  Box,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from "@fidesui/react";
import { flexRender, Table as TableInstance } from "@tanstack/react-table";
import React, { ReactNode } from "react";

const getTableTHandTDStyles = (cellId: string) => {
  return cellId === "select"
    ? { padding: "0px", width: "55px" }
    : {
        "padding-left": "16px",
        "padding-right": "8px",
        "padding-top": "0px",
        "padding-bottom": "0px",
      };
};

type Props<T> = {
  tableInstance: TableInstance<T>;
  footer?: ReactNode;
  onRowClick?: (row: T) => void;
};

export function FidesTableV2<T>({
  tableInstance,
  footer,
  onRowClick,
}: Props<T>) {
  return (
    <Box height="inherit">
      <TableContainer height="inherit" overflowY="auto">
        <Table variant="unstyled" borderCollapse="collapse">
          <Thead
            position="sticky"
            top="0"
            height="36px"
            backgroundColor="gray.50"
          >
            {tableInstance.getHeaderGroups().map((headerGroup) => (
              <Tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <Th
                      borderWidth="1px"
                      borderColor="gray.200"
                      key={header.id}
                      colSpan={header.colSpan}
                      data-testid={`column-${header.id}`}
                      style={getTableTHandTDStyles(header.column.id)}
                    >
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                    </Th>
                  );
                })}
              </Tr>
            ))}
          </Thead>
          <Tbody>
            {tableInstance.getRowModel().rows.map((row) => {
              // @ts-ignore
              const rowName = row.original.name;
              return (
                <Tr
                  key={row.id}
                  height="36px"
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
                        borderWidth="1px"
                        borderColor="gray.200"
                        height="inherit"
                        style={getTableTHandTDStyles(cell.column.id)}
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
