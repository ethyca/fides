import {
  AntButton as Button,
  AntDivider as Divider,
  AntFlex as Flex,
  AntList as List,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  useToast,
} from "fidesui";
import NextLink from "next/link";
import { useEffect, useState } from "react";

import Layout from "~/features/common/Layout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  PaginationBar,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { useGetMonitorSummaryQuery } from "~/features/data-discovery-and-detection/action-center/actionCenter.slice";
import { DisabledMonitorPage } from "~/features/data-discovery-and-detection/action-center/DisabledMonitorPage";
import { EmptyMonitorResult } from "~/features/data-discovery-and-detection/action-center/EmptyMonitorResult";
import { MonitorResult } from "~/features/data-discovery-and-detection/action-center/MonitorResult";
import { MonitorSummary } from "~/features/data-discovery-and-detection/action-center/types";
import { SearchInput } from "~/features/data-discovery-and-detection/SearchInput";
import { useGetConfigurationSettingsQuery } from "~/features/privacy-requests";

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
  const { data: appConfig, isLoading: isConfigLoading } =
    useGetConfigurationSettingsQuery({
      api_set: false,
    });
  const webMonitorEnabled =
    !!appConfig?.detection_discovery?.website_monitor_enabled;

  useEffect(() => {
    resetPageIndexToDefault();
  }, [searchQuery, resetPageIndexToDefault]);

  const { data, isError, isLoading, isFetching } = useGetMonitorSummaryQuery(
    {
      pageIndex,
      pageSize,
      search: searchQuery,
    },
    { skip: isConfigLoading || !webMonitorEnabled },
  );

  useEffect(() => {
    if (isError && !!toast && webMonitorEnabled) {
      toast({
        title: "Error fetching data",
        description: "Please try again later",
        status: "error",
      });
    }
  }, [isError, toast, webMonitorEnabled]);

  useEffect(() => {
    if (data) {
      setTotalPages(data.total || 1);
    }
  }, [data, setTotalPages]);

  const results = data?.items || [];
  const loadingResults = isFetching
    ? (Array.from({ length: pageSize }, (_, index) => ({
        key: index.toString(),
        updates: [],
        last_monitored: null,
      })) as any[])
    : [];

  const handleIgnore = (monidorId: string) => {
    // TASK: hook up ignore action to API
    console.log("Ignoring report", monidorId);
  };

  if (!webMonitorEnabled) {
    return <DisabledMonitorPage isConfigLoading={isConfigLoading} />;
  }

  console.log("==>", pageSize, data?.total);

  return (
    <Layout title="Action center">
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
      </Flex>

      <List
        loading={isLoading}
        dataSource={results || loadingResults}
        locale={{
          emptyText: <EmptyMonitorResult />,
        }}
        renderItem={(summary: MonitorSummary) => (
          <MonitorResult
            showSkeleton={isFetching}
            key={summary.key}
            monitorSummary={summary}
            actions={[
              <NextLink
                key="review"
                href={`${ACTION_CENTER_ROUTE}/${summary.key}`}
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
                  handleIgnore(summary.key);
                }}
                data-testid={`ignore-button-${summary.key}`}
              >
                Ignore
              </Button>,
            ]}
          />
        )}
      />

      {!!results && !!data?.total && data.total > pageSize && (
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
    </Layout>
  );
};

export default ActionCenterPage;
