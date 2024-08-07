import {
  ColumnSort,
  flexRender,
  Header,
  Row,
  RowData,
  Table as TableInstance,
} from "@tanstack/react-table";
import {
  ArrowDownIcon,
  ArrowUpIcon,
  Box,
  Button,
  HStack,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  MoreIcon,
  Portal,
  SmallCloseIcon,
  Table,
  TableContainer,
  Tbody,
  Td,
  Th,
  Thead,
  theme,
  Tr,
} from "fidesui";
import React, { ReactNode, useEffect, useMemo } from "react";

import { useLocalStorage } from "~/features/common/hooks/useLocalStorage";
import { DisplayAllIcon, GroupedIcon } from "~/features/common/Icon";
import { FidesRow } from "~/features/common/table/v2/FidesRow";
import { getTableTHandTDStyles } from "~/features/common/table/v2/util";
import { DATAMAP_LOCAL_STORAGE_KEYS } from "~/features/datamap/constants";

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
    overflow?: "auto" | "visible" | "hidden";
    disableRowClick?: boolean;
    onCellClick?: (row: TData) => void;
  }
}
/* eslint-enable */

export const sortingDisplay: {
  [key: string]: { icon: JSX.Element; title: string };
} = {
  asc: { icon: <ArrowUpIcon />, title: "Sort ascending" },
  desc: { icon: <ArrowDownIcon />, title: "Sort descending" },
};

const tableHeaderButtonStyles = {
  height: theme.space[9], // same as table header height
  width: "100%",
  textAlign: "start",
  "&:focus-visible": {
    backgroundColor: "gray.100",
  },
  "&:focus": {
    outline: "none",
  },
};

interface HeaderContentProps<T> {
  header: Header<T, unknown>;
  onGroupAll: (id: string) => void;
  onDisplayAll: (id: string) => void;
  isDisplayAll: boolean;
  enableSorting: boolean;
}
const HeaderContent = <T,>({
  header,
  onGroupAll,
  onDisplayAll,
  isDisplayAll,
  enableSorting,
}: HeaderContentProps<T>) => {
  if (!header.column.columnDef.meta?.showHeaderMenu) {
    if (enableSorting && header.column.getCanSort()) {
      return (
        <Button
          data-testid={`${header.id}-header-sort`}
          onClick={header.column.getToggleSortingHandler()}
          rightIcon={
            sortingDisplay[header.column.getIsSorted() as string]?.icon
          }
          title={
            sortingDisplay[header.column.getNextSortingOrder() as string]
              ?.title ?? "Clear sort"
          }
          variant="ghost"
          size="sm"
          sx={{
            ...getTableTHandTDStyles(header.column.id),
            ...tableHeaderButtonStyles,
          }}
        >
          {flexRender(header.column.columnDef.header, header.getContext())}
        </Button>
      );
    }

    return (
      <Box
        data-testid={`${header.id}-header`}
        sx={{ ...getTableTHandTDStyles(header.column.id) }}
        fontSize="xs"
        lineHeight={9} // same as table header height
        fontWeight="medium"
      >
        {flexRender(header.column.columnDef.header, header.getContext())}
      </Box>
    );
  }

  return (
    <Menu placement="bottom-end">
      <MenuButton
        as={Button}
        rightIcon={
          <HStack>
            {sortingDisplay[header.column.getIsSorted() as string]?.icon}
            <MoreIcon transform="rotate(90deg)" />
          </HStack>
        }
        title="Column options"
        variant="ghost"
        size="sm"
        sx={{
          ...getTableTHandTDStyles(header.column.id),
          ...tableHeaderButtonStyles,
        }}
        data-testid={`${header.id}-header-menu`}
      >
        {flexRender(header.column.columnDef.header, header.getContext())}
      </MenuButton>
      <Portal>
        <MenuList
          fontSize="xs"
          minW="0"
          w="158px"
          data-testid={`${header.id}-header-menu-list`}
        >
          <MenuItem
            gap={2}
            color={!isDisplayAll ? "complimentary.500" : undefined}
            onClick={() => onGroupAll(header.id)}
          >
            <GroupedIcon /> Group all
          </MenuItem>
          <MenuItem
            gap={2}
            color={isDisplayAll ? "complimentary.500" : undefined}
            onClick={() => onDisplayAll(header.id)}
          >
            <DisplayAllIcon /> Display all
          </MenuItem>
          {enableSorting && header.column.getCanSort() && (
            <MenuItem gap={2} onClick={header.column.getToggleSortingHandler()}>
              {sortingDisplay[header.column.getNextSortingOrder() as string]
                ?.icon ?? <SmallCloseIcon />}
              {sortingDisplay[header.column.getNextSortingOrder() as string]
                ?.title ?? "Clear sort"}
            </MenuItem>
          )}
        </MenuList>
      </Portal>
    </Menu>
  );
};

type Props<T> = {
  tableInstance: TableInstance<T>;
  rowActionBar?: ReactNode;
  footer?: ReactNode;
  onRowClick?: (row: T, e: React.MouseEvent<HTMLTableCellElement>) => void;
  renderRowTooltipLabel?: (row: Row<T>) => string | undefined;
  emptyTableNotice?: ReactNode;
  overflow?: "auto" | "visible" | "hidden";
  enableSorting?: boolean;
  onSort?: (columnSort: ColumnSort) => void;
};

const TableBody = <T,>({
  tableInstance,
  rowActionBar,
  onRowClick,
  renderRowTooltipLabel,
  displayAllColumns,
  emptyTableNotice,
}: Omit<Props<T>, "footer" | "enableSorting" | "onSort"> & {
  displayAllColumns: string[];
}) => (
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
    {tableInstance.getRowModel().rows.length === 0 &&
      !tableInstance.getState()?.globalFilter &&
      emptyTableNotice && (
        <Tr>
          <Td colSpan={100}>{emptyTableNotice}</Td>
        </Tr>
      )}
  </Tbody>
);

const MemoizedTableBody = React.memo(
  TableBody,
  (prev, next) =>
    prev.tableInstance.options.data === next.tableInstance.options.data,
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
  emptyTableNotice,
  overflow = "auto",
  onSort,
  enableSorting = !!onSort,
}: Props<T>) => {
  const [displayAllColumns, setDisplayAllColumns] = useLocalStorage<string[]>(
    DATAMAP_LOCAL_STORAGE_KEYS.DISPLAY_ALL_COLUMNS,
    [],
  );

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

  useEffect(() => {
    if (onSort) {
      const columnSort = tableInstance.getState().sorting;
      onSort(columnSort[0]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tableInstance.getState().sorting]);

  return (
    <TableContainer
      data-testid="fidesTable"
      overflowY={overflow}
      overflowX={overflow}
      borderColor="gray.200"
      borderBottomWidth="1px"
      borderRightWidth="1px"
      borderLeftWidth="1px"
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
                  borderColor="gray.200"
                  borderTopWidth="1px"
                  borderBottomWidth="1px"
                  borderRightWidth="1px"
                  _last={{
                    borderRightWidth: 0,
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
                    enableSorting={enableSorting}
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
            emptyTableNotice={emptyTableNotice}
          />
        ) : (
          <TableBody
            tableInstance={tableInstance}
            rowActionBar={rowActionBar}
            onRowClick={onRowClick}
            renderRowTooltipLabel={renderRowTooltipLabel}
            displayAllColumns={displayAllColumns}
            emptyTableNotice={emptyTableNotice}
          />
        )}
        {footer}
      </Table>
    </TableContainer>
  );
};
