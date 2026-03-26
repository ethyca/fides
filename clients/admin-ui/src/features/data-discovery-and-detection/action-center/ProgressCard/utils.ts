import { Icons } from "fidesui";

import { pluralize } from "~/features/common/utils";
import { AggregateStatisticsResponse } from "~/types/api/models/AggregateStatisticsResponse";
import { APIMonitorType } from "~/types/api/models/APIMonitorType";

import { MONITOR_UPDATE_LABELS } from "../constants";
import { ProgressCardProps } from "./ProgressCard";

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

export const MONITOR_TYPE_TO_LABEL: Record<APIMonitorType, string> = {
  datastore: "Data stores",
  infrastructure: "Infrastructure",
  website: "Web monitors",
};

export const MONITOR_TYPE_TO_ICON: Record<
  APIMonitorType,
  Icons.CarbonIconType
> = {
  datastore: Icons.DataBase,
  infrastructure: Icons.TransformInstructions,
  website: Icons.Wikis,
};

export const MONITOR_TYPE_TO_EMPTY_TEXT: Record<APIMonitorType, string> = {
  datastore:
    "Connect to a data store to begin discovering and classifying sensitive data fields.",
  infrastructure:
    "Connect an identity provider or cloud environment to populate the system inventory.",
  website:
    "Add a web monitor to start tracking cookies, tags, and other resources accross your sites.",
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
): ProgressCardProps => ({
  title: MONITOR_TYPE_TO_LABEL[response.monitor_type],
  subtitle: `${response?.total_monitors} ${pluralize(response?.total_monitors ?? 0, "monitor", "monitors")}`,
  progress: {
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
