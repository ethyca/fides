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
  Header,
  Row,
  RowData,
  Table as TableInstance,
} from "@tanstack/react-table";
import React, { ReactNode, useState } from "react";

import { FidesRow } from "~/features/common/table/v2/FidesRow";

import { DisplayAllIcon, GroupedIcon } from "../../Icon";
import { getTableTHandTDStyles } from "./util";
// import { getTableTHandTDStyles } from "~/features/common/table/v2/util";

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
    showHeaderMenu?: boolean;
  }
}
/* eslint-enable */

const HeaderContent = <T,>({
  header,
  onGroupAll,
  onDisplayAll,
  isDisplayAll,
}: {
  header: Header<T, unknown>;
  onGroupAll: (id: string) => void;
  onDisplayAll: (id: string) => void;
  isDisplayAll: boolean;
}) => {
  // TODO: return regular render if there is no grouping possible

  if (!header.column.columnDef.meta?.showHeaderMenu) {
    return (
      <Box style={{ ...getTableTHandTDStyles(header.column.id) }}>
        {flexRender(header.column.columnDef.header, header.getContext())}
      </Box>
    );
  }

  return (
    <Menu>
      <MenuButton
        as={Button}
        rightIcon={<ChevronDownIcon />}
        variant="ghost"
        width="100%"
        pr={1}
        textAlign="start"
      >
        {flexRender(header.column.columnDef.header, header.getContext())}
      </MenuButton>
      <Portal>
        <MenuList fontSize="xs" minW="0" w="158px">
          <MenuItem
            color={!isDisplayAll ? "complimentary.500" : undefined}
            onClick={() => onGroupAll(header.id)}
          >
            <GroupedIcon mr="2" /> Group all
          </MenuItem>
          <MenuItem
            color={isDisplayAll ? "complimentary.500" : undefined}
            onClick={() => onDisplayAll(header.id)}
          >
            <DisplayAllIcon mr="2" />
            Display all
          </MenuItem>
        </MenuList>
      </Portal>
    </Menu>
  );
};
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
}: Props<T>) => {
  // TODO: https://tanstack.com/table/v8/docs/examples/react/column-resizing-performant
  const [displayAllColumns, setDisplayAllColumns] = useState<string[]>([]);

  const handleAddDisplayColumn = (id: string) => {
    setDisplayAllColumns([...displayAllColumns, id]);
  };
  const handleRemoveDisplayColumn = (id: string) => {
    setDisplayAllColumns(displayAllColumns.filter((c) => c !== id));
  };

  return (
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
                    padding: 0,
                    width: header.column.columnDef.meta?.width || "unset",
                    minWidth:
                      header.column.columnDef.meta?.minWidth ||
                      (header.column.getCanResize()
                        ? header.getSize()
                        : "unset"),
                    maxWidth:
                      header.column.columnDef.meta?.maxWidth ||
                      (header.column.getCanResize()
                        ? header.getSize()
                        : "unset"),
                    overflowX: "auto",
                  }}
                  textTransform="unset"
                  position="relative"
                >
                  <HeaderContent
                    header={header}
                    onGroupAll={handleRemoveDisplayColumn}
                    onDisplayAll={handleAddDisplayColumn}
                    isDisplayAll={
                      !!displayAllColumns.find((c) => header.id === c)
                    }
                  />
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
              displayAllColumns={displayAllColumns}
            />
          ))}
        </Tbody>
        {footer}
      </Table>
    </TableContainer>
  );
};
