import {
  Table,
  TableContainer,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
} from "@fidesui/react";
import { flexRender, Table as TableInstance } from "@tanstack/react-table";
import React, { ReactNode } from "react";

const getTableTHandTDStyles = (cellId: string) =>
  cellId === "select"
    ? { padding: "0px", width: "55px" }
    : {
        paddingLeft: "16px",
        paddingRight: "8px",
        paddingTop: "0px",
        paddingBottom: "0px",
      };

type Props<T> = {
  tableInstance: TableInstance<T>;
  rowActionBar?: ReactNode;
  footer?: ReactNode;
  onRowClick?: (row: T) => void;
};

export const FidesTableV2 = <T,>({
  tableInstance,
  rowActionBar,
  footer,
  onRowClick,
}: Props<T>) => (
  <TableContainer
    overflowY="auto"
    borderBottomWidth="1px"
    borderBottomColor="gray.200"
  >
    <Table
      variant="unstyled"
      style={{
        borderCollapse: "separate",
        borderSpacing: 0,
      }}
    >
      <Thead
        position="sticky"
        top="0"
        height="36px"
        zIndex={10}
        backgroundColor="gray.50"
      >
        {tableInstance.getHeaderGroups().map((headerGroup) => (
          <Tr key={headerGroup.id}>
            {headerGroup.headers.map((header) => (
              <Th
                key={header.id}
                borderTopWidth="1px"
                borderTopColor="gray.200"
                borderBottomWidth="1px"
                borderBottomColor="gray.200"
                borderRightWidth="1px"
                borderRightColor="gray.200"
                _first={{
                  borderLeftWidth: "1px",
                  borderLeftColor: "gray.200",
                }}
                colSpan={header.colSpan}
                data-testid={`column-${header.id}`}
                style={getTableTHandTDStyles(header.column.id)}
              >
                {flexRender(
                  header.column.columnDef.header,
                  header.getContext()
                )}
              </Th>
            ))}
          </Tr>
        ))}
      </Thead>
      <Tbody>
        {rowActionBar}
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
              {row.getVisibleCells().map((cell) => (
                <Td
                  key={cell.id}
                  borderBottomWidth="1px"
                  borderBottomColor="gray.200"
                  borderRightWidth="1px"
                  borderRightColor="gray.200"
                  _first={{
                    borderLeftWidth: "1px",
                    borderLeftColor: "gray.200",
                  }}
                  height="inherit"
                  style={getTableTHandTDStyles(cell.column.id)}
                  onClick={
                    cell.column.columnDef.header !== "Enable" && onRowClick
                      ? () => {
                          onRowClick(row.original);
                        }
                      : undefined
                  }
                >
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </Td>
              ))}
            </Tr>
          );
        })}
      </Tbody>
      {footer}
    </Table>
  </TableContainer>
);
