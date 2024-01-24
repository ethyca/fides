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
import React, { ReactNode, useMemo, useState } from "react";

import { FidesRow } from "~/features/common/table/v2/FidesRow";
import { getTableTHandTDStyles } from "~/features/common/table/v2/util";

import { DisplayAllIcon, GroupedIcon } from "../../Icon";

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
  if (!header.column.columnDef.meta?.showHeaderMenu) {
    return (
      <Box style={{ ...getTableTHandTDStyles(header.column.id) }}>
        {flexRender(header.column.columnDef.header, header.getContext())}
      </Box>
    );
  }

  return (
    <Menu placement="bottom-end">
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

const TableBody = <T,>({
  tableInstance,
  rowActionBar,
  onRowClick,
  renderRowTooltipLabel,
  displayAllColumns,
}: Omit<Props<T>, "footer"> & { displayAllColumns: string[] }) => (
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
);

const MemoizedTableBody = React.memo(
  TableBody,
  (prev, next) =>
    prev.tableInstance.options.data === next.tableInstance.options.data
) as typeof TableBody;

/**
 * To enable column resizing, when creating your tableInstance, pass the prop
 * `enableColumnResizing: true`. You'll likely also want `columnResizeMode: "onChange"`.
 *
 * For cells that should either display all or group all, add `showHeaderMenu` to the
 * columnDef's `meta` field and use the cell `GroupCountBadgeCell`
 */
export const FidesTableV2 = <T,>({
  tableInstance,
  rowActionBar,
  footer,
  onRowClick,
  renderRowTooltipLabel,
}: Props<T>) => {
  const [displayAllColumns, setDisplayAllColumns] = useState<string[]>([]);

  const handleAddDisplayColumn = (id: string) => {
    setDisplayAllColumns([...displayAllColumns, id]);
  };
  const handleRemoveDisplayColumn = (id: string) => {
    setDisplayAllColumns(displayAllColumns.filter((c) => c !== id));
  };

  // From https://tanstack.com/table/v8/docs/examples/react/column-resizing-performant
  // To optimize resizing performance
  const columnSizeVars = useMemo(() => {
    const headers = tableInstance.getFlatHeaders();
    const colSizes: { [key: string]: number } = {};
    // eslint-disable-next-line no-plusplus
    for (let i = 0; i < headers.length; i++) {
      const header = headers[i]!;
      colSizes[`--header-${header.id}-size`] = header.getSize();
      colSizes[`--col-${header.column.id}-size`] = header.column.getSize();
    }
    return colSizes;
    // Disabling since the example docs do
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tableInstance.getState().columnSizingInfo]);

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
          ...columnSizeVars,
          minWidth: "100%",
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
        {tableInstance.getState().columnSizingInfo.isResizingColumn ? (
          <MemoizedTableBody
            tableInstance={tableInstance}
            rowActionBar={rowActionBar}
            onRowClick={onRowClick}
            renderRowTooltipLabel={renderRowTooltipLabel}
            displayAllColumns={displayAllColumns}
          />
        ) : (
          <TableBody
            tableInstance={tableInstance}
            rowActionBar={rowActionBar}
            onRowClick={onRowClick}
            renderRowTooltipLabel={renderRowTooltipLabel}
            displayAllColumns={displayAllColumns}
          />
        )}
        {footer}
      </Table>
    </TableContainer>
  );
};
