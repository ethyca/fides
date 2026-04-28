import { Icons, StackedBarChartProps } from "fidesui";

import { pluralize } from "~/features/common/utils";
import { AggregateStatisticsResponse } from "~/types/api/models/AggregateStatisticsResponse";
import { APIMonitorType } from "~/types/api/models/APIMonitorType";

import { STATUS_COUNTS_TO_RESOURCE_STATUS } from "../fields/MonitorFields.const";
import { ProgressCardProps } from "./ProgressCard";

export const MONITOR_TYPE_TO_LABEL: Record<APIMonitorType, string> = {
  datastore: "Monitored data stores",
  infrastructure: "Monitored infrastructure",
  website: "Monitored websites",
  cloud_infrastructure: "Monitored cloud infrastructure",
};

export const MONITOR_TYPE_TO_ICON: Record<
  APIMonitorType,
  Icons.CarbonIconType
> = {
  datastore: Icons.DataBase,
  infrastructure: Icons.TransformInstructions,
  website: Icons.Wikis,
  cloud_infrastructure: Icons.Cloud,
};

export const MONITOR_TYPE_TO_EMPTY_TEXT: Record<APIMonitorType, string> = {
  datastore:
    "Connect to a data store to begin discovering and classifying sensitive data fields.",
  infrastructure:
    "Connect an identity provider or cloud environment to populate the system inventory.",
  website:
    "Add a web monitor to start tracking cookies, tags, and other resources across your sites.",
  cloud_infrastructure:
    "Connect a cloud provider to discover and monitor your infrastructure resources.",
};

const MONITOR_TYPE_TO_PRIMARY_STATISTIC: Record<APIMonitorType, string> = {
  infrastructure: "Total systems",
  website: "Resources approved",
  datastore: "Resources approved",
  cloud_infrastructure: "Resources approved",
};

const MONITOR_TYPE_TO_PERCENT_STATISTIC_KEY: Record<
  APIMonitorType,
  keyof NonNullable<AggregateStatisticsResponse["top_classifications"]>
> = {
  datastore: "data_categories",
  infrastructure: "data_uses",
  website: "data_uses",
  cloud_infrastructure: "data_uses",
};

const MONITOR_TYPE_TO_PERCENT_STATISTIC_LABEL: Record<APIMonitorType, string> =
  {
    datastore: "Data categories",
    infrastructure: "Data uses",
    website: "Categories of consent",
    cloud_infrastructure: "Services",
  };

const MONITOR_BAR_CHART_SEGMENTS: StackedBarChartProps["segments"] = [
  {
    key: "approved",
    color: "colorSuccess",
    label: "Approved",
  },
  {
    key: "classified",
    color: "colorWarning",
    label: "Classified",
  },
  {
    key: "unlabeled",
    color: "colorPrimaryBg",
    label: "Unlabeled",
  },
  {
    key: "empty",
    color: "colorPrimaryBg",
    label: "",
  },
] as const;

export const buildWidgetProps = (
  response: AggregateStatisticsResponse,
): ProgressCardProps => ({
  title: MONITOR_TYPE_TO_LABEL[response.monitor_type],
  subtitle: `${response?.total_monitors} ${pluralize(response?.total_monitors ?? 0, "monitor", "monitors")}`,
  progress: {
    label: MONITOR_TYPE_TO_PRIMARY_STATISTIC[response.monitor_type],
    denominator: response?.approval_progress?.total,
    numerator: response?.status_counts?.monitored,
    percent: response?.approval_progress?.percentage,
  },
  barChartProps: {
    data: {
      progress: {
        approved: response.status_counts?.monitored ?? 0,
        classified:
          (response.status_counts?.reviewed ?? 0) +
          (response.status_counts?.classified ?? 0),
        unlabeled: response.status_counts?.addition ?? 0,
        empty:
          (response.status_counts?.monitored ?? 0) -
            (response.status_counts?.classified ?? 0) -
            (response.approval_progress?.percentage ?? 0) <=
          0
            ? 1
            : 0,
      },
    },
    segments: MONITOR_BAR_CHART_SEGMENTS,
  },
  numericStats: {
    label: "Current status",
    data: [
      {
        label: STATUS_COUNTS_TO_RESOURCE_STATUS.addition,
        count: response.status_counts?.addition ?? 0,
      },
      {
        label: STATUS_COUNTS_TO_RESOURCE_STATUS.classified,
        count:
          (response.status_counts?.classified ?? 0) +
          (response.status_counts?.reviewed ?? 0),
      },
      {
        label: STATUS_COUNTS_TO_RESOURCE_STATUS.classifying,
        count: response.status_counts?.classifying ?? 0,
      },
      {
        label: STATUS_COUNTS_TO_RESOURCE_STATUS.monitored,
        count: response.status_counts?.monitored ?? 0,
      },
      {
        label: STATUS_COUNTS_TO_RESOURCE_STATUS.removal,
        count: response.status_counts?.removal ?? 0,
      },
    ],
  },
  percentageStats: {
    label: MONITOR_TYPE_TO_PERCENT_STATISTIC_LABEL[response.monitor_type],
    data: (
      response?.top_classifications?.[
        MONITOR_TYPE_TO_PERCENT_STATISTIC_KEY[response.monitor_type]
      ] ?? []
    ).flatMap(({ name, percentage }) => ({ label: name, value: percentage })),
  },
  lastUpdated: response?.last_updated ?? undefined,
});
