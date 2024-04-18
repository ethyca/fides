/* eslint-disable react/no-unstable-nested-components */

import { Text, VStack } from "@fidesui/react";
import {
  ColumnDef,
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useEffect, useMemo, useState } from "react";

import {
  FidesTableV2,
  PaginationBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { useGetMonitorResultsQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import DiscoveryMonitorTabFilter, {
  FirstLetterFilterValue,
} from "~/features/data-discovery-and-detection/DiscoveryMonitorTabFilter";
import useStagedResourceColumns, {
  findResourceType,
  MonitorResultsItem,
  StagedResourceType,
} from "~/features/data-discovery-and-detection/hooks/useStagedResourceColumns";
import { StagedResource } from "~/types/api";

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
        No results found.
      </Text>
      <Text fontSize="sm">
        [insert some copy about how to find results here]
      </Text>
    </VStack>
  </VStack>
);

interface MonitorResultTableProps {
  monitorId: string;
  resourceUrn?: string;
  onSelectResource: ({
    monitorId,
    resourceUrn,
  }: {
    monitorId: string;
    resourceUrn: string;
  }) => void;
}

const DiscoveryMonitorResultTable = ({
  monitorId,
  resourceUrn,
  onSelectResource,
}: MonitorResultTableProps) => {
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
    monitor_config_id: monitorId,
    staged_resource_urn: resourceUrn,
    page: pageIndex,
    size: pageSize,
  });

  const [filterValue, setFilterValue] = useState<FirstLetterFilterValue>(
    FirstLetterFilterValue.ALL
  );

  const filterByFirstLetter = (
    item: MonitorResultsItem,
    filter: FirstLetterFilterValue
  ) => {
    if (filter === FirstLetterFilterValue.NONE) {
      return false;
    }
    if (filter === FirstLetterFilterValue.ALL) {
      return true;
    }
    const startsWithVowel = ["a", "e", "i", "o", "u"].some((vowel) =>
      item.name.toLocaleLowerCase().startsWith(vowel)
    );
    if (startsWithVowel) {
      return filter === FirstLetterFilterValue.VOWEL;
    }
    return filter === FirstLetterFilterValue.CONSONANT;
  };

  const resourceType = findResourceType(
    resources?.items[0] as MonitorResultsItem
  );

  const { columns } = useStagedResourceColumns(resourceType);

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
    [columns]
  );

  const filteredData = useMemo(
    () => data.filter((item) => filterByFirstLetter(item, filterValue)),
    [data, filterValue]
  );

  const handleRowClick =
    resourceType !== StagedResourceType.FIELD
      ? (resource: StagedResource) =>
          onSelectResource({ monitorId, resourceUrn: resource.urn })
      : undefined;

  const tableInstance = useReactTable<StagedResource>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    columns: resourceColumns,
    manualPagination: true,
    data: filteredData,
  });

  if (isLoading) {
    return <TableSkeletonLoader rowHeight={36} numRows={36} />;
  }

  return (
    <>
      <DiscoveryMonitorTabFilter onFilterChange={setFilterValue} />
      <FidesTableV2
        tableInstance={tableInstance}
        onRowClick={handleRowClick}
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

export default DiscoveryMonitorResultTable;
