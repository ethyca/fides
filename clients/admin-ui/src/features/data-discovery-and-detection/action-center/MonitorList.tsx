import {
  Flex,
  Icons,
  List,
  Pagination,
  Select,
  useChakraToast as useToast,
} from "fidesui";
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

const MonitorList = () => {
  const toast = useToast();
  const {
    flags: {
      webMonitor: webMonitorEnabled,
      heliosV2: heliosV2Enabled,
      oktaMonitor: oktaMonitorEnabled,
    },
  } = useFeatures();
  const { paginationProps, pageIndex, pageSize, resetPagination } =
    useAntPagination();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFilter, setSelectedFilter] = useState<string>("all");

  // Build filter options based on enabled monitor types
  const filterOptions = [
    ...(webMonitorEnabled || heliosV2Enabled || oktaMonitorEnabled
      ? [{ value: "all", label: "All monitors" }]
      : []),
    ...(heliosV2Enabled
      ? [{ value: MONITOR_TYPES.DATASTORE, label: "Data store monitors" }]
      : []),
    ...(webMonitorEnabled
      ? [{ value: MONITOR_TYPES.WEBSITE, label: "Website monitors" }]
      : []),
    ...(oktaMonitorEnabled
      ? [
          {
            value: MONITOR_TYPES.INFRASTRUCTURE,
            label: "Infrastructure monitors",
          },
        ]
      : []),
  ];

  // Only show filter when 2+ monitor types are enabled (meaning 3+ options including "all")
  const shouldShowFilter = filterOptions.length > 2;

  // Build monitor_type filter based on selected filter
  const getMonitorTypesFromFilter = (
    filter: string,
  ): MONITOR_TYPES[] | undefined => {
    if (filter === MONITOR_TYPES.DATASTORE) {
      return [MONITOR_TYPES.DATASTORE];
    }
    if (filter === MONITOR_TYPES.WEBSITE) {
      return [MONITOR_TYPES.WEBSITE];
    }
    if (filter === MONITOR_TYPES.INFRASTRUCTURE) {
      return [MONITOR_TYPES.INFRASTRUCTURE];
    }
    // "all" - return all enabled monitor types
    const allTypes = [
      ...(webMonitorEnabled ? [MONITOR_TYPES.WEBSITE] : []),
      ...(heliosV2Enabled ? [MONITOR_TYPES.DATASTORE] : []),
      ...(oktaMonitorEnabled ? [MONITOR_TYPES.INFRASTRUCTURE] : []),
    ];
    return allTypes.length > 0 ? allTypes : undefined;
  };

  const monitorTypes = getMonitorTypesFromFilter(selectedFilter);

  const { data, isError, isLoading } = useGetAggregateMonitorResultsQuery({
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
    monitor_type: monitorTypes,
  });

  // Reset filter if selected option is no longer available
  useEffect(() => {
    const isValidFilter = filterOptions.some(
      (option) => option.value === selectedFilter,
    );
    if (!isValidFilter && filterOptions.length > 0) {
      setSelectedFilter(filterOptions[0].value);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [webMonitorEnabled, heliosV2Enabled, oktaMonitorEnabled]);

  useEffect(() => {
    resetPagination();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery, selectedFilter]);

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

  if (!webMonitorEnabled && !heliosV2Enabled && !oktaMonitorEnabled) {
    return <DisabledMonitorsPage />;
  }

  return (
    <Flex className="h-[calc(100%-48px)] overflow-hidden" gap="middle" vertical>
      <Flex className="items-center justify-between">
        <DebouncedSearchInput value={searchQuery} onChange={setSearchQuery} />
        {shouldShowFilter && (
          <Select
            value={selectedFilter}
            onChange={(value) => {
              if (typeof value === "string") {
                setSelectedFilter(value);
              }
            }}
            options={filterOptions}
            className="w-auto min-w-[200px]"
            data-testid="monitor-type-filter"
            aria-label="Filter by monitor type"
          />
        )}
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
