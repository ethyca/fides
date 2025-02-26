import { getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { AntEmpty as Empty } from "fidesui";
import { useEffect, useState } from "react";

import {
  FidesTableV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { SearchInput } from "~/features/data-discovery-and-detection/SearchInput";
import { useGetSystemAssetsQuery } from "~/features/system/system.slice";
import useSystemAssetColumns from "~/features/system/tabs/system-assets/useSystemAssetColumns";
import { SystemResponse } from "~/types/api";

const SystemAssetsTable = ({ system }: { system: SystemResponse }) => {
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

  const { data, isLoading, isFetching } = useGetSystemAssetsQuery({
    fides_key: system.fides_key,
    search: searchQuery,
    page: pageIndex,
    size: pageSize,
  });

  useEffect(() => {
    resetPageIndexToDefault();
  }, [searchQuery, resetPageIndexToDefault]);

  useEffect(() => {
    setTotalPages(data?.pages);
  }, [data, setTotalPages]);

  const columns = useSystemAssetColumns();

  const tableInstance = useReactTable({
    getCoreRowModel: getCoreRowModel(),
    columns,
    manualPagination: true,
    data: data?.items || [],
    columnResizeMode: "onChange",
  });

  if (!system) {
    return null;
  }

  if (isLoading) {
    return <TableSkeletonLoader rowHeight={36} numRows={36} />;
  }

  return (
    <>
      <TableActionBar>
        <SearchInput value={searchQuery} onChange={setSearchQuery} />
      </TableActionBar>
      <FidesTableV2
        tableInstance={tableInstance}
        emptyTableNotice={
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="No assets found"
            data-testid="empty-state"
          />
        }
      />
      <PaginationBar
        totalRows={data?.items?.length || 0}
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

export default SystemAssetsTable;
