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
import EmptyCatalogTableNotice from "~/features/data-catalog/datasets/EmptyCatalogTableNotice";
import useCatalogDatasetColumns from "~/features/data-catalog/datasets/useCatalogDatasetColumns";
import { useGetMonitorResultsQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { useGetSystemByFidesKeyQuery } from "~/features/system";
import { StagedResourceAPIResponse } from "~/types/api";

const EMPTY_RESPONSE = {
  items: [],
  total: 0,
  page: 1,
  size: 50,
  pages: 1,
};

// dataset view when projects are present

const CatalogDatasetView = () => {
  const { query, push } = useRouter();
  const systemKey = query.systemId as string;
  const projectId = query.projectId as string;

  const { data: system, isLoading: systemIsLoading } =
    useGetSystemByFidesKeyQuery(systemKey);

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
    staged_resource_urn: projectId,
    page: pageIndex,
    size: pageSize,
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
  const showContent = !isLoading && !systemIsLoading && !isFetching;

  if (isLoading || isFetching || systemIsLoading) {
    return <TableSkeletonLoader rowHeight={36} numRows={36} />;
  }

  return (
    <Layout title="Data catalog">
      <PageHeader
        heading="Data catalog"
        breadcrumbItems={[
          { title: "All systems", href: DATA_CATALOG_ROUTE },
          {
            title: system?.name || systemKey,
            href: `${DATA_CATALOG_ROUTE}/${systemKey}/projects`,
          },
          { title: projectId },
        ]}
      />
      {!showContent && <TableSkeletonLoader rowHeight={36} numRows={36} />}
      {showContent && (
        <>
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
        </>
      )}
    </Layout>
  );
};

export default CatalogDatasetView;
