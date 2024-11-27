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
import { useEffect, useMemo, useState } from "react";

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
import { useGetProjectsQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import IconLegendTooltip from "~/features/data-discovery-and-detection/IndicatorLegend";
import { SearchInput } from "~/features/data-discovery-and-detection/SearchInput";
import useSpoofGetProjectsQuery, {
  DatasetLifecycleProject,
} from "~/features/dataset-lifecycle/projects/useSpoofGetProjectsQuery";
import StatusBadgeCell from "~/features/dataset-lifecycle/StatusBadgeCell";
import SystemActionsCell from "~/features/dataset-lifecycle/systems/SystemActionCell";

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

const columnHelper = createColumnHelper<DatasetLifecycleProject>();

const ProjectsTable = ({
  monitor_config_id,
}: {
  monitor_config_id?: string;
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
  } = useGetProjectsQuery({
    page: pageIndex,
    size: pageSize,
    monitor_config_id: "bq-monitor",
  });

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => queryResult ?? EMPTY_RESPONSE, [queryResult]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const columns: ColumnDef<DatasetLifecycleProject, any>[] = useMemo(
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
        },
      }),
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: "Name",
      }),
      columnHelper.accessor((row) => row.status, {
        id: "status",
        cell: (props) => <StatusBadgeCell statusResult={props.getValue()} />,
        header: "Status",
      }),
      columnHelper.accessor((row) => row.lastUpdated, {
        id: "lastUpdated",
        cell: (props) => <RelativeTimestampCell time={props.getValue()} />,
        header: "Last Updated",
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
            onHideClick={() =>
              console.log(`hiding project ${props.row.original.urn}...`)
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

  const tableInstance = useReactTable<DatasetLifecycleProject>({
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

  const handleBulkHide = () => {
    console.log(`hiding projects ${selectedRowIds.join(", ")}...`);
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
        onRowClick={() => console.log("row clicked")}
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

export default ProjectsTable;
