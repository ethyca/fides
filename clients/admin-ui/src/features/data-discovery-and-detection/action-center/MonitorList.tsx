import {
  Flex,
  Icons,
  List,
  Pagination,
  useChakraToast as useToast,
} from "fidesui";
import { useEffect } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import { useFeatures } from "~/features/common/features";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { useGetAggregateMonitorResultsQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { DisabledMonitorsPage } from "~/features/data-discovery-and-detection/action-center/DisabledMonitorsPage";
import { EmptyMonitorsResult } from "~/features/data-discovery-and-detection/action-center/EmptyMonitorsResult";
import useSearchForm from "~/features/data-discovery-and-detection/action-center/hooks/useSearchForm";
import { MonitorResult } from "~/features/data-discovery-and-detection/action-center/MonitorResult";
import { MONITOR_TYPES } from "~/features/data-discovery-and-detection/action-center/utils/getMonitorType";

import MonitorListSearchForm from "./forms/MonitorListSearchForm";
import { SearchFormQueryState } from "./MonitorList.const";

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

  const availableMonitorTypes = [
    ...(webMonitorEnabled ? [MONITOR_TYPES.WEBSITE] : []),
    ...(heliosV2Enabled ? [MONITOR_TYPES.DATASTORE] : []),
    ...(oktaMonitorEnabled ? [MONITOR_TYPES.INFRASTRUCTURE] : []),
  ] as const;

  const currentUser = useAppSelector(selectUser);

  const { requestData, ...formProps } = useSearchForm({
    queryState: SearchFormQueryState(
      [...availableMonitorTypes],
      currentUser?.isRootUser ? undefined : currentUser?.id,
    ),
    initialValues: {
      steward_key: currentUser?.isRootUser ? null : (currentUser?.id ?? null),
    },
    translate: ({
      steward_key,
      search,
      monitor_type,
    }): Omit<
      Parameters<typeof useGetAggregateMonitorResultsQuery>[0],
      "page" | "size"
    > => {
      return {
        search: search || undefined,
        monitor_type: monitor_type ? [monitor_type] : undefined,
        steward_user_id:
          typeof steward_key === "undefined" || !steward_key
            ? []
            : [steward_key],
      };
    },
  });

  const { data, isError, isLoading } = useGetAggregateMonitorResultsQuery({
    ...(typeof requestData === "object" ? requestData : {}),
    page: pageIndex,
    size: pageSize,
  });

  useEffect(() => {
    resetPagination();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestData]);

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
      <MonitorListSearchForm
        {...formProps}
        availableMonitorTypes={availableMonitorTypes}
      />
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
