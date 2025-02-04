/* eslint-disable react/no-unstable-nested-components */
import {
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Box, Flex } from "fidesui";
import { useEffect, useMemo, useState } from "react";

import {
  FidesTableV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import EmptyCatalogTableNotice from "~/features/data-catalog/datasets/EmptyCatalogTableNotice";
import useCatalogResourceColumns from "~/features/data-catalog/useCatalogResourceColumns";
import { useGetMonitorResultsQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { SearchInput } from "~/features/data-discovery-and-detection/SearchInput";
import { StagedResourceType } from "~/features/data-discovery-and-detection/types/StagedResourceType";
import { findResourceType } from "~/features/data-discovery-and-detection/utils/findResourceType";
import resourceHasChildren from "~/features/data-discovery-and-detection/utils/resourceHasChildren";
import { DiffStatus, StagedResourceAPIResponse } from "~/types/api";

// everything except muted
const DIFF_STATUS_FILTERS = [
  DiffStatus.ADDITION,
  DiffStatus.CLASSIFYING,
  DiffStatus.CLASSIFICATION_ADDITION,
  DiffStatus.CLASSIFICATION_QUEUED,
  DiffStatus.CLASSIFICATION_UPDATE,
  DiffStatus.MONITORED,
  DiffStatus.PROMOTING,
  DiffStatus.REMOVAL,
  DiffStatus.REMOVING,
];

const EMPTY_RESPONSE = {
  items: [],
  total: 0,
  page: 1,
  size: 50,
  pages: 1,
};

const CatalogResourcesTable = ({
  resourceUrn,
  onRowClick,
}: {
  resourceUrn: string;
  onRowClick: (row: StagedResourceAPIResponse) => void;
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
    resetPageIndexToDefault,
  } = useServerSidePagination();

  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    resetPageIndexToDefault();
  }, [resourceUrn, resetPageIndexToDefault]);

  const {
    isFetching,
    isLoading,
    data: resources,
  } = useGetMonitorResultsQuery({
    staged_resource_urn: resourceUrn,
    page: pageIndex,
    size: pageSize,
    diff_status: DIFF_STATUS_FILTERS,
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

  const type = findResourceType(data[0] ?? StagedResourceType.NONE);

  const columns = useCatalogResourceColumns(type);

  const tableInstance = useReactTable<StagedResourceAPIResponse>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    columns,
    manualPagination: true,
    data,
    columnResizeMode: "onChange",
    getRowId: (row) => row.urn,
  });

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
        </Flex>
      </TableActionBar>
      <FidesTableV2
        tableInstance={tableInstance}
        emptyTableNotice={<EmptyCatalogTableNotice />}
        getRowIsClickable={(row) => resourceHasChildren(row)}
        onRowClick={onRowClick}
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

export default CatalogResourcesTable;
