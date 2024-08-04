/* eslint-disable react/no-unstable-nested-components */

import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Box, Flex, Text, VStack } from "fidesui";
import { useEffect, useMemo, useState } from "react";

import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { RelativeTimestampCell } from "~/features/common/table/v2/cells";
import { useGetMonitorResultsQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import IconLegendTooltip from "~/features/data-discovery-and-detection/IndicatorLegend";
import ResultStatusBadgeCell from "~/features/data-discovery-and-detection/tables/ResultStatusBadgeCell";
import ResultStatusCell from "~/features/data-discovery-and-detection/tables/ResultStatusCell";
import getResourceRowName from "~/features/data-discovery-and-detection/utils/getResourceRowName";
import { Database, DiffStatus, StagedResource } from "~/types/api";

import DetectionItemAction from "../DetectionItemActions";
import DiscoveryItemActions from "../DiscoveryItemActions";
import { SearchInput } from "../SearchInput";
import { ResourceActivityTypeEnum } from "../types/ResourceActivityTypeEnum";
import findProjectFromUrn from "../utils/findProjectFromUrn";
import findActivityType from "../utils/getResourceActivityLabel";

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
        No activity found
      </Text>
      <Text fontSize="sm">You&apos;re up to date!</Text>
    </VStack>
  </VStack>
);

const columnHelper = createColumnHelper<Database>();

interface ActivityTableProps {
  onRowClick: (resource: StagedResource) => void;
  statusFilters?: DiffStatus[];
  childsStatusFilters?: DiffStatus[];
}

const ActivityTable = ({
  onRowClick,
  statusFilters,
  childsStatusFilters,
}: ActivityTableProps) => {
  const [searchQuery, setSearchQuery] = useState("");

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
    data: resources,
  } = useGetMonitorResultsQuery({
    diff_status: statusFilters,
    child_diff_status: childsStatusFilters,
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
  });

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => resources ?? EMPTY_RESPONSE, [resources]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const resourceColumns: ColumnDef<StagedResource, any>[] = useMemo(
    () => [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => <ResultStatusCell result={props.row.original} />,
        header: (props) => <DefaultHeaderCell value="Name" {...props} />,
      }),
      columnHelper.accessor((row) => row.urn, {
        id: "project",
        cell: (props) => (
          <DefaultCell value={findProjectFromUrn(props.getValue())} />
        ),
        header: (props) => <DefaultHeaderCell value="Project" {...props} />,
      }),
      columnHelper.display({
        id: "status",
        cell: (props) => <ResultStatusBadgeCell result={props.row.original} />,
        header: (props) => <DefaultHeaderCell value="Status" {...props} />,
      }),
      columnHelper.accessor((resource) => findActivityType(resource), {
        id: "type",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Type" {...props} />,
      }),
      columnHelper.accessor((row) => row.monitor_config_id, {
        id: "monitor",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Detected by" {...props} />,
      }),
      columnHelper.accessor((row) => row.source_modified, {
        id: "time",
        cell: (props) => <RelativeTimestampCell time={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="When" {...props} />,
      }),
      columnHelper.accessor((row) => row, {
        id: "action",
        cell: (props) =>
          findActivityType(props.getValue()) ===
          ResourceActivityTypeEnum.DATASET ? (
            <DetectionItemAction resource={props.getValue()} />
          ) : (
            <DiscoveryItemActions resource={props.getValue()} />
          ),
        header: (props) => <DefaultHeaderCell value="Action" {...props} />,
      }),
    ],
    [],
  );

  const tableInstance = useReactTable<StagedResource>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    getRowId: getResourceRowName,
    columns: resourceColumns,
    manualPagination: true,
    data,
  });

  if (isLoading) {
    return <TableSkeletonLoader rowHeight={36} numRows={36} />;
  }

  return (
    <>
      <TableActionBar>
        <Flex gap={6} align="center">
          <Box w={400} flexShrink={0}>
            <SearchInput value={searchQuery} onChange={setSearchQuery} />
          </Box>
          <IconLegendTooltip />
        </Flex>
      </TableActionBar>
      <FidesTableV2
        tableInstance={tableInstance}
        onRowClick={onRowClick}
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

export default ActivityTable;
