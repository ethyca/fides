import {
  AntButton as Button,
  AntDivider as Divider,
  AntFlex as Flex,
  AntList as List,
  AntMenu as Menu,
  useToast,
} from "fidesui";
import NextLink from "next/link";
import { useCallback, useEffect, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  PaginationBar,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { useGetConfigurationSettingsQuery } from "~/features/config-settings/config-settings.slice";
import { useGetAggregateMonitorResultsQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { InProgressMonitorTasksList } from "~/features/data-discovery-and-detection/action-center/components/InProgressMonitorTasksList";
import { DisabledMonitorsPage } from "~/features/data-discovery-and-detection/action-center/DisabledMonitorsPage";
import { EmptyMonitorsResult } from "~/features/data-discovery-and-detection/action-center/EmptyMonitorsResult";
import useTopLevelActionCenterTabs, {
  TopLevelActionCenterTabHash,
} from "~/features/data-discovery-and-detection/action-center/hooks/useTopLevelActionCenterTabs";
import { MonitorResult } from "~/features/data-discovery-and-detection/action-center/MonitorResult";
import { MONITOR_TYPES } from "~/features/data-discovery-and-detection/action-center/utils/getMonitorType";

const buildMonitorLink = (monitorType: MONITOR_TYPES, monitorKey: string) =>
  monitorType !== MONITOR_TYPES.WEBSITE
    ? `${ACTION_CENTER_ROUTE}/data-explorer/${monitorKey}`
    : `${ACTION_CENTER_ROUTE}/${monitorKey}`;

const ActionCenterPage = () => {
  const toast = useToast();
  const { tabs, activeTab, onTabChange } = useTopLevelActionCenterTabs();
  const { flags } = useFeatures();
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
      setTotalPages(data.total ?? 1);
    }
  }, [data, setTotalPages]);

  /*
   * Filtering paginated results can lead to odd behaviors
   * Either key should be constructed on the FE to display result, or BE should provide this functionality via the api
   */
  const results =
    data?.items
      ?.flatMap((monitor) =>
        !!monitor.key && typeof monitor.key !== "undefined" ? [monitor] : [],
      )
      .filter(
        (monitor) =>
          flags.alphaFullActionCenter ||
          monitor.monitorType === MONITOR_TYPES.WEBSITE,
      ) || [];
  const loadingResults = isFetching
    ? Array.from({ length: pageSize }, (_, index) => ({
        key: index.toString(),
        updates: [],
        last_monitored: null,
      }))
    : [];

  // TODO: [HJ-337] Add button functionality

  // const handleAdd = (monitorId: string) => {
  //   console.log("Add report", monitorId);
  // };

  const getWebsiteMonitorActions = useCallback(
    (monitorKey: string, link?: string) => [
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
      <NextLink key="review" href={link ?? ""} passHref legacyBehavior>
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

      <Menu
        aria-label="Action center tabs"
        mode="horizontal"
        items={tabs.map((tab) => ({
          key: tab.hash,
          label: tab.label,
        }))}
        selectedKeys={[activeTab]}
        onClick={async (menuInfo) => {
          const validKey = Object.values(TopLevelActionCenterTabHash).find(
            (value) => value === menuInfo.key,
          );
          if (validKey) {
            await onTabChange(validKey);
          }
        }}
        className="mb-4"
        data-testid="action-center-tabs"
      />

      {activeTab === TopLevelActionCenterTabHash.IN_PROGRESS ? (
        <InProgressMonitorTasksList />
      ) : (
        <>
          <Flex className="justify-between py-6">
            <DebouncedSearchInput
              value={searchQuery}
              onChange={setSearchQuery}
            />
          </Flex>

          <List
            loading={isLoading}
            dataSource={results || loadingResults}
            locale={{
              emptyText: <EmptyMonitorsResult />,
            }}
            renderItem={(summary) => {
              const link = summary.key
                ? buildMonitorLink(summary.monitorType, summary.key)
                : "";
              return (
                !!summary?.key && (
                  <MonitorResult
                    showSkeleton={isFetching}
                    key={summary.key}
                    monitorSummary={summary}
                    href={link}
                    actions={getWebsiteMonitorActions(summary.key, link)} // TODO: when monitor type becomes available, use it to determine actions. Defaulting to website monitor actions for now.
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
        </>
      )}
    </Layout>
  );
};

export default ActionCenterPage;
