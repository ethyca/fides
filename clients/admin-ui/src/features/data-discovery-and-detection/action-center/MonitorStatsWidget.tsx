import { Descriptions, Flex, Paragraph, Text } from "fidesui";
import { useQueryStates } from "nuqs";

import { useFlags } from "~/features/common/features";
import { nFormatter } from "~/features/common/utils";
import { APIMonitorType } from "~/types/api/models/APIMonitorType";

import { useGetAggregateStatisticsQuery } from "./action-center.slice";
import { SearchFormQueryState } from "./MonitorList.const";
import { buildWidgetProps } from "./ProgressCard/utils";

export interface MonitorStatsWidgetProps {
  monitorId?: string;
  monitorType: APIMonitorType;
}

const MonitorStatsWidget = ({
  monitorId,
  monitorType,
}: MonitorStatsWidgetProps) => {
  const {
    flags: { heliosInsights },
  } = useFlags();
  const [filters] = useQueryStates(
    SearchFormQueryState(Object.values(APIMonitorType)),
  );

  const { data } = useGetAggregateStatisticsQuery(
    {
      monitor_type: monitorType,
      monitor_config_id: monitorId,
      steward_user_id: filters.steward_key ? [filters.steward_key] : undefined,
    },
    {
      refetchOnMountOrArgChange: true,
    },
  );

  const totalMonitors = data?.total_monitors ?? 0;
  const { numericStats, percentageStats } = buildWidgetProps({
    monitor_type: monitorType,
    total_monitors: totalMonitors,
    ...data,
  });

  return (
    heliosInsights && (
      <Flex className="w-full" gap="middle" vertical>
        <Text strong>Classification</Text>
        <Descriptions
          size="small"
          items={[
            {
              label: numericStats?.label,
              children: (
                <Paragraph
                  ellipsis={{
                    rows: 1,
                    tooltip: {
                      title: numericStats?.data
                        .map((stat) => `${stat.count} ${stat.label}`)
                        .join(", "),
                    },
                  }}
                >
                  {numericStats?.data
                    .map((stat) => `${stat.count} ${stat.label}`)
                    .join(", ")}
                </Paragraph>
              ),
              span: "filled",
            },
            {
              label: percentageStats?.label,
              children: (
                <Paragraph
                  ellipsis={{
                    rows: 1,
                    tooltip: percentageStats?.data
                      .map(
                        (stat) => `${stat.label} (${nFormatter(stat.value)}%)`,
                      )
                      .join(", "),
                  }}
                >
                  {percentageStats?.data
                    .map((stat) => `${stat.label} (${nFormatter(stat.value)}%)`)
                    .join(", ")}
                </Paragraph>
              ),

              span: "filled",
            },
          ]}
        />
      </Flex>
    )
  );
};

export default MonitorStatsWidget;
