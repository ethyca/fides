/* eslint-disable react/no-unstable-nested-components */

import { Box, Text, VStack } from "@fidesui/react";
import {
  ColumnDef,
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  RowSelectionState,
  useReactTable,
} from "@tanstack/react-table";
import { useEffect, useMemo, useState } from "react";
import SearchBar from "~/features/common/SearchBar";

import {
  FidesTableV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { useGetMonitorResultsQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import useDiscoveryResultColumns from "~/features/data-discovery-and-detection/hooks/useDiscoveryResultColumns";
import useDiscoveryRoutes from "~/features/data-discovery-and-detection/hooks/useDiscoveryRoutes";
import DiscoveryBulkActions from "~/features/data-discovery-and-detection/tables/DiscoveryBulkActions";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";
import { StagedResourceType } from "~/features/data-discovery-and-detection/types/StagedResourceType";
import { findResourceType } from "~/features/data-discovery-and-detection/utils/findResourceType";
import { DiffStatus, StagedResource } from "~/types/api";
import SearchInput from "../SearchInput";

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

interface MonitorResultTableProps {
  resourceUrn: string;
}

const DiscoveryResultTable = ({ resourceUrn }: MonitorResultTableProps) => {
  const diffStatusFilter: DiffStatus[] = [
    DiffStatus.CLASSIFICATION_ADDITION,
    DiffStatus.CLASSIFICATION_UPDATE,
  ];

  const childDiffStatusFilter: DiffStatus[] = [
    DiffStatus.CLASSIFICATION_ADDITION,
    DiffStatus.CLASSIFICATION_UPDATE,
  ];

  const [searchQuery, setSearchQuery] = useState("");
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});

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
    staged_resource_urn: resourceUrn,
    page: pageIndex,
    size: pageSize,
    child_diff_status: childDiffStatusFilter,
    diff_status: diffStatusFilter,
    search: searchQuery,
  });

  const resourceType = findResourceType(
    resources?.items[0] as DiscoveryMonitorItem
  );

  const isField = resourceType === StagedResourceType.FIELD;

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => resources ?? EMPTY_RESPONSE, [resources]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const { columns } = useDiscoveryResultColumns({ resourceType });

  const resourceColumns: ColumnDef<StagedResource, any>[] = useMemo(
    () => columns,
    [columns]
  );

  const { navigateToDiscoveryResults } = useDiscoveryRoutes();

  const handleRowClicked = !isField
    ? (row: StagedResource) =>
        navigateToDiscoveryResults({ resourceUrn: row.urn })
    : undefined;

  const tableInstance = useReactTable<StagedResource>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    columns: resourceColumns,
    manualPagination: true,
    onRowSelectionChange: setRowSelection,
    state: {
      rowSelection,
    },
    getRowId: (row) => row.urn,
    data,
  });

  if (isLoading) {
    return <TableSkeletonLoader rowHeight={36} numRows={36} />;
  }

  return (
    <>
      <TableActionBar>
        <Box w="full" maxW={64}>
          <SearchInput value={searchQuery} onChange={setSearchQuery} />
        </Box>
        <DiscoveryBulkActions
          resourceType={resourceType}
          resourceUrn={resourceUrn}
        />
      </TableActionBar>
      <FidesTableV2
        tableInstance={tableInstance}
        onRowClick={handleRowClicked}
        emptyTableNotice={<EmptyTableNotice />}
        overflow="visible"
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

export default DiscoveryResultTable;
