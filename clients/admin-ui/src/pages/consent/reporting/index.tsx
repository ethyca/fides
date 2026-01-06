import dayjs, { Dayjs } from "dayjs";
import {
  Button,
  DateRangePicker,
  Dropdown,
  Flex,
  Icons,
  Table,
  useChakraToast as useToast,
} from "fidesui";
import React, { useCallback, useMemo, useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { usePagination } from "~/features/common/hooks";
import PageHeader from "~/features/common/PageHeader";
import { InfinitePaginator } from "~/features/common/pagination/InfinitePaginator";
import { successToastParams } from "~/features/common/toast";
import { useGetAllHistoricalPrivacyPreferencesQuery } from "~/features/consent-reporting/consent-reporting.slice";
import ConsentLookupModal from "~/features/consent-reporting/ConsentLookupModal";
import ConsentReportDownloadModal from "~/features/consent-reporting/ConsentReportDownloadModal";
import ConsentTcfDetailModal from "~/features/consent-reporting/ConsentTcfDetailModal";
import useConsentReportingColumns from "~/features/consent-reporting/hooks/useConsentReportingTableColumns";

const ConsentReportingPage = () => {
  const pagination = usePagination();
  const { pageIndex, pageSize, updatePageIndex } = pagination;
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

  const toast = useToast();

  const { data, isLoading, isFetching, refetch } =
    useGetAllHistoricalPrivacyPreferencesQuery({
      page: pageIndex,
      size: pageSize,
      startDate,
      endDate,
      includeTotal: false,
    });

  const { items: privacyPreferences } = useMemo(() => {
    const results = data || { items: [], total: 0, pages: 0 };
    return results;
  }, [data]);

  const onTcfDetailViewClick = useCallback((tcfPreferences: any) => {
    setIsConsentTcfDetailModalOpen(true);
    setCurrentTcfPreferences(tcfPreferences);
  }, []);

  // Ant Design table columns
  const antColumns = useConsentReportingColumns({
    onTcfDetailViewClick,
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
      <Flex vertical gap="middle" data-testid="consent-reporting">
        <Flex justify="space-between">
          <DateRangePicker
            placeholder={["From", "To"]}
            maxDate={today}
            data-testid="input-date-range-ant"
            onChange={(dates: [Dayjs | null, Dayjs | null] | null) => {
              setStartDate(dates && dates[0]);
              setEndDate(dates && dates[1]);
            }}
          />
          <Flex gap={12}>
            <Button
              icon={<Icons.Download />}
              data-testid="download-btn-ant"
              onClick={() => setIsDownloadReportModalOpen(true)}
              aria-label="Download Consent Report"
            />
            <Dropdown
              menu={{
                items: [
                  {
                    key: "1",
                    label: (
                      <span data-testid="consent-preference-lookup-btn-ant">
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
                aria-label="Menu"
                icon={<Icons.OverflowMenuVertical />}
                data-testid="consent-reporting-dropdown-btn-ant"
              />
            </Dropdown>
          </Flex>
        </Flex>
        <Table
          columns={antColumns}
          dataSource={privacyPreferences}
          rowKey="id"
          loading={isLoading}
          pagination={false}
        />
        <InfinitePaginator
          disableNext={(data?.items?.length ?? 0) < pageSize}
          pagination={pagination}
        />
      </Flex>
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
