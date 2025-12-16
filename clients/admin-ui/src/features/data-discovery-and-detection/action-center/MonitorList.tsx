import {
  Flex,
  Icons,
  List,
  Pagination,
  useChakraToast as useToast,
} from "fidesui";
import { NextPage } from "next";
import { useEffect, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { useFeatures } from "~/features/common/features";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { useGetAggregateMonitorResultsQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { DisabledMonitorsPage } from "~/features/data-discovery-and-detection/action-center/DisabledMonitorsPage";
import { EmptyMonitorsResult } from "~/features/data-discovery-and-detection/action-center/EmptyMonitorsResult";
import { MonitorResult } from "~/features/data-discovery-and-detection/action-center/MonitorResult";
import { MONITOR_TYPES } from "~/features/data-discovery-and-detection/action-center/utils/getMonitorType";

const MonitorList: NextPage = () => {
  const toast = useToast();
  const {
    flags: { webMonitor: webMonitorEnabled, heliosV2: heliosV2Enabled },
  } = useFeatures();
  const { paginationProps, pageIndex, pageSize, resetPagination } =
    useAntPagination();
  const [searchQuery, setSearchQuery] = useState("");

  // Build monitor_type filter based on enabled feature flags
  const monitorTypes = [
    ...(webMonitorEnabled ? [MONITOR_TYPES.WEBSITE] : []),
    ...(heliosV2Enabled ? [MONITOR_TYPES.DATASTORE] : []),
  ] as const;

  const { data, isError, isLoading } = useGetAggregateMonitorResultsQuery({
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
    monitor_type: monitorTypes.length > 0 ? [...monitorTypes] : undefined,
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

  if (!webMonitorEnabled && !heliosV2Enabled) {
    return <DisabledMonitorsPage />;
  }

  return (
    <Flex className="h-[calc(100%-48px)] overflow-hidden" gap="middle" vertical>
      <Flex className="justify-between ">
        <DebouncedSearchInput value={searchQuery} onChange={setSearchQuery} />
      </Flex>
      <List
        loading={isLoading}
        dataSource={results}
        locale={{
          emptyText: <EmptyMonitorsResult />,
        }}
        className="h-full overflow-y-auto overflow-x-clip" // overflow-x-clip to prevent horizontal scroll. see https://stackoverflow.com/a/69767073/441894
        renderItem={(summary) => {
          const link =
            summary.key && summary.monitorType
              ? `${ACTION_CENTER_ROUTE}/${summary.monitorType}/${summary.key}`
              : "";
          return (
            !!summary?.key && (
              <MonitorResult
                key={summary.key}
                monitorSummary={summary}
                href={link}
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
  );
};

export default MonitorList;
