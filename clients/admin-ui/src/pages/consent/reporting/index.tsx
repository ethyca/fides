/* eslint-disable react/no-unstable-nested-components */
import { getCoreRowModel, useReactTable } from "@tanstack/react-table";
import dayjs, { Dayjs } from "dayjs";
import {
  AntButton as Button,
  AntDateRangePicker as DateRangePicker,
  AntDropdown as Dropdown,
  AntEmpty as Empty,
  AntFlex as Flex,
  AntSelect as Select,
  Icons,
  useToast,
} from "fidesui";
import React, { useMemo, useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { usePagination } from "~/features/common/hooks/usePagination";
import PageHeader from "~/features/common/PageHeader";
import {
  FidesTableV2,
  TableActionBar,
  TableSkeletonLoader,
} from "~/features/common/table/v2";
import { successToastParams } from "~/features/common/toast";
import { useGetAllHistoricalPrivacyPreferencesQuery } from "~/features/consent-reporting/consent-reporting.slice";
import ConsentLookupModal from "~/features/consent-reporting/ConsentLookupModal";
import ConsentReportDownloadModal from "~/features/consent-reporting/ConsentReportDownloadModal";
import ConsentTcfDetailModal from "~/features/consent-reporting/ConsentTcfDetailModal";
import useConsentReportingTableColumns from "~/features/consent-reporting/hooks/useConsentReportingTableColumns";
import { ConsentReportingSchema } from "~/types/api";

const ConsentReportingPage = () => {
  // const pagination = useServerSidePagination();
  const today = useMemo(() => dayjs(), []);
  const [startDate, setStartDate] = useState<Dayjs | null>(null);
  const [endDate, setEndDate] = useState<Dayjs | null>(null);
  const [isConsentLookupModalOpen, setIsConsentLookupModalOpen] =
    useState(false);
  const [isDownloadReportModalOpen, setIsDownloadReportModalOpen] =
    useState(false);
  const [isConsentTcfDetailModalOpen, setIsConsentTcfDetailModalOpen] =
    useState(false);
  const [currentTcfPreferences, setCurrentTcfPreferences] = useState();

  const {
    pageIndex,
    pageSize,
    updatePageIndex,
    updatePageSize,
    nextPage,
    previousPage,
  } = usePagination();

  const toast = useToast();

  const { data, isLoading, isFetching, refetch } =
    useGetAllHistoricalPrivacyPreferencesQuery({
      page: pageIndex,
      size: pageSize,
      startDate,
      endDate,
      includeTotal: Boolean(startDate) && Boolean(endDate),
    });

  const { items: privacyPreferences } = useMemo(() => {
    const results = data || { items: [], total: 0, pages: 0 };
    return results;
  }, [data]);

  const onTcfDetailViewClick = (tcfPreferences: any) => {
    setIsConsentTcfDetailModalOpen(true);
    setCurrentTcfPreferences(tcfPreferences);
  };

  const columns = useConsentReportingTableColumns({ onTcfDetailViewClick });
  const tableInstance = useReactTable<ConsentReportingSchema>({
    getCoreRowModel: getCoreRowModel(),
    data: privacyPreferences,
    columns,
    getRowId: (row) => `${row.id}`,
    manualPagination: true,
  });

  const handleClickRefresh = async () => {
    updatePageIndex(1);
    await refetch();
    toast(
      successToastParams(
        "Consent report refreshed successfully.",
        "Report Refreshed",
      ),
    );
  };

  return (
    <FixedLayout title="Consent reporting">
      <PageHeader
        heading="Consent reporting"
        rightContent={
          <Button
            type="primary"
            onClick={handleClickRefresh}
            loading={isFetching}
          >
            Refresh
          </Button>
        }
      />
      <div data-testid="consent-reporting" className="overflow-auto">
        {isLoading ? (
          <div className="border p-2">
            <TableSkeletonLoader rowHeight={26} numRows={10} />
          </div>
        ) : (
          <>
            <TableActionBar>
              <DateRangePicker
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
                  aria-label="Download Consent Report"
                />
                <Dropdown
                  menu={{
                    items: [
                      {
                        key: "1",
                        label: (
                          <span data-testid="consent-preference-lookup-btn">
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
                  <Button
                    icon={<Icons.OverflowMenuVertical />}
                    data-testid="consent-reporting-dropdown-btn"
                  />
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
            <div
              style={{
                display: "flex",
                columnGap: "10px",
                alignItems: "center",
              }}
            >
              <Button onClick={previousPage} disabled={pageIndex === 1}>
                Previous
              </Button>
              <span>{pageIndex}</span>
              <Button
                onClick={nextPage}
                disabled={(data?.items?.length ?? 0) < pageSize}
              >
                Next
              </Button>
              <Select
                style={{ width: "auto" }}
                value={pageSize}
                onChange={updatePageSize}
                options={[
                  { label: 25, value: 25 },
                  { label: 50, value: 50 },
                  { label: 100, value: 100 },
                ]}
                // eslint-disable-next-line react/no-unstable-nested-components
                labelRender={() => {
                  return <span>{pageSize} / page</span>;
                }}
              />
            </div>
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
      <ConsentTcfDetailModal
        isOpen={isConsentTcfDetailModalOpen}
        onClose={() => {
          setIsConsentTcfDetailModalOpen(false);
          setCurrentTcfPreferences(undefined);
        }}
        tcfPreferences={currentTcfPreferences}
      />
    </FixedLayout>
  );
};

export default ConsentReportingPage;
