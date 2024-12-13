import {
  AntButton as Button,
  AntDivider as Divider,
  AntEmpty as Empty,
  AntFlex as Flex,
  AntList as List,
  AntTypography as Typography,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  useToast,
} from "fidesui";
import NextLink from "next/link";
import { useEffect, useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import {
  ACTION_CENTER_ROUTE,
  INTEGRATION_MANAGEMENT_ROUTE,
} from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  PaginationBar,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { useGetMonitorSummaryQuery } from "~/features/data-discovery-and-detection/action-center/actionCenter.slice";
import { MonitorResult } from "~/features/data-discovery-and-detection/action-center/MonitorResult";
import { MonitorSummary } from "~/features/data-discovery-and-detection/action-center/types";
import { SearchInput } from "~/features/data-discovery-and-detection/SearchInput";

const { Text } = Typography;

const ActionCenterPage = () => {
  const toast = useToast();
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

  useEffect(() => {
    resetPageIndexToDefault();
  }, [searchQuery, resetPageIndexToDefault]);

  const { data, isError, isLoading, isFetching } = useGetMonitorSummaryQuery({
    pageIndex,
    pageSize,
    search: searchQuery,
  });

  useEffect(() => {
    if (isError && !!toast) {
      toast({
        title: "Error fetching data",
        description: "Please try again later",
        status: "error",
      });
    }
  }, [isError, toast]);

  useEffect(() => {
    if (data) {
      setTotalPages(data.total || 1);
    }
  }, [data, setTotalPages]);

  let results = data?.items || [];
  const loadingResults = isFetching
    ? (Array.from({ length: pageSize }, (_, index) => ({
        monitor_config_id: index.toString(),
        asset_counts: [],
        last_monitored: null,
      })) as any[])
    : [];

  // TASK: Remove this block
  if (!isLoading && !isFetching && !data) {
    results = [
      {
        monitor_config_id: "1",
        name: "Ethyca's Website Monitor",
        hostname: "ethyca.com",
        total_assets: 140,
        asset_counts: [
          { type: "cookies", count: 100 },
          { type: "pixels", count: 40 },
          { type: "tags", count: 3 },
        ],
        last_monitored: "2024-12-12T00:00:00Z",
        warning: "One or more sytems were found without consent",
      },
    ];
  }

  const handleIgnore = (reportId: string) => {
    // TASK: hook up ignore action to API
    console.log("Ignoring report", reportId);
  };

  return (
    <FixedLayout
      title="Action center"
      mainProps={{
        padding: "0 40px 48px",
      }}
    >
      {/* TASK: migrate to ANT */}
      <PageHeader breadcrumbs={[{ title: "Action center" }]}>
        <Breadcrumb
          separator="/"
          data-testid="results-breadcrumb"
          fontSize="sm"
          fontWeight="semibold"
          mt={-1}
          mb={0}
        >
          <BreadcrumbItem isCurrentPage>
            <BreadcrumbLink ml={1}>All activity</BreadcrumbLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </PageHeader>

      <Flex className="justify-between py-6">
        <SearchInput value={searchQuery} onChange={setSearchQuery} />

        {/* TASK: filter */}
        <Button data-testid="monitors-filter" size="small">
          Filter
        </Button>
      </Flex>

      <List
        loading={isLoading}
        dataSource={results || loadingResults}
        locale={{
          emptyText: (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="All caught up! Set up an integration monitor to track your infrastructure in greater detail."
            >
              <NextLink
                href={INTEGRATION_MANAGEMENT_ROUTE}
                passHref
                legacyBehavior
              >
                <Button type="primary">Visit integrations</Button>
              </NextLink>
            </Empty>
          ),
        }}
        renderItem={(summary: MonitorSummary) => (
          <MonitorResult
            showSkeleton={isFetching}
            key={summary.monitor_config_id}
            monitorSummary={summary}
            actions={[
              <NextLink
                key="review"
                href={`${ACTION_CENTER_ROUTE}/${summary.monitor_config_id}`}
                passHref
                legacyBehavior
              >
                <Button type="link" className="p-0">
                  Review
                </Button>
              </NextLink>,
              <Button
                key="ignore"
                type="link"
                className="p-0"
                onClick={() => {
                  handleIgnore(summary.monitor_config_id);
                }}
              >
                Ignore
              </Button>,
            ]}
          />
        )}
      />

      {!!results && !!data?.total && pageSize > data.total && (
        <>
          <Divider className="mb-6 mt-0" />
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
        </>
      )}
    </FixedLayout>
  );
};

export default ActionCenterPage;
