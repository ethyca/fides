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
  Checkbox,
  HStack,
  Menu,
  MenuButton,
  MenuDivider,
  MenuItem,
  MenuList,
  MoreIcon,
  Portal,
  SmallCloseIcon,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  theme,
  Tr,
} from "fidesui";
import React, { ReactNode, useEffect, useMemo, useState } from "react";

import { useLocalStorage } from "~/features/common/hooks/useLocalStorage";
import { DisplayAllIcon, GroupedIcon } from "~/features/common/Icon";
import { FidesRow } from "~/features/common/table/v2/FidesRow";
import {
  COLUMN_VERSION_DELIMITER,
  columnExpandedVersion,
  getTableTHandTDStyles,
} from "~/features/common/table/v2/util";

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
    showHeaderMenu?: boolean;
    showHeaderMenuWrapOption?: boolean;
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
  onExpandAll: (id: string) => void;
  onWrapToggle: (id: string, doWrap: boolean) => void;
  isExpandAll: boolean;
  isWrapped: boolean;
  enableSorting: boolean;
}
const HeaderContent = <T,>({
  header,
  onGroupAll,
  onExpandAll,
  onWrapToggle,
  isExpandAll,
  isWrapped,
  enableSorting,
}: HeaderContentProps<T>) => {
  const { meta } = header.column.columnDef;
  if (!meta?.showHeaderMenu) {
    if (enableSorting && header.column.getCanSort()) {
      // TODO PROD-2567 - leaving this as a Chakra button for now, but should
      // be migrated to AntButton as part of table migration
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
    <Menu placement="bottom-end" closeOnSelect={!meta.showHeaderMenuWrapOption}>
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
            color={isExpandAll ? "complimentary.500" : undefined}
            onClick={() => onExpandAll(header.id)}
          >
            <DisplayAllIcon /> Expand all
          </MenuItem>
          <MenuItem
            gap={2}
            color={!isExpandAll ? "complimentary.500" : undefined}
            onClick={() => onGroupAll(header.id)}
          >
            <GroupedIcon /> Collapse all
          </MenuItem>
          {enableSorting && header.column.getCanSort() && (
            <MenuItem gap={2} onClick={header.column.getToggleSortingHandler()}>
              {sortingDisplay[header.column.getNextSortingOrder() as string]
                ?.icon ?? <SmallCloseIcon />}
              {sortingDisplay[header.column.getNextSortingOrder() as string]
                ?.title ?? "Clear sort"}
            </MenuItem>
          )}
          {meta.showHeaderMenuWrapOption && (
            <>
              <MenuDivider />
              <Box px={3}>
                <Checkbox
                  size="sm"
                  isChecked={isWrapped}
                  onChange={() => onWrapToggle(header.id, !isWrapped)}
                  colorScheme="complimentary"
                >
                  <Text fontSize="xs">Wrap results</Text>
                </Checkbox>
              </Box>
            </>
          )}
        </MenuList>
      </Portal>
    </Menu>
  );
};

type FidesTableProps<T> = {
  tableInstance: TableInstance<T>;
  rowActionBar?: ReactNode;
  footer?: ReactNode;
  onRowClick?: (row: T, e: React.MouseEvent<HTMLTableCellElement>) => void;
  /**
   * Optional function to filter whether onRowClick should be enabled based on
   * the row data.  If not provided, onRowClick will be enabled for all rows.
   */
  getRowIsClickable?: (row: T) => boolean;
  renderRowTooltipLabel?: (row: Row<T>) => string | undefined;
  emptyTableNotice?: ReactNode;
  overflow?: "auto" | "visible" | "hidden";
  enableSorting?: boolean;
  onSort?: (columnSort: ColumnSort) => void;
  columnExpandStorageKey?: string;
  columnWrapStorageKey?: string;
};

const TableBody = <T,>({
  tableInstance,
  rowActionBar,
  onRowClick,
  getRowIsClickable,
  renderRowTooltipLabel,
  expandedColumns,
  wrappedColumns,
  emptyTableNotice,
}: Omit<FidesTableProps<T>, "footer" | "enableSorting" | "onSort"> & {
  expandedColumns: string[];
  wrappedColumns: string[];
}) => {
  const getRowClickHandler = (row: T) => {
    if (!getRowIsClickable) {
      return onRowClick;
    }
    return getRowIsClickable(row) ? onRowClick : undefined;
  };

  return (
    <Tbody data-testid="fidesTable-body">
      {rowActionBar}
      {tableInstance.getRowModel().rows.map((row) => (
        <FidesRow<T>
          key={row.id}
          row={row}
          onRowClick={getRowClickHandler(row.original)}
          renderRowTooltipLabel={renderRowTooltipLabel}
          expandedColumns={expandedColumns}
          wrappedColumns={wrappedColumns}
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
};

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
  getRowIsClickable,
  renderRowTooltipLabel,
  emptyTableNotice,
  overflow = "auto",
  onSort,
  enableSorting = !!onSort,
  columnExpandStorageKey,
  columnWrapStorageKey,
}: FidesTableProps<T>) => {
  const [colExpandVersion, setColExpandVersion] = useState<number>(1);
  const [expandedColumns, setExpandedColumns] = useLocalStorage<string[]>(
    columnExpandStorageKey,
    [],
  );
  const [wrappedColumns, setWrappedColumns] = useLocalStorage<string[]>(
    columnWrapStorageKey,
    [],
  );

  const handleColumnExpand = (id: string) => {
    const newExpandedColumns = expandedColumns.filter(
      (c) => c.split(COLUMN_VERSION_DELIMITER)[0] !== id,
    );
    setExpandedColumns([
      ...newExpandedColumns,
      `${id}${COLUMN_VERSION_DELIMITER}${colExpandVersion}`,
    ]);
    setColExpandVersion(colExpandVersion + 1);
  };
  const handleColumnCollapse = (id: string) => {
    const newExpandedColumns = expandedColumns.filter(
      (c) => c.split(COLUMN_VERSION_DELIMITER)[0] !== id,
    );
    setExpandedColumns([
      ...newExpandedColumns,
      `${id}${COLUMN_VERSION_DELIMITER}${colExpandVersion * -1}`,
    ]);
    setColExpandVersion(colExpandVersion + 1);
  };
  const handleColumnWrap = (id: string, doWrap: boolean) => {
    setWrappedColumns(
      doWrap ? [...wrappedColumns, id] : wrappedColumns.filter((c) => c !== id),
    );
  };

  // From https://tanstack.com/table/v8/docs/examples/react/column-resizing-performant
  // To optimize resizing performance
  const columnSizeVars = useMemo(() => {
    const headers = tableInstance.getFlatHeaders();
    const colSizes: { [key: string]: number } = {};
    for (let i = 0; i < headers.length; i += 1) {
      const header = headers[i]!;
      const columnHasBeenResized =
        !!tableInstance.getState().columnSizing?.[header.id];
      const initialWidthSetting = header.column.columnDef.meta?.width;
      const columnIsAuto = initialWidthSetting === "auto";
      if (!columnHasBeenResized && columnIsAuto) {
        setTimeout(() => {
          // wait for DOM rendering to get the actual width
          const autoWidth = document.getElementById(
            `column-${header.id}`,
          )?.offsetWidth;
          if (autoWidth) {
            // set the column size to the actual width
            // if we don't do this, the column will jank when resizing
            tableInstance.setColumnSizing((updater) => {
              return { ...updater, [header.id]: autoWidth };
            });
            colSizes[`--header-${header.id}-size`] = autoWidth;
            colSizes[`--col-${header.column.id}-size`] = autoWidth;
          }
        });
      } else {
        colSizes[`--header-${header.id}-size`] = header.getSize();
        colSizes[`--col-${header.column.id}-size`] = header.column.getSize();
      }
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
              {headerGroup.headers.map((header) => {
                const v = columnExpandedVersion(header.id, expandedColumns);
                const colIsExpanded = !!v && v > 0;
                return (
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
                    id={`column-${header.id}`}
                    sx={{
                      padding: 0,
                      width: `calc(var(--header-${header.id}-size) * 1px)`,
                      overflowX: "auto",
                    }}
                    textTransform="unset"
                    position="relative"
                    _hover={{
                      "& .resizer": {
                        opacity: 1,
                      },
                    }}
                  >
                    <HeaderContent
                      header={header}
                      onGroupAll={handleColumnCollapse}
                      onExpandAll={handleColumnExpand}
                      onWrapToggle={handleColumnWrap}
                      isExpandAll={colIsExpanded}
                      isWrapped={!!wrappedColumns.find((c) => header.id === c)}
                      enableSorting={enableSorting}
                    />
                    {/* Capture area to render resizer cursor */}
                    {header.column.getCanResize() ? (
                      <Box
                        onDoubleClick={() => header.column.resetSize()}
                        onMouseDown={header.getResizeHandler()}
                        position="absolute"
                        height="100%"
                        top="0"
                        right="0"
                        width="5px"
                        cursor="col-resize"
                        userSelect="none"
                        // eslint-disable-next-line tailwindcss/no-custom-classname
                        className="resizer"
                        opacity={0}
                        backgroundColor={
                          header.column.getIsResizing()
                            ? "complimentary.500"
                            : "gray.200"
                        }
                      />
                    ) : null}
                  </Th>
                );
              })}
            </Tr>
          ))}
        </Thead>
        {tableInstance.getState().columnSizingInfo.isResizingColumn ? (
          <MemoizedTableBody
            tableInstance={tableInstance}
            rowActionBar={rowActionBar}
            onRowClick={onRowClick}
            getRowIsClickable={getRowIsClickable}
            renderRowTooltipLabel={renderRowTooltipLabel}
            expandedColumns={expandedColumns}
            wrappedColumns={wrappedColumns}
            emptyTableNotice={emptyTableNotice}
          />
        ) : (
          <TableBody
            tableInstance={tableInstance}
            rowActionBar={rowActionBar}
            onRowClick={onRowClick}
            getRowIsClickable={getRowIsClickable}
            renderRowTooltipLabel={renderRowTooltipLabel}
            expandedColumns={expandedColumns}
            wrappedColumns={wrappedColumns}
            emptyTableNotice={emptyTableNotice}
          />
        )}
        {footer}
      </Table>
    </TableContainer>
  );
};
