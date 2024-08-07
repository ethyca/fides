/* eslint-disable react/no-unstable-nested-components */

import {
  ColumnDef,
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Box, Flex, Switch, Text, VStack } from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";

import {
  FidesTableV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { useGetMonitorResultsQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import useDetectionResultColumns from "~/features/data-discovery-and-detection/hooks/useDetectionResultColumns";
import useDiscoveryRoutes from "~/features/data-discovery-and-detection/hooks/useDiscoveryRoutes";
import IconLegendTooltip from "~/features/data-discovery-and-detection/IndicatorLegend";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";
import { StagedResourceType } from "~/features/data-discovery-and-detection/types/StagedResourceType";
import { findResourceType } from "~/features/data-discovery-and-detection/utils/findResourceType";
import getResourceRowName from "~/features/data-discovery-and-detection/utils/getResourceRowName";
import { DiffStatus, StagedResource } from "~/types/api";

import { SearchInput } from "../SearchInput";

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
  resourceUrn?: string;
}

const DetectionResultTable = ({ resourceUrn }: MonitorResultTableProps) => {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");

  const [isShowingFullSchema, setIsShowingFullSchema] = useState<boolean>(
    router.query?.showFullSchema === "true" || false,
  );

  const diffStatusFilter: DiffStatus[] = [
    DiffStatus.ADDITION,
    DiffStatus.REMOVAL,
  ];
  if (isShowingFullSchema) {
    diffStatusFilter.push(DiffStatus.MONITORED);
    diffStatusFilter.push(DiffStatus.MUTED);
  }

  const childDiffStatusFilter: DiffStatus[] = [
    DiffStatus.ADDITION,
    DiffStatus.REMOVAL,
  ];
  if (isShowingFullSchema) {
    childDiffStatusFilter.push(DiffStatus.MONITORED);
    childDiffStatusFilter.push(DiffStatus.MUTED);
  }

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
    resources?.items[0] as DiscoveryMonitorItem,
  );

  const { columns } = useDetectionResultColumns({ resourceType });

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => resources ?? EMPTY_RESPONSE, [resources]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const resourceColumns: ColumnDef<StagedResource, any>[] = useMemo(
    () => columns,
    [columns],
  );

  const { navigateToDetectionResults } = useDiscoveryRoutes();

  const handleRowClicked =
    resourceType !== StagedResourceType.FIELD
      ? (row: StagedResource) =>
          navigateToDetectionResults({
            resourceUrn: row.urn,
            showFullSchema: isShowingFullSchema,
          })
      : undefined;

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
        <Flex
          direction="row"
          alignItems="center"
          justifyContent="space-between"
          width="full"
        >
          <Flex gap={6} align="center">
            <Box w={400} flexShrink={0}>
              <SearchInput value={searchQuery} onChange={setSearchQuery} />
            </Box>
            <IconLegendTooltip />
          </Flex>
          <Flex direction="row" alignItems="center">
            <Switch
              size="sm"
              isChecked={isShowingFullSchema}
              onChange={() => setIsShowingFullSchema(!isShowingFullSchema)}
              colorScheme="purple"
              data-testid="full-schema-toggle"
            />
            <Text marginLeft={2} fontSize="xs" fontWeight="medium">
              Show full schema
            </Text>
          </Flex>
        </Flex>
      </TableActionBar>
      <FidesTableV2
        tableInstance={tableInstance}
        onRowClick={handleRowClicked}
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

export default DetectionResultTable;
