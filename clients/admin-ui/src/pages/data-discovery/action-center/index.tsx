import {
  AntButton as Button,
  AntFlex as Flex,
  AntList as List,
  AntMenu as Menu,
  AntPagination as Pagination,
  Icons,
  useToast,
} from "fidesui";
import NextLink from "next/link";
import { useCallback, useEffect, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { useFeatures } from "~/features/common/features";
import FixedLayout from "~/features/common/FixedLayout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { useGetAggregateMonitorResultsQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { InProgressMonitorTasksList } from "~/features/data-discovery-and-detection/action-center/components/InProgressMonitorTasksList";
import { DisabledMonitorsPage } from "~/features/data-discovery-and-detection/action-center/DisabledMonitorsPage";
import { EmptyMonitorsResult } from "~/features/data-discovery-and-detection/action-center/EmptyMonitorsResult";
import useTopLevelActionCenterTabs, {
  TopLevelActionCenterTabHash,
} from "~/features/data-discovery-and-detection/action-center/hooks/useTopLevelActionCenterTabs";
import { MonitorResult } from "~/features/data-discovery-and-detection/action-center/MonitorResult";
import { MONITOR_TYPES } from "~/features/data-discovery-and-detection/action-center/utils/getMonitorType";

const ActionCenterPage = () => {
  const toast = useToast();
  const { tabs, activeTab, onTabChange } = useTopLevelActionCenterTabs();
  const { flags } = useFeatures();
  const { paginationProps, pageIndex, pageSize, resetPagination } =
    useAntPagination();
  const [searchQuery, setSearchQuery] = useState("");
  const { webMonitor: webMonitorEnabled, heliosV2: llmClassifierEnabled } =
    flags;

  // Build monitor_type filter based on enabled feature flags
  const monitorTypes: MONITOR_TYPES[] = [
    ...(webMonitorEnabled ? [MONITOR_TYPES.WEBSITE] : []),
    ...(llmClassifierEnabled ? [MONITOR_TYPES.DATASTORE] : []),
  ];

  const { data, isError, isLoading, isFetching } =
    useGetAggregateMonitorResultsQuery({
      page: pageIndex,
      size: pageSize,
      search: searchQuery,
      monitor_type: monitorTypes.length > 0 ? monitorTypes : undefined,
    });

  useEffect(() => {
    resetPagination();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery]);

  useEffect(() => {
    if (isError) {
      toast({
        title: "Error fetching data",
        description: "Please try again later",
        status: "error",
      });
    }
  }, [isError, toast]);

  const results =
    data?.items?.flatMap((monitor) =>
      !!monitor.key && typeof monitor.key !== "undefined" ? [monitor] : [],
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

  if (!webMonitorEnabled && !llmClassifierEnabled) {
    return <DisabledMonitorsPage />;
  }

  return (
    <FixedLayout
      title="Action center"
      mainProps={{ overflow: "hidden" }}
      fullHeight
    >
      <PageHeader
        heading="Action center"
        breadcrumbItems={[{ title: "All activity" }]}
        isSticky={false}
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
        <Flex
          className="h-[calc(100%-48px)] overflow-hidden"
          gap="middle"
          vertical
        >
          <Flex className="justify-between ">
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
            className="h-full overflow-scroll"
            renderItem={(summary) => {
              const link =
                summary.key && summary.monitorType
                  ? `${ACTION_CENTER_ROUTE}/${summary.monitorType}/${summary.key}`
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
          <Pagination
            {...paginationProps}
            total={data?.total || 0}
            showSizeChanger={{
              suffixIcon: <Icons.ChevronDown />,
            }}
            hideOnSinglePage={
              // if we're on the smallest page size, and there's only one page, hide the pagination
              paginationProps.pageSize?.toString() ===
              paginationProps.pageSizeOptions?.[0]
            }
          />
        </Flex>
      )}
    </FixedLayout>
  );
};

export default ActionCenterPage;
