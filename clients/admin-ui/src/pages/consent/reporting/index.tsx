/* eslint-disable react/no-unstable-nested-components */
import { getCoreRowModel, useReactTable } from "@tanstack/react-table";
import dayjs, { Dayjs } from "dayjs";
import {
  AntButton as Button,
  AntDatePicker as DatePicker,
  AntDropdown as Dropdown,
  AntEmpty as Empty,
  AntFlex as Flex,
  Icons,
} from "fidesui";
import React, { useMemo, useState } from "react";

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
import ConsentLookupModal from "~/features/consent-reporting/ConsentLookupModal";
import ConsentReportDownloadModal from "~/features/consent-reporting/ConsentReportDownloadModal";
import useConsentReportingTableColumns from "~/features/consent-reporting/hooks/useConsentReportingTableColumns";
import { ConsentReportingSchema } from "~/types/api";

const ConsentReportingPage = () => {
  const pagination = useServerSidePagination();
  const today = useMemo(() => dayjs(), []);
  const [startDate, setStartDate] = useState<Dayjs | null>(null);
  const [endDate, setEndDate] = useState<Dayjs | null>(null);
  const [isConsentLookupModalOpen, setIsConsentLookupModalOpen] =
    useState(false);
  const [isDownloadReportModalOpen, setIsDownloadReportModalOpen] =
    useState(false);

  const dateFormat = "YYYY-MM-DD";
  const { data, isLoading, isFetching, refetch } =
    useGetAllHistoricalPrivacyPreferencesQuery({
      page: pagination.pageIndex,
      size: pagination.pageSize,
      startDate: startDate?.format(dateFormat),
      endDate: endDate?.format(dateFormat),
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

  return (
    <Layout title="Consent reporting">
      <PageHeader
        heading="Consent reporting"
        rightContent={
          <Button type="primary" onClick={refetch} loading={isFetching}>
            Refresh
          </Button>
        }
      />
      <div data-testid="consent-reporting">
        {isLoading ? (
          <div className="border p-2">
            <TableSkeletonLoader rowHeight={26} numRows={10} />
          </div>
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
                  onClick={() => setIsDownloadReportModalOpen(true)}
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
                        onClick: () => setIsConsentLookupModalOpen(true),
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
              emptyTableNotice={
                <Empty
                  description="No results."
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  imageStyle={{ marginBottom: 15 }}
                />
              }
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
      </div>
      <ConsentLookupModal
        isOpen={isConsentLookupModalOpen}
        onClose={() => setIsConsentLookupModalOpen(false)}
      />
      <ConsentReportDownloadModal
        isOpen={isDownloadReportModalOpen}
        onClose={() => setIsDownloadReportModalOpen(false)}
        startDate={startDate}
        endDate={endDate}
      />
    </Layout>
  );
};

export default ConsentReportingPage;
