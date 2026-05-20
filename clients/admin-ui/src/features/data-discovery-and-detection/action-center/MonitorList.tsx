import { skipToken } from "@reduxjs/toolkit/query";
import { Flex, Icons, List, Pagination, useMessage } from "fidesui";
import { useEffect } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import { useFeatures } from "~/features/common/features";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { useGetAggregateMonitorResultsQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { EmptyMonitorsResult } from "~/features/data-discovery-and-detection/action-center/EmptyMonitorsResult";
import useSearchForm from "~/features/data-discovery-and-detection/action-center/hooks/useSearchForm";
import {
  MOCK_AWS_MONITOR_KEY,
  MOCK_AWS_MONITOR_SUMMARY,
} from "~/features/data-discovery-and-detection/action-center/mock/awsCloudInfraMock";
import { MonitorResult } from "~/features/data-discovery-and-detection/action-center/MonitorResult";
import { useGetUserMonitorsQuery } from "~/features/user-management";
import { APIMonitorType } from "~/types/api/models/APIMonitorType";

import MonitorListSearchForm from "./forms/MonitorListSearchForm";
import {
  MonitorSearchForm,
  MonitorSearchFormQuerySchema,
  SearchFormQueryState,
} from "./MonitorList.const";
import MonitorStats from "./MonitorStats";

const MonitorList = () => {
  const message = useMessage();
  const {
    flags: { webMonitor: webMonitorEnabled, awsMonitor: awsMonitorEnabled },
  } = useFeatures();
  const { paginationProps, pageIndex, pageSize, resetPagination } =
    useAntPagination();

  const availableMonitorTypes = [
    ...(webMonitorEnabled ? [APIMonitorType.WEBSITE] : []),
    APIMonitorType.DATASTORE,
    APIMonitorType.INFRASTRUCTURE,
    ...(awsMonitorEnabled ? [APIMonitorType.CLOUD_INFRASTRUCTURE] : []),
  ] as const;

  const currentUser = useAppSelector(selectUser);

  const { data: userMonitors } = useGetUserMonitorsQuery(
    currentUser?.id
      ? {
          id: currentUser.id,
        }
      : skipToken,
  );

  const defaultStewardFilter =
    (userMonitors ?? []).length > 0 ? currentUser?.id : undefined;

  const { requestData, setSearchForm, ...formProps } = useSearchForm<
    Partial<Parameters<typeof useGetAggregateMonitorResultsQuery>[0]>,
    MonitorSearchForm
  >({
    schema: MonitorSearchFormQuerySchema([...availableMonitorTypes]),
    queryState: SearchFormQueryState([...availableMonitorTypes]),
    initialValues: {
      search: null,
      monitor_type: null,
      steward_key: defaultStewardFilter ?? null,
    },
    translate: ({ search, monitor_type, steward_key }) => {
      return {
        search: search || undefined,
        monitor_type: monitor_type
          ? [monitor_type]
          : [
              ...availableMonitorTypes,
            ] /** this should be handled via ant binding ideally. * */,
        steward_user_id:
          typeof steward_key === "undefined" || !steward_key
            ? []
            : [steward_key],
      };
    },
  });

  const normalizedRequest =
    typeof requestData === "object" && requestData !== null ? requestData : {};

  // BE doesn't yet accept "cloud_infrastructure" as a monitor_type query value
  // (returns 422). Strip it from the BE call; the mock row is injected client-side
  // below. If filtering specifically to cloud_infrastructure, omit the param so
  // the BE doesn't error — we only want the mock row anyway.
  const requestedMonitorTypes = normalizedRequest.monitor_type;
  const beMonitorTypes = requestedMonitorTypes?.filter(
    (t) => t !== APIMonitorType.CLOUD_INFRASTRUCTURE,
  );
  const onlyCloudInfraRequested =
    !!requestedMonitorTypes?.length && beMonitorTypes?.length === 0;

  const { data, isError, isLoading } = useGetAggregateMonitorResultsQuery(
    {
      ...normalizedRequest,
      monitor_type: beMonitorTypes,
      page: pageIndex,
      size: pageSize,
    },
    {
      skip: onlyCloudInfraRequested,
    },
  );

  useEffect(() => {
    if (defaultStewardFilter) {
      setSearchForm({ steward_key: defaultStewardFilter });
    }
  }, [setSearchForm, defaultStewardFilter]);

  useEffect(() => {
    if (isError) {
      message.error("Error fetching data. Please try again later");
    }
  }, [isError, message]);

  const results =
    data?.items?.flatMap((monitor) =>
      !!monitor.key && typeof monitor.key !== "undefined" ? [monitor] : [],
    ) || [];

  const monitorTypeFilter =
    normalizedRequest.monitor_type ?? availableMonitorTypes;
  const searchFilter = normalizedRequest.search ?? "";
  const shouldShowMockAws =
    awsMonitorEnabled &&
    pageIndex === 1 &&
    monitorTypeFilter.includes(APIMonitorType.CLOUD_INFRASTRUCTURE) &&
    !results.some((m) => m.key === MOCK_AWS_MONITOR_KEY) &&
    (!searchFilter ||
      MOCK_AWS_MONITOR_SUMMARY.name
        .toLowerCase()
        .includes(searchFilter.toLowerCase()));

  const displayResults = shouldShowMockAws
    ? [MOCK_AWS_MONITOR_SUMMARY, ...results]
    : results;

  return (
    <Flex className="h-[calc(100%-48px)] overflow-hidden" gap="medium" vertical>
      <MonitorListSearchForm
        {...formProps}
        onFinish={(values) => {
          formProps.onFinish(values);
          resetPagination();
        }}
        availableMonitorTypes={availableMonitorTypes}
      />
      <MonitorStats />
      <List
        loading={isLoading}
        dataSource={displayResults}
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
