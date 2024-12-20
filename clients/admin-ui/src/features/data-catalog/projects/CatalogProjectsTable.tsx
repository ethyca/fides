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
  FidesTableV2,
  IndeterminateCheckboxCell,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { RelativeTimestampCell } from "~/features/common/table/v2/cells";
import CatalogResourceNameCell from "~/features/data-catalog/CatalogResourceNameCell";
import CatalogStatusBadgeCell from "~/features/data-catalog/CatalogStatusBadgeCell";
import { useGetCatalogProjectsQuery } from "~/features/data-catalog/data-catalog.slice";
import SystemActionsCell from "~/features/data-catalog/systems/SystemActionCell";
import { getCatalogResourceStatus } from "~/features/data-catalog/utils";
import { useMuteResourcesMutation } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import IconLegendTooltip from "~/features/data-discovery-and-detection/IndicatorLegend";
import { SearchInput } from "~/features/data-discovery-and-detection/SearchInput";
import { StagedResourceAPIResponse } from "~/types/api";

const EMPTY_RESPONSE = {
  items: [],
  total: 0,
  page: 1,
  size: 50,
  pages: 1,
};

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

const columnHelper = createColumnHelper<StagedResourceAPIResponse>();

const CatalogProjectsTable = ({
  systemKey,
  monitorConfigIds,
}: {
  systemKey: string;
  monitorConfigIds: string[];
}) => {
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [rowSelectionState, setRowSelectionState] = useState<RowSelectionState>(
    {},
  );

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
  } = useGetCatalogProjectsQuery({
    page: pageIndex,
    size: pageSize,
    monitor_config_ids: monitorConfigIds,
  });

  const router = useRouter();

  const [hideProjects] = useMuteResourcesMutation();

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => queryResult ?? EMPTY_RESPONSE, [queryResult]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const columns: ColumnDef<StagedResourceAPIResponse, any>[] = useMemo(
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
            onChange={table.getToggleAllPageRowsSelectedHandler()}
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
        cell: (props) => (
          <CatalogResourceNameCell resource={props.row.original} />
        ),
        header: "Project",
      }),
      columnHelper.display({
        id: "status",
        cell: ({ row }) => (
          <CatalogStatusBadgeCell
            status={getCatalogResourceStatus(row.original)}
          />
        ),
        header: "Status",
      }),
      columnHelper.accessor((row) => row.monitor_config_id, {
        id: "monitorConfigId",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: "Detected by",
      }),
      columnHelper.accessor((row) => row.description, {
        id: "description",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: "Description",
      }),
      columnHelper.accessor((row) => row.updated_at, {
        id: "lastUpdated",
        cell: (props) => <RelativeTimestampCell time={props.getValue()} />,
        header: "Updated",
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
            onHideClick={async () => {
              await hideProjects({ staged_resource_urns: [props.row.id] });
            }}
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
    [hideProjects],
  );

  const tableInstance = useReactTable<StagedResourceAPIResponse>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    manualPagination: true,
    columnResizeMode: "onChange",
    columns,
    data,
    onRowSelectionChange: setRowSelectionState,
    state: {
      rowSelection: rowSelectionState,
    },
  });

  const selectedRowIds = Object.keys(rowSelectionState);

  const handleBulkHide = async () => {
    await hideProjects({ staged_resource_urns: selectedRowIds });
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
            <MenuItem onClick={handleBulkHide}>Hide</MenuItem>
          </MenuList>
        </Menu>
      </TableActionBar>
      <FidesTableV2
        tableInstance={tableInstance}
        emptyTableNotice={<EmptyTableNotice />}
        onRowClick={(row) =>
          router.push(`${DATA_CATALOG_ROUTE}/${systemKey}/projects/${row.urn}`)
        }
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

export default CatalogProjectsTable;
