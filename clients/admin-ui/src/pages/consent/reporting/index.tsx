/* eslint-disable react/no-unstable-nested-components */
import { getCoreRowModel, useReactTable } from "@tanstack/react-table";
import dayjs, { Dayjs } from "dayjs";
import {
  AntButton as Button,
  AntDatePicker as DatePicker,
  AntDropdown as Dropdown,
  AntFlex as Flex,
  Box,
  Icons,
  Text,
} from "fidesui";
import React, { useMemo } from "react";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import {
  FidesTableV2,
  PAGE_SIZES,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { useGetAllHistoricalPrivacyPreferencesQuery } from "~/features/consent-reporting/consent-reporting.slice";
import useConsentReportingDownload from "~/features/consent-reporting/hooks/useConsentReportingDownload";
import useConsentReportingTableColumns from "~/features/consent-reporting/hooks/useConsentReportingTableColumns";
import { ConsentReportingSchema } from "~/types/api";

const ConsentReportingPage = () => {
  const pagination = useServerSidePagination();
  const today = useMemo(() => dayjs(), []);
  const [startDate, setStartDate] = React.useState<Dayjs | null>(null);
  const [endDate, setEndDate] = React.useState<Dayjs | null>(null);

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

  const columns = useConsentReportingTableColumns();
  const tableInstance = useReactTable<ConsentReportingSchema>({
    getCoreRowModel: getCoreRowModel(),
    data: privacyPreferences,
    columns,
    getRowId: (row) => `${row.id}`,
    manualPagination: true,
  });

  const { downloadReport, isDownloadingReport } = useConsentReportingDownload();
  const handleDownloadClicked = () => {
    const dateFormat = "YYYY-MM-DD";
    downloadReport({
      startDate: startDate?.format(dateFormat),
      endDate: endDate?.format(dateFormat),
    });
  };

  return (
    <Layout title="Consent reporting">
      <PageHeader heading="Consent reporting" />
      <Box data-testid="consent-reporting">
        <Text fontSize="sm" mb={6} width={{ base: "100%", lg: "50%" }}>
          Download a CSV containing a report of consent preferences made by
          users on your sites. Select a date range below and click
          &quot;Download report&quot;. Depending on the number of records in the
          date range you select, it may take several minutes to prepare the file
          after you click &quot;Download report&quot;.
        </Text>

        {isLoading ? (
          <Box p={2} borderWidth={1}>
            <TableSkeletonLoader rowHeight={26} numRows={10} />
          </Box>
        ) : (
          <>
            <TableActionBar>
              <DatePicker.RangePicker
                placeholder={["From", "To"]}
                maxDate={today}
                data-testid="input-date-range"
                onChange={(dates: [Dayjs | null, Dayjs | null] | null) => {
                  setStartDate(dates && dates[0]);
                  setEndDate(dates && dates[1]);
                }}
              />
              <Flex gap={12}>
                <Button
                  icon={<Icons.Download />}
                  data-testid="download-btn"
                  loading={isDownloadingReport}
                  onClick={handleDownloadClicked}
                />
                <Dropdown
                  menu={{
                    items: [
                      {
                        key: "1",
                        label: (
                          <span data-testid="consent-preference-lookup-button">
                            Consent preference lookup
                          </span>
                        ),
                      },
                    ],
                  }}
                  overlayStyle={{ width: "220px" }}
                  trigger={["click"]}
                >
                  <Button icon={<Icons.OverflowMenuVertical />} />
                </Dropdown>
              </Flex>
            </TableActionBar>
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
