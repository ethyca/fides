/* eslint-disable react/no-unstable-nested-components */
import {
  createColumnHelper,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Box, Text } from "fidesui";
import React, { useMemo } from "react";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  PAGE_SIZES,
  PaginationBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { formatDate } from "~/features/common/utils";
import { useGetAllHistoricalPrivacyPreferencesQuery } from "~/features/consent-reporting/consent-reporting.slice";
import ConsentReporting from "~/features/consent-reporting/ConsentReporting";
import { ConsentReportingSchema } from "~/types/api";

const columnHelper = createColumnHelper<ConsentReportingSchema>();

const ConsentReportingPage = () => {
  const pagination = useServerSidePagination();

  const { data, isLoading, isFetching } =
    useGetAllHistoricalPrivacyPreferencesQuery({
      page: pagination.pageIndex,
      size: pagination.pageSize,
    });

  const { setTotalPages } = pagination;
  const { items: privacyPreferences, total: totalRows } = useMemo(() => {
    const results = data || { items: [], total: 0, pages: 0 };
    setTotalPages(results.pages);
    return results;
  }, [data, setTotalPages]);

  const columns = useMemo(
    () => [
      columnHelper.accessor((row) => row.id, {
        id: "id",
        cell: ({ getValue }) => <DefaultCell value={getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Preference ID" {...props} />
        ),
        enableSorting: false,
      }),
      columnHelper.accessor((row) => row.request_timestamp, {
        id: "request_timestamp",
        cell: ({ getValue }) => <DefaultCell value={formatDate(getValue())} />,
        header: (props) => (
          <DefaultHeaderCell value="Time received" {...props} />
        ),
      }),
    ],
    [],
  );

  const tableInstance = useReactTable<ConsentReportingSchema>({
    getCoreRowModel: getCoreRowModel(),
    data: privacyPreferences,
    columns,
    getRowId: (row) => `${row.id}`,
    manualPagination: true,
  });

  return (
    <Layout title="Consent reporting">
      <PageHeader heading="Consent reporting" />
      <Box data-testid="consent">
        <Text fontSize="sm" mb={6} width={{ base: "100%", lg: "50%" }}>
          Download a CSV containing a report of consent preferences made by
          users on your sites. Select a date range below and click
          &quot;Download report&quot;. Depending on the number of records in the
          date range you select, it may take several minutes to prepare the file
          after you click &quot;Download report&quot;.
        </Text>
        <ConsentReporting />

        {isLoading ? (
          <Box p={2} borderWidth={1}>
            <TableSkeletonLoader rowHeight={26} numRows={10} />
          </Box>
        ) : (
          <>
            <FidesTableV2<ConsentReportingSchema>
              tableInstance={tableInstance}
            />
            <PaginationBar
              totalRows={totalRows || 0}
              pageSizes={PAGE_SIZES}
              setPageSize={pagination.setPageSize}
              onPreviousPageClick={pagination.onPreviousPageClick}
              isPreviousPageDisabled={
                pagination.isPreviousPageDisabled || isFetching
              }
              onNextPageClick={pagination.onNextPageClick}
              isNextPageDisabled={pagination.isNextPageDisabled || isFetching}
              startRange={pagination.startRange}
              endRange={pagination.endRange}
            />
          </>
        )}
      </Box>
    </Layout>
  );
};

export default ConsentReportingPage;
