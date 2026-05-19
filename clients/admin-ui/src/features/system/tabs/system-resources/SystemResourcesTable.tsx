import { getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { ChakraText as Text, Empty, Select } from "fidesui";
import { useEffect, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import {
  FidesTableV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { SystemResponse } from "~/types/api";
import { CloudInfraStagedResource } from "~/types/api/models/CloudInfraStagedResource";

import { REGION_FILTER_OPTIONS, SERVICE_FILTER_OPTIONS } from "./constants";
import SystemResourceDetailDrawer from "./SystemResourceDetailDrawer";
import { useMockSystemResources } from "./useMockSystemResources";
import useSystemResourceColumns from "./useSystemResourceColumns";

const COPY = `This page displays cloud infrastructure resources associated with this system, detected by the AWS infrastructure monitor.`;

const SystemResourcesTable = ({ system }: { system: SystemResponse }) => {
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
  const [serviceFilter, setServiceFilter] = useState<string>("all");
  const [regionFilter, setRegionFilter] = useState<string>("all");
  const [detailResource, setDetailResource] =
    useState<CloudInfraStagedResource | null>(null);

  const { data, isLoading, isFetching } = useMockSystemResources({
    search: searchQuery,
    service: serviceFilter,
    region: regionFilter,
    page: pageIndex,
    size: pageSize,
  });

  useEffect(() => {
    resetPageIndexToDefault();
  }, [searchQuery, serviceFilter, regionFilter, resetPageIndexToDefault]);

  useEffect(() => {
    setTotalPages(data?.pages);
  }, [data, setTotalPages]);

  const columns = useSystemResourceColumns({
    onResourceClick: setDetailResource,
  });

  const tableInstance = useReactTable({
    getCoreRowModel: getCoreRowModel(),
    columns,
    manualPagination: true,
    data: data?.items || [],
    columnResizeMode: "onChange",
    getRowId: (row) => row.urn,
  });

  if (!system) {
    return null;
  }

  if (isLoading) {
    return <TableSkeletonLoader rowHeight={36} numRows={12} />;
  }

  return (
    <>
      <Text fontSize="sm" mb={4}>
        {COPY}
      </Text>
      <TableActionBar>
        <DebouncedSearchInput value={searchQuery} onChange={setSearchQuery} />
        <Select
          aria-label="Filter by service"
          data-testid="service-filter"
          value={serviceFilter}
          onChange={setServiceFilter}
          options={SERVICE_FILTER_OPTIONS}
          style={{ width: 180 }}
        />
        <Select
          aria-label="Filter by region"
          data-testid="region-filter"
          value={regionFilter}
          onChange={setRegionFilter}
          options={REGION_FILTER_OPTIONS}
          style={{ width: 180 }}
        />
      </TableActionBar>
      <FidesTableV2
        tableInstance={tableInstance}
        emptyTableNotice={
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="No resources found"
            data-testid="empty-state"
          />
        }
      />
      <PaginationBar
        totalRows={data?.total || 0}
        pageSizes={PAGE_SIZES}
        setPageSize={setPageSize}
        onPreviousPageClick={onPreviousPageClick}
        isPreviousPageDisabled={isPreviousPageDisabled || isFetching}
        onNextPageClick={onNextPageClick}
        isNextPageDisabled={isNextPageDisabled || isFetching}
        startRange={startRange}
        endRange={endRange}
      />
      <SystemResourceDetailDrawer
        resource={detailResource}
        isOpen={!!detailResource}
        onClose={() => setDetailResource(null)}
      />
    </>
  );
};

export default SystemResourcesTable;
