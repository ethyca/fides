/* eslint-disable react/no-unstable-nested-components */

import { Text, VStack } from "@fidesui/react";
import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useEffect, useMemo } from "react";

import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  PaginationBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { useGetAllMonitorsQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { DiscoveryMonitorConfig } from "~/types/api";

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
        No monitors available.
      </Text>
      <Text fontSize="sm">[insert some copy about how to add a monitor]</Text>
    </VStack>
  </VStack>
);

const columnHelper = createColumnHelper<DiscoveryMonitorConfig>();

const TestMonitorTable = ({
  viewMonitorResults,
}: {
  viewMonitorResults: (monitor: DiscoveryMonitorConfig) => void;
}) => {
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
    data: monitors,
  } = useGetAllMonitorsQuery({
    page: pageIndex,
    size: pageSize,
  });

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => monitors ?? EMPTY_RESPONSE, [monitors]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const monitorColumns: ColumnDef<DiscoveryMonitorConfig, any>[] = useMemo(
    () => [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Name" {...props} />,
      }),
      columnHelper.accessor((row) => row.type, {
        id: "type",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Type" {...props} />,
      }),
      columnHelper.accessor((row) => row.monitor_frequency, {
        id: "monitor_frequency",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Frequency" {...props} />,
      }),
      columnHelper.accessor((row) => row.data_steward, {
        id: "data_steward",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Data Steward" {...props} />
        ),
      }),
    ],
    []
  );

  const tableInstance = useReactTable<DiscoveryMonitorConfig>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    columns: monitorColumns,
    manualPagination: true,
    data,
  });

  if (isLoading) {
    return <TableSkeletonLoader rowHeight={36} numRows={5} />;
  }

  return (
    <>
      <FidesTableV2
        tableInstance={tableInstance}
        onRowClick={viewMonitorResults}
        emptyTableNotice={<EmptyTableNotice />}
      />
      <PaginationBar
        totalRows={totalRows}
        pageSizes={PAGE_SIZES}
        setPageSize={setPageSize}
        onPreviousPageClick={onPreviousPageClick}
        isPreviousPageDisabled={isPreviousPageDisabled || isFetching}
        onNextPageClick={onNextPageClick}
        isNextPageDisabled={isNextPageDisabled || isFetching}
        startRange={startRange}
        endRange={endRange}
      />
    </>
  );
};

export default TestMonitorTable;
