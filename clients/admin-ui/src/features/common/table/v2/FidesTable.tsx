import {
  Box,
  Button,
  ChevronDownIcon,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Portal,
  Table,
  TableContainer,
  Tbody,
  Th,
  Thead,
  Tr,
} from "@fidesui/react";
import {
  flexRender,
  Row,
  RowData,
  Table as TableInstance,
} from "@tanstack/react-table";
import React, { ReactNode } from "react";

import { FidesRow } from "~/features/common/table/v2/FidesRow";
import { getTableTHandTDStyles } from "~/features/common/table/v2/util";

/*
  This was throwing a false positive for unused parameters.
  It's also how the library author recommends typing meta.
  https://tanstack.com/table/v8/docs/api/core/column-def#meta
*/
/* eslint-disable */
declare module "@tanstack/table-core" {
  interface ColumnMeta<TData extends RowData, TValue> {
    width?: string;
    minWidth?: string;
    maxWidth?: string;
    displayText?: string;
  }
}
/* eslint-enable */

type Props<T> = {
  tableInstance: TableInstance<T>;
  rowActionBar?: ReactNode;
  footer?: ReactNode;
  onRowClick?: (row: T) => void;
  renderRowTooltipLabel?: (row: Row<T>) => string | undefined;
};

export const FidesTableV2 = <T,>({
  tableInstance,
  rowActionBar,
  footer,
  onRowClick,
  renderRowTooltipLabel,
}: Props<T>) => (
  <TableContainer
    data-testid="fidesTable"
    overflowY="auto"
    borderBottomWidth="1px"
    borderBottomColor="gray.200"
  >
    <Table
      variant="unstyled"
      style={{
        borderCollapse: "separate",
        borderSpacing: 0,
        width: tableInstance.getCenterTotalSize(),
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
          <Tr key={headerGroup.id} height="inherit">
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
                style={{
                  // ...getTableTHandTDStyles(header.column.id),
                  padding: 0,
                  width: header.column.columnDef.meta?.width || "unset",
                  minWidth:
                    header.column.columnDef.meta?.minWidth ||
                    (header.column.getCanResize() ? header.getSize() : "unset"),
                  maxWidth:
                    header.column.columnDef.meta?.maxWidth ||
                    (header.column.getCanResize() ? header.getSize() : "unset"),
                  overflowX: "auto",
                }}
                textTransform="unset"
                position="relative"
              >
                <Menu size="xs">
                  <MenuButton
                    as={Button}
                    rightIcon={<ChevronDownIcon />}
                    variant="ghost"
                    width="100%"
                    pr={1}
                    textAlign="start"
                  >
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext()
                    )}
                  </MenuButton>
                  <Portal>
                    <MenuList fontSize="xs">
                      <MenuItem>Group all</MenuItem>
                      <MenuItem>Display all</MenuItem>
                    </MenuList>
                  </Portal>
                </Menu>
                {/* Capture area to render resizer cursor */}
                {header.column.getCanResize() ? (
                  <Box
                    onDoubleClick={header.column.resetSize}
                    onMouseDown={header.getResizeHandler()}
                    position="absolute"
                    height="100%"
                    top="0"
                    right="0"
                    width="5px"
                    cursor="col-resize"
                    userSelect="none"
                  />
                ) : null}
              </Th>
            ))}
          </Tr>
        ))}
      </Thead>
      <Tbody data-testid="fidesTable-body">
        {rowActionBar}
        {tableInstance.getRowModel().rows.map((row) => (
          <FidesRow<T>
            key={row.id}
            row={row}
            onRowClick={onRowClick}
            renderRowTooltipLabel={renderRowTooltipLabel}
          />
        ))}
      </Tbody>
      {footer}
    </Table>
  </TableContainer>
);
