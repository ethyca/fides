import {
  AntButton as Button,
  AntDivider as Divider,
  AntFlex as Flex,
  AntList as List,
  useToast,
} from "fidesui";
import NextLink from "next/link";
import { useCallback, useEffect, useState } from "react";

import Layout from "~/features/common/Layout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  PaginationBar,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { useGetConfigurationSettingsQuery } from "~/features/config-settings/config-settings.slice";
import { useGetAggregateMonitorResultsQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { DisabledMonitorsPage } from "~/features/data-discovery-and-detection/action-center/DisabledMonitorsPage";
import { EmptyMonitorsResult } from "~/features/data-discovery-and-detection/action-center/EmptyMonitorsResult";
import { MonitorResult } from "~/features/data-discovery-and-detection/action-center/MonitorResult";
import { MonitorAggregatedResults } from "~/features/data-discovery-and-detection/action-center/types";
import { SearchInput } from "~/features/data-discovery-and-detection/SearchInput";

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

  const { data, isError, isLoading, isFetching } =
    useGetAggregateMonitorResultsQuery(
      {
        page: pageIndex,
        size: pageSize,
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

  // TODO: [HJ-337] Add button functionality

  // const handleAdd = (monidorId: string) => {
  //   console.log("Add report", monidorId);
  // };

  const getWebsiteMonitorActions = useCallback(
    (monitorKey: string) => [
      // <Button
      //   key="add"
      //   type="link"
      //   className="p-0"
      //   onClick={() => {
      //     handleAdd(monitorKey);
      //   }}
      //   data-testid={`add-button-${monitorKey}`}
      // >
      //   Add
      // </Button>,
      <NextLink
        key="review"
        href={`${ACTION_CENTER_ROUTE}/${monitorKey}`}
        passHref
        legacyBehavior
      >
        <Button
          type="link"
          className="p-0"
          data-testid={`review-button-${monitorKey}`}
        >
          Review
        </Button>
      </NextLink>,
    ],
    [],
  );

  if (!webMonitorEnabled) {
    return <DisabledMonitorsPage isConfigLoading={isConfigLoading} />;
  }

  return (
    <Layout title="Action center">
      <PageHeader
        heading="Action center"
        breadcrumbItems={[{ title: "All activity" }]}
      />

      <Flex className="justify-between py-6">
        <SearchInput value={searchQuery} onChange={setSearchQuery} />
      </Flex>

      <List
        loading={isLoading}
        dataSource={results || loadingResults}
        locale={{
          emptyText: <EmptyMonitorsResult />,
        }}
        renderItem={(summary: MonitorAggregatedResults) => {
          return (
            !!summary && (
              <MonitorResult
                showSkeleton={isFetching}
                key={summary.key}
                monitorSummary={summary}
                actions={getWebsiteMonitorActions(summary.key)} // TODO: when monitor type becomes available, use it to determine actions. Defaulting to website monitor actions for now.
              />
            )
          );
        }}
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
