import classNames from "classnames";
import {
  Badge,
  BadgeProps,
  Button,
  Dropdown,
  DropdownProps,
  Flex,
  Icons,
  Menu,
} from "fidesui";
import _ from "lodash";
import { PropsWithChildren } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { pluralize } from "~/features/common/utils";
import useActionCenterNavigation, {
  ActionCenterRoute,
  ActionCenterRouteConfig,
} from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterNavigation";
import { AggregateStatisticsResponse } from "~/types/api/models/AggregateStatisticsResponse";
import { APIMonitorType } from "~/types/api/models/APIMonitorType";

import { useGetAggretateStatisticsQuery } from "./action-center.slice";
import { MONITOR_UPDATE_LABELS } from "./constants";
import { MonitorStatCard, MonitorStatCardProps } from "./MonitorStatCard";

export interface ActionCenterLayoutProps {
  monitorId?: string;
  routeConfig: ActionCenterRouteConfig;
  pageSettings?: {
    dropdownProps?: DropdownProps;
    badgeProps?: BadgeProps;
  };
}

const getMonitorUpdateName = (key: string, count: number) => {
  const names = Object.entries(MONITOR_UPDATE_LABELS).find(
    ([k]) => key === k,
  )?.[1];

  if (!names) {
    return key;
  }
  // names is [singular, plural]
  return pluralize(count, ...names);
};

const MONITOR_TYPE_TO_LABEL: Record<APIMonitorType, string> = {
  datastore: "Data stores",
  infrastructure: "Infrastructure",
  website: "Web monitors",
};

const MONITOR_TYPE_TO_PRIMARY_STATISTIC: Record<APIMonitorType, string> = {
  datastore: "Resources approved",
  infrastructure: "Total systems",
  website: "Resources approved",
};

const MONITOR_TYPE_TO_NUMERIC_STATISTIC: Record<
  APIMonitorType,
  keyof AggregateStatisticsResponse
> = {
  datastore: "status_counts",
  infrastructure: "vendor_counts",
  website: "status_counts",
};

const MONITOR_TYPE_TO_PERCENT_STATISTIC_KEY: Record<
  APIMonitorType,
  keyof NonNullable<AggregateStatisticsResponse["top_classifications"]>
> = {
  datastore: "data_categories",
  infrastructure: "data_uses",
  website: "data_uses",
};

const MONITOR_TYPE_TO_PERECENT_STATISTIC_LABEL: Record<APIMonitorType, string> =
  {
    datastore: "Data categories",
    infrastructure: "Data uses",
    website: "Categories of consent",
  };

export const transformStatisticsResponseToCardProps = (
  response: AggregateStatisticsResponse,
): MonitorStatCardProps => ({
  title: MONITOR_TYPE_TO_LABEL[response.monitor_type],
  subtitle: `${response?.total_monitors} ${pluralize(response?.total_monitors ?? 0, "monitor", "monitors")}`,
  primaryStat: {
    label: MONITOR_TYPE_TO_PRIMARY_STATISTIC[response.monitor_type],
    denominator: response?.approval_progress?.total,
    numerator: response?.approval_progress?.approved,
    percent: response?.approval_progress?.percentage,
  },
  numericStats: {
    label: "Current status",
    data: Object.entries(
      response?.[MONITOR_TYPE_TO_NUMERIC_STATISTIC[response.monitor_type]] ??
        [],
    ).flatMap(([label, value]) =>
      value
        ? [{ label: getMonitorUpdateName(label, value), count: value }]
        : [],
    ),
  },
  percentageStats: {
    label: MONITOR_TYPE_TO_PERECENT_STATISTIC_LABEL[response.monitor_type],
    data: (
      response?.top_classifications?.[
        MONITOR_TYPE_TO_PERCENT_STATISTIC_KEY[response.monitor_type]
      ] ?? []
    ).flatMap(({ name, percentage }) => ({ label: name, value: percentage })),
  },
  lastUpdated: response?.last_updated ?? undefined,
});

const ActionCenterLayout = ({
  children,
  monitorId,
  routeConfig,
  pageSettings,
}: PropsWithChildren<ActionCenterLayoutProps>) => {
  const {
    items: menuItems,
    activeItem,
    setActiveItem,
  } = useActionCenterNavigation(routeConfig);
  const { data: websiteStatistics } = useGetAggretateStatisticsQuery(
    {
      monitor_type: "website",
      monitor_config_id: monitorId,
    },
    { refetchOnMountOrArgChange: true },
  );

  const { data: datastoreStatistics } = useGetAggretateStatisticsQuery(
    {
      monitor_type: "datastore",
      monitor_config_id: monitorId,
    },
    { refetchOnMountOrArgChange: true },
  );

  const { data: infrastructureStatistics } = useGetAggretateStatisticsQuery({
    monitor_type: "infrastructure",
    monitor_config_id: monitorId,
  });

  return (
    <FixedLayout
      title="Action center"
      mainProps={{ overflow: "hidden" }}
      fullHeight
    >
      <PageHeader
        heading="Action center"
        breadcrumbItems={[
          { title: "All activity", href: ACTION_CENTER_ROUTE },
          ...(monitorId ? [{ title: monitorId }] : []),
        ]}
        isSticky={false}
        rightContent={
          pageSettings && (
            <Flex>
              <Badge {...pageSettings.badgeProps}>
                <Dropdown {...pageSettings.dropdownProps}>
                  <Button
                    aria-label="Page settings"
                    icon={<Icons.SettingsView />}
                  />
                </Dropdown>
              </Badge>
            </Flex>
          )
        }
      />
      <div
        className={classNames(
          ...["w-full", ...(!monitorId ? ["grid grid-cols-3 gap-4 pb-4"] : [])],
        )}
      >
        {[infrastructureStatistics, datastoreStatistics, websiteStatistics].map(
          (response) =>
            response && (response.total_monitors ?? 0) > 0 ? (
              <MonitorStatCard
                {...transformStatisticsResponseToCardProps(response)}
                key={response?.monitor_type}
                compact={!!monitorId}
              />
            ) : null,
        )}
      </div>
      <Menu
        aria-label="Action center tabs"
        mode="horizontal"
        items={Object.values(menuItems)}
        selectedKeys={_.compact([activeItem])}
        onClick={async (menuInfo) => {
          const validKey = Object.values(ActionCenterRoute).find(
            (value) => value === menuInfo.key,
          );
          if (validKey) {
            await setActiveItem(validKey);
          }
        }}
        className="mb-4"
        data-testid="action-center-tabs"
      />
      {children}
    </FixedLayout>
  );
};

export default ActionCenterLayout;
