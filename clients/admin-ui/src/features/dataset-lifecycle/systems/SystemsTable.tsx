/* eslint-disable react/no-unstable-nested-components */

import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  RowSelectionState,
  useReactTable,
} from "@tanstack/react-table";
import {
  AntButton,
  Box,
  Flex,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Text,
  VStack,
} from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";

import { E2E_DATASETS_ROUTE } from "~/features/common/nav/v2/routes";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import {
  IndeterminateCheckboxCell,
  RelativeTimestampCell,
} from "~/features/common/table/v2/cells";
import IconLegendTooltip from "~/features/data-discovery-and-detection/IndicatorLegend";
import { SearchInput } from "~/features/data-discovery-and-detection/SearchInput";
import StatusBadgeCell from "~/features/dataset-lifecycle/StatusBadgeCell";
import SystemActionsCell from "~/features/dataset-lifecycle/systems/SystemActionCell";
import systemHasHeliosIntegration from "~/features/dataset-lifecycle/systems/systemHasHeliosIntegration";
import SystemNameCell from "~/features/dataset-lifecycle/systems/SystemNameCell";
import useSpoofGetSystemsQuery, {
  DatasetLifecycleSystem,
} from "~/features/dataset-lifecycle/systems/useSpoofGetSystemsQuery";

const EMPTY_RESPONSE = {
  items: [],
  total: 0,
  page: 1,
  size: 50,
  pages: 1,
};

const columnHelper = createColumnHelper<DatasetLifecycleSystem>();

const EmptyTableNotice = () => (
  <VStack
    mt={6}
    p={10}
    spacing={4}
    borderRadius="base"
    maxW="70%"
    data-testid="empty-state"
    alignSelf="center"
    margin="auto"
  >
    <VStack>
      <Text fontSize="md" fontWeight="600">
        No systems found
      </Text>
      <Text fontSize="sm">You&apos;re up to date!</Text>
    </VStack>
  </VStack>
);

const SystemsTable = () => {
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [rowSelectionState, setRowSelectionState] = useState<RowSelectionState>(
    {},
  );

  const router = useRouter();

  const {
    PAGE_SIZES,
    pageSize,
    setPageSize,
    onPreviousPageClick,
    isPreviousPageDisabled,
    onNextPageClick,
    isNextPageDisabled,
    startRange,
    endRange,
    pageIndex,
    setTotalPages,
  } = useServerSidePagination();

  const {
    isFetching,
    isLoading,
    data: queryResult,
  } = useSpoofGetSystemsQuery({
    pageIndex,
    pageSize,
    searchQuery,
  });

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => queryResult ?? EMPTY_RESPONSE, [queryResult]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const columns: ColumnDef<DatasetLifecycleSystem, any>[] = useMemo(
    () => [
      columnHelper.display({
        id: "select",
        cell: ({ row }) => (
          <IndeterminateCheckboxCell
            isChecked={row.getIsSelected()}
            onChange={row.getToggleSelectedHandler()}
            dataTestId={`select-row-${row.id}`}
          />
        ),
        header: ({ table }) => (
          <IndeterminateCheckboxCell
            isChecked={table.getIsAllPageRowsSelected()}
            isIndeterminate={table.getIsSomeRowsSelected()}
            onChange={table.getToggleAllRowsSelectedHandler()}
            dataTestId="select-all-rows"
          />
        ),
        maxSize: 25,
        enableResizing: false,
        meta: {
          cellProps: {
            borderRight: "none",
          },
        },
      }),
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: ({ row, getValue }) => (
          <SystemNameCell
            value={getValue()}
            clickable={systemHasHeliosIntegration(row.original)}
          />
        ),
        header: (props) => <DefaultHeaderCell value="Name" {...props} />,
      }),
      columnHelper.accessor((row) => row.status, {
        id: "status",
        cell: ({ getValue }) => <StatusBadgeCell statusResult={getValue()} />,
        header: (props) => <DefaultHeaderCell value="Status" {...props} />,
      }),
      columnHelper.accessor((row) => row.changes, {
        id: "changes",
        cell: ({ getValue }) => <DefaultCell value={getValue()} />,
        header: (props) => <DefaultHeaderCell value="Changes" {...props} />,
      }),
      columnHelper.accessor((row) => row.lastUpdated, {
        id: "updated-at",
        cell: ({ getValue }) => <RelativeTimestampCell time={getValue()} />,
        header: (props) => <DefaultHeaderCell value="When" {...props} />,
      }),
      columnHelper.accessor((row) => row.dataUses, {
        id: "data-uses",
        cell: ({ getValue }) => <DefaultCell value={getValue().join(", ")} />,
        header: (props) => <DefaultHeaderCell value="Data uses" {...props} />,
        meta: {
          cellProps: {
            borderRight: "none",
          },
        },
      }),
      columnHelper.display({
        id: "actions",
        cell: (props) => (
          <SystemActionsCell
            onDetailClick={() =>
              router.push(`/systems/configure/${props.row.original.id}`)
            }
            onHideClick={() =>
              console.log(`hiding system ${props.row.original.id}...`)
            }
          />
        ),
        maxSize: 20,
        enableResizing: false,
        meta: {
          cellProps: {
            borderLeft: "none",
          },
        },
      }),
    ],
    [],
  );

  const tableInstance = useReactTable<DatasetLifecycleSystem>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    getRowId: (row) => row.id,
    manualPagination: true,
    columnResizeMode: "onChange",
    columns,
    data,
    onRowSelectionChange: setRowSelectionState,
    state: {
      rowSelection: rowSelectionState,
    },
  });

  const selectedRowIds = Object.keys(rowSelectionState).filter(
    (k) => rowSelectionState[k],
  );

  const handleBulkAddDataUse = () => {
    console.log(`adding a data use to systems ${selectedRowIds.join(", ")}...`);
    setRowSelectionState({});
  };

  const handleBulkHide = () => {
    console.log(`hiding systems ${selectedRowIds.join(", ")}...`);
    setRowSelectionState({});
  };

  if (isLoading || isFetching) {
    return <TableSkeletonLoader rowHeight={36} numRows={36} />;
  }

  return (
    <>
      <TableActionBar>
        <Flex gap={6} align="center">
          <Box flexShrink={0}>
            <SearchInput value={searchQuery} onChange={setSearchQuery} />
          </Box>
          <IconLegendTooltip />
        </Flex>
        <Menu size="xs">
          <MenuButton
            as={AntButton}
            size="small"
            disabled={!selectedRowIds.length}
          >
            Actions
          </MenuButton>
          <MenuList>
            <MenuItem onClick={handleBulkAddDataUse}>Add data use</MenuItem>
            <MenuItem onClick={handleBulkHide}>Hide</MenuItem>
          </MenuList>
        </Menu>
      </TableActionBar>
      <FidesTableV2
        tableInstance={tableInstance}
        emptyTableNotice={<EmptyTableNotice />}
        getRowIsClickable={systemHasHeliosIntegration}
        onRowClick={(row) => router.push(`${E2E_DATASETS_ROUTE}/${row.id}`)}
      />
      <PaginationBar
        totalRows={totalRows || 0}
        pageSizes={PAGE_SIZES}
        setPageSize={setPageSize}
        onPreviousPageClick={onPreviousPageClick}
        isPreviousPageDisabled={isPreviousPageDisabled}
        onNextPageClick={onNextPageClick}
        isNextPageDisabled={isNextPageDisabled}
        startRange={startRange}
        endRange={endRange}
      />
    </>
  );
};

export default SystemsTable;
