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

import { DATA_CATALOG_ROUTE } from "~/features/common/nav/v2/routes";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { IndeterminateCheckboxCell } from "~/features/common/table/v2/cells";
import { getQueryParamsFromArray } from "~/features/common/utils";
import { useGetCatalogSystemsQuery } from "~/features/data-catalog/data-catalog.slice";
import SystemActionsCell from "~/features/data-catalog/systems/SystemActionCell";
import { useLazyGetAvailableDatabasesByConnectionQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import IconLegendTooltip from "~/features/data-discovery-and-detection/IndicatorLegend";
import { SearchInput } from "~/features/data-discovery-and-detection/SearchInput";
import { SystemWithMonitorKeys } from "~/types/api";

const EMPTY_RESPONSE = {
  items: [],
  total: 0,
  page: 1,
  size: 50,
  pages: 1,
};

const columnHelper = createColumnHelper<SystemWithMonitorKeys>();

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
    data: queryResult,
    isLoading,
    isFetching,
  } = useGetCatalogSystemsQuery({
    page: pageIndex,
    size: pageSize,
    show_hidden: false,
  });

  const [getProjects] = useLazyGetAvailableDatabasesByConnectionQuery();

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => queryResult ?? EMPTY_RESPONSE, [queryResult]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const handleRowClicked = async (row: SystemWithMonitorKeys) => {
    // if there are projects, go to project view; otherwise go to datasets view
    const projectsResponse = await getProjects({
      connection_config_key: row.connection_configs!.key,
      page: 1,
      size: 1,
    });

    const hasProjects = !!projectsResponse?.data?.total;
    const queryString = getQueryParamsFromArray(
      row.monitor_config_keys ?? [],
      "monitor_config_ids",
    );

    const url = `${DATA_CATALOG_ROUTE}/${row.fides_key}${hasProjects ? "/projects" : ""}?${queryString}`;
    router.push(url);
  };

  const columns: ColumnDef<SystemWithMonitorKeys, any>[] = useMemo(
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
          disableRowClick: true,
        },
      }),
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: ({ getValue, row }) => (
          <DefaultCell
            value={getValue()}
            fontWeight={
              row.original.connection_configs?.key ? "semibold" : "normal"
            }
          />
        ),
        header: (props) => <DefaultHeaderCell value="Name" {...props} />,
      }),
      // columnHelper.display({
      //   id: "data-uses",
      //   cell: ({ row }) => <EditDataUseCell system={row.original} />,
      //   header: (props) => <DefaultHeaderCell value="Data uses" {...props} />,
      //   meta: {
      //     disableRowClick: true,
      //   },
      //   minSize: 280,
      // }),
      columnHelper.display({
        id: "actions",
        cell: (props) => (
          <SystemActionsCell
            onDetailClick={() =>
              router.push(`/systems/configure/${props.row.original.fides_key}`)
            }
          />
        ),
        maxSize: 20,
        enableResizing: false,
        meta: {
          cellProps: {
            borderLeft: "none",
          },
          disableRowClick: true,
        },
      }),
    ],
    [router],
  );

  const tableInstance = useReactTable<SystemWithMonitorKeys>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    getRowId: (row) => row.fides_key,
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
        {/* <Menu size="xs">
          <MenuButton
            as={AntButton}
            size="small"
            disabled={!selectedRowIds.length}
          >
            Actions
          </MenuButton>
          <MenuList>
            <MenuItem onClick={handleBulkAddDataUse}>Add data use</MenuItem>
          </MenuList>
        </Menu> */}
      </TableActionBar>
      <FidesTableV2
        tableInstance={tableInstance}
        emptyTableNotice={<EmptyTableNotice />}
        onRowClick={handleRowClicked}
        getRowIsClickable={(row) => !!row.connection_configs?.key}
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
