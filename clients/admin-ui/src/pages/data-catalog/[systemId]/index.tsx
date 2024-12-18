import {
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { AntButton, Flex } from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useMemo } from "react";

import Layout from "~/features/common/Layout";
import { DATA_CATALOG_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  FidesTableV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { useGetCatalogDatasetsQuery } from "~/features/data-catalog/data-catalog.slice";
import EmptyCatalogTableNotice from "~/features/data-catalog/datasets/EmptyCatalogTableNotice";
import useCatalogDatasetColumns from "~/features/data-catalog/datasets/useCatalogDatasetColumns";
import { StagedResourceAPIResponse } from "~/types/api";

// REPLACE: dataset view, system has no projects

const EMPTY_RESPONSE = {
  items: [],
  total: 0,
  page: 1,
  size: 50,
  pages: 1,
};

const CatalogDatasetViewNoProjects = () => {
  const { query, push } = useRouter();
  const systemKey = query["system-id"] as string;

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
  } = useGetCatalogDatasetsQuery({
    page: pageIndex,
    size: pageSize,
    monitor_config_ids: ["dynamo-monitor"],
  });

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => resources ?? EMPTY_RESPONSE, [resources]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const columns = useCatalogDatasetColumns();

  const tableInstance = useReactTable<StagedResourceAPIResponse>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    columns,
    manualPagination: true,
    data,
    columnResizeMode: "onChange",
  });

  if (isLoading || isFetching) {
    return <TableSkeletonLoader rowHeight={36} numRows={36} />;
  }

  return (
    <Layout title="Data catalog">
      <PageHeader breadcrumbs={[{ title: "Data catalog" }]} />
      <TableActionBar>
        <Flex gap={6} align="center">
          {/* <Box flexShrink={0}>
            <SearchInput value={searchQuery} onChange={setSearchQuery} />
          </Box> */}
        </Flex>
        <AntButton disabled>Actions</AntButton>
      </TableActionBar>
      <FidesTableV2
        tableInstance={tableInstance}
        emptyTableNotice={<EmptyCatalogTableNotice />}
        onRowClick={(row) =>
          push(`${DATA_CATALOG_ROUTE}/${systemKey}/${row.urn}`)
        }
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
    </Layout>
  );
};

export default CatalogDatasetViewNoProjects;
