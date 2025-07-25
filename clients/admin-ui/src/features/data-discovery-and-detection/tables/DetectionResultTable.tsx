/* eslint-disable react/no-unstable-nested-components */

import {
  ColumnDef,
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { AntTabs as Tabs, Box, Flex, Text, VStack } from "fidesui";
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
import useDetectionResultFilterTabs, {
  DetectionResultFilterTabs,
} from "~/features/data-discovery-and-detection/hooks/useDetectionResultsFilterTabs";
import useDiscoveryRoutes from "~/features/data-discovery-and-detection/hooks/useDiscoveryRoutes";
import IconLegendTooltip from "~/features/data-discovery-and-detection/IndicatorLegend";
import { findResourceType } from "~/features/data-discovery-and-detection/utils/findResourceType";
import getResourceRowName from "~/features/data-discovery-and-detection/utils/getResourceRowName";
import isNestedField from "~/features/data-discovery-and-detection/utils/isNestedField";
import { StagedResource, StagedResourceTypeValue } from "~/types/api";

import { DebouncedSearchInput } from "../../common/DebouncedSearchInput";

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
  const [searchQuery, setSearchQuery] = useState("");

  const {
    filterTabs,
    activeTabKey,
    onTabChange,
    activeDiffFilters,
    activeChildDiffFilters,
    activeChangeTypeOverride,
  } = useDetectionResultFilterTabs();

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
    resetPageIndexToDefault,
  } = useServerSidePagination();

  useEffect(() => {
    resetPageIndexToDefault();
  }, [
    resourceUrn,
    searchQuery,
    resetPageIndexToDefault,
    activeDiffFilters,
    activeChildDiffFilters,
  ]);

  const {
    isFetching,
    isLoading,
    data: resources,
  } = useGetMonitorResultsQuery({
    staged_resource_urn: resourceUrn,
    page: pageIndex,
    size: pageSize,
    child_diff_status: activeChildDiffFilters,
    diff_status: activeDiffFilters,
    search: searchQuery,
  });

  const resourceType = findResourceType(resources?.items[0]);

  const { columns } = useDetectionResultColumns({
    resourceType,
    changeTypeOverride: activeChangeTypeOverride,
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
    () => columns,
    [columns],
  );

  const { navigateToDetectionResults } = useDiscoveryRoutes();

  const handleRowClicked = (row: StagedResource) =>
    navigateToDetectionResults({
      resourceUrn: row.urn,
      filterTab: activeTabKey,
    });

  const getRowIsClickable = (row: StagedResource) =>
    resourceType !== StagedResourceTypeValue.FIELD || isNestedField(row);

  const tableInstance = useReactTable<StagedResource>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    getRowId: getResourceRowName,
    columns: resourceColumns,
    manualPagination: true,
    data,
    columnResizeMode: "onChange",
  });

  if (isLoading) {
    return <TableSkeletonLoader rowHeight={36} numRows={36} />;
  }

  return (
    <>
      <Tabs
        items={filterTabs.map((tab) => ({
          key: tab.key,
          label: tab.label,
        }))}
        activeKey={activeTabKey}
        onChange={(tab) => onTabChange(tab as DetectionResultFilterTabs)}
      />
      <TableActionBar>
        <Flex
          direction="row"
          alignItems="center"
          justifyContent="space-between"
          width="full"
        >
          <Flex gap={6} align="center">
            <Box flexShrink={0}>
              <DebouncedSearchInput
                value={searchQuery}
                onChange={setSearchQuery}
              />
            </Box>
            <IconLegendTooltip />
          </Flex>
        </Flex>
      </TableActionBar>
      <FidesTableV2
        tableInstance={tableInstance}
        onRowClick={handleRowClicked}
        getRowIsClickable={getRowIsClickable}
        emptyTableNotice={<EmptyTableNotice />}
      />
      <PaginationBar
        totalRows={totalRows || 0}
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
