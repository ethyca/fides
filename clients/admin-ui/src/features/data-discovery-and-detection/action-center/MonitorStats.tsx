import { skipToken } from "@reduxjs/toolkit/query";
import classNames from "classnames";
import { Button, Divider, Flex, OpenCloseArrow, Text } from "fidesui";
import { motion } from "motion/react";
import { useQueryStates } from "nuqs";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import { useFeatures } from "~/features/common/features";
import { useGetAllUsersQuery, useGetUserMonitorsQuery } from "~/features/user-management";
import { AggregateStatisticsResponse } from "~/types/api/models/AggregateStatisticsResponse";
import { APIMonitorType } from "~/types/api/models/APIMonitorType";

import { useGetAggregateStatisticsQuery } from "./action-center.slice";
import { getDashboardMockStats } from "./mockDashboardData";
import { SearchFormQueryState } from "./MonitorList.const";
import MonitorStatsCollapsed from "./MonitorStatsCollapsed";
import AnimatedProgressCard from "./ProgressCard/AnimatedProgressCard";
import { ProgressCard } from "./ProgressCard/ProgressCard";
import SummaryCard from "./ProgressCard/SummaryCard";
import { transformStatisticsResponseToCardProps } from "./ProgressCard/utils";
import SchemaExplorerDashboard from "./SchemaExplorerDashboard";
import { MONITOR_TYPES } from "./utils/getMonitorType";

export interface MonitorStatsProps {
  monitorId?: string;
  isExpanded?: boolean;
  onToggle?: () => void;
  /** "sidebar" = left panel (default), "top" = horizontal cards above content */
  layout?: "sidebar" | "top";
}

const MonitorStats = ({
  monitorId,
  isExpanded = false,
  onToggle,
  layout = "sidebar",
}: MonitorStatsProps) => {
  const {
    flags: { heliosInsights, webMonitor: webMonitorEnabled },
  } = useFeatures();

  // Read filter state from URL (same nuqs parsers as MonitorList)
  const availableMonitorTypes = [
    ...(webMonitorEnabled ? [MONITOR_TYPES.WEBSITE] : []),
    MONITOR_TYPES.DATASTORE,
    MONITOR_TYPES.INFRASTRUCTURE,
  ] as const;

  const currentUser = useAppSelector(selectUser);
  const { data: userMonitors } = useGetUserMonitorsQuery(
    currentUser?.id ? { id: currentUser.id } : skipToken,
  );
  const defaultStewardFilter =
    (userMonitors ?? []).length > 0 ? currentUser?.id : undefined;

  const [searchForm] = useQueryStates(
    SearchFormQueryState([...availableMonitorTypes], defaultStewardFilter),
  );

  // Fetch all users to resolve steward name for mock overrides
  const { data: allUsers } = useGetAllUsersQuery({
    page: 1,
    size: 100,
  });
  const activeStewName = useMemo(() => {
    if (!searchForm.steward_key || !allUsers?.items) return undefined;
    const user = allUsers.items.find((u) => u.id === searchForm.steward_key);
    return user
      ? `${user.first_name ?? ""} ${user.last_name ?? ""}`.trim()
      : undefined;
  }, [searchForm.steward_key, allUsers]);

  const { data: websiteStatistics } = useGetAggregateStatisticsQuery(
    {
      monitor_type: "website",
      monitor_config_id: monitorId ? [monitorId] : undefined,
    },
    { refetchOnMountOrArgChange: true },
  );

  const { data: datastoreStatistics } = useGetAggregateStatisticsQuery(
    {
      monitor_type: "datastore",
      monitor_config_id: monitorId ? [monitorId] : undefined,
    },
    { refetchOnMountOrArgChange: true },
  );

  const { data: infrastructureStatistics } = useGetAggregateStatisticsQuery(
    {
      monitor_type: "infrastructure",
      monitor_config_id: monitorId ? [monitorId] : undefined,
    },
    { refetchOnMountOrArgChange: true },
  );

  // Apply mock overrides when steward filter is active
  const applyMockOverride = (
    realData: AggregateStatisticsResponse | undefined,
    monitorType: APIMonitorType,
  ): AggregateStatisticsResponse | undefined => {
    if (!realData || monitorId) return realData;
    const override = getDashboardMockStats(
      monitorType,
      searchForm.steward_key,
      activeStewName,
    );
    if (!override) return realData;
    return { ...realData, ...override, monitor_type: monitorType };
  };

  const statistics = [
    applyMockOverride(infrastructureStatistics, APIMonitorType.INFRASTRUCTURE),
    applyMockOverride(datastoreStatistics, APIMonitorType.DATASTORE),
    applyMockOverride(websiteStatistics, APIMonitorType.WEBSITE),
  ]
    .flatMap((s) => (s ? [s] : []))
    .flatMap(({ total_monitors = 0, ...response }) =>
      !monitorId || total_monitors > 0
        ? [{ total_monitors, ...response }]
        : [],
    );

  if (!heliosInsights) {
    return null;
  }

  // On a specific monitor page (schema explorer), three-section dashboard
  if (monitorId) {
    const stat = statistics[0];
    if (!stat) return null;
    return (
      <SchemaExplorerDashboard
        stat={stat as AggregateStatisticsResponse}
        monitorId={monitorId}
      />
    );
  }

  // Top layout: always-visible summary cards above content
  if (layout === "top") {
    return (
      <div className="w-full pb-4">
        <Flex>
          {statistics.map(
            ({ total_monitors = 0, monitor_type, ...response }, index) => {
              const isDimmed =
                (searchForm.monitor_type != null &&
                  (monitor_type as string) !== searchForm.monitor_type) ||
                total_monitors === 0;

              return (
                <Flex key={monitor_type} className="min-w-0 flex-1">
                  {index > 0 && (
                    <Divider
                      type="vertical"
                      className="!mx-4 !h-auto self-stretch"
                    />
                  )}
                  <div
                    className={classNames(
                      "min-w-0 flex-1 transition-opacity duration-1000 ease-in-out",
                      isDimmed && "pointer-events-none opacity-30",
                    )}
                  >
                    <SummaryCard
                      stat={{
                        total_monitors,
                        monitor_type,
                        ...response,
                      }}
                    />
                  </div>
                </Flex>
              );
            },
          )}
        </Flex>
      </div>
    );
  }

  // Sidebar layout: always-visible summary cards
  return (
    <div className="h-full w-[260px] overflow-y-auto overflow-x-hidden pr-2">
      <Flex vertical>
        {statistics.map(
          ({ total_monitors = 0, monitor_type, ...response }, index) => {
            const isDimmed =
              (searchForm.monitor_type != null &&
                (monitor_type as string) !== searchForm.monitor_type) ||
              total_monitors === 0;

            return (
              <div
                key={monitor_type}
                className={classNames(
                  "transition-opacity duration-1000 ease-in-out",
                  isDimmed && "pointer-events-none opacity-30",
                )}
              >
                {index > 0 && <Divider className="!my-2" />}
                <SummaryCard
                  stat={{
                    total_monitors,
                    monitor_type,
                    ...response,
                  }}
                />
              </div>
            );
          },
        )}
      </Flex>
    </div>
  );
};

export default MonitorStats;
