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
import { useSearchParams } from "next/navigation";
import { useRouter } from "next/router";
import React, { useContext, useEffect, useMemo, useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
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

type QueryParam = ReturnType<InstanceType<typeof URLSearchParams>["get"]>;
function useStatefulQueryParam<
  InitialValue = QueryParam,
  TransformedValue = QueryParam,
>(
  key: string,
  fromQueryParam: (value: QueryParam) => TransformedValue,
  initialValue: InitialValue,
) {
  const searchParams = useSearchParams();
  const paramValue = searchParams?.get(key) ?? null;
  const [value, setValue] = useState(
    fromQueryParam(paramValue) ?? initialValue,
  );
  const router = useRouter();

  useEffect(() => {
    const nextQueryParams = new URLSearchParams(window.location.search);
    if (value === initialValue || value === undefined || value === null) {
      nextQueryParams.delete(key);
    } else {
      nextQueryParams.set(key, value.toString());
    }
    router.push({
      query: nextQueryParams.toString(),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, paramValue, value]);

  return [value, setValue] as const;
}

const safeParseInt = (
  v: string | null | undefined,
): number | null | undefined => (typeof v === "string" ? parseInt(v, 10) : v);

const DEFAULT_PAGE = 1;
const DEFAULT_SIZE = 25;

const usePaginatorState = () => {
  const [page, setPage] = useStatefulQueryParam(
    "page",
    safeParseInt,
    DEFAULT_PAGE,
  );
  const [size, internalSetSize] = useStatefulQueryParam(
    "size",
    safeParseInt,
    DEFAULT_SIZE,
  );

  const setSize = (nextSize: number) => {
    internalSetSize(nextSize);
    setPage(1);
  };

  const previous = () =>
    setPage((previousPage) => {
      const nextPage = previousPage - 1;
      if (nextPage < DEFAULT_PAGE) {
        return DEFAULT_PAGE;
      }
      return nextPage;
    });
  const next = () => setPage((previousPage) => previousPage + 1);

  return {
    previous,
    next,
    setSize,
    page,
    size,
  };
};

const PageContext = React.createContext<
  ReturnType<typeof usePaginatorState> | undefined
>(undefined);

const PaginationContext = ({ children }: { children: React.ReactNode }) => {
  const paginationState = usePaginatorState();

  return (
    <PageContext.Provider value={paginationState}>
      {children}
    </PageContext.Provider>
  );
};

const usePagination = () => {
  const paginationContext = useContext(PageContext);
  if (paginationContext) {
    return paginationContext;
  }

  throw new Error("Pagination Context Provider not found.");
};

const Paginator = () => {
  const { next, page, size, previous, setSize } = usePagination();

  return (
    <div style={{ display: "flex", columnGap: "10px", alignItems: "center" }}>
      <Button onClick={previous} disabled={page === 1}>
        Previous
      </Button>
      <span>{page}</span>
      <Button onClick={next}>Next</Button>
      <Select
        style={{ width: "auto" }}
        value={size}
        onChange={setSize}
        options={[
          { label: 25, value: 25 },
          { label: 50, value: 50 },
          { label: 100, value: 100 },
        ]}
        labelRender={() => {
          return <span>{size} / page</span>;
        }}
      />
    </div>
  );
};

const ConsentReporting = () => {
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
  const { page, size } = usePagination();

  const toast = useToast();

  const { data, isLoading, isFetching, refetch } =
    useGetAllHistoricalPrivacyPreferencesQuery({
      page,
      size,
      startDate,
      endDate,
      include_total: false,
    });

  const { items: privacyPreferences } = useMemo(() => {
    const results = data ?? { items: [] };

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
          </>
        )}
      </div>
      <Paginator />
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

const ConsentReportingPage = () => {
  return (
    <PaginationContext>
      <ConsentReporting />
    </PaginationContext>
  );
};

export default ConsentReportingPage;
