import classNames from "classnames";
import { Button, Card, Flex, Icons, Text } from "fidesui";
import Link from "next/link";

import { useFlags } from "~/features/common/features";
import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";

import { useGetAggretateStatisticsQuery } from "./action-center.slice";
import { ProgressCard } from "./ProgressCard/ProgressCard";
import {
  MONITOR_TYPE_TO_EMPTY_TEXT,
  MONITOR_TYPE_TO_ICON,
  MONITOR_TYPE_TO_LABEL,
  transformStatisticsResponseToCardProps,
} from "./ProgressCard/utils";

export interface MonitorStatsProps {
  monitorId?: string;
}

const MonitorStats = ({ monitorId }: MonitorStatsProps) => {
  const {
    flags: { heliosInsights },
  } = useFlags();

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

  const { data: infrastructureStatistics } = useGetAggretateStatisticsQuery(
    {
      monitor_type: "infrastructure",
      monitor_config_id: monitorId,
    },
    { refetchOnMountOrArgChange: true },
  );

  const statistics = [
    ...(infrastructureStatistics ? [infrastructureStatistics] : []),
    ...(datastoreStatistics ? [datastoreStatistics] : []),
    ...(websiteStatistics ? [websiteStatistics] : []),
  ].flatMap(({ total_monitors = 0, ...response }) =>
    !monitorId || total_monitors > 0 ? [{ total_monitors, ...response }] : [],
  ); // filtering out statistics without monitors when on a specific monitor screen

  const renderIcon = (icon: Icons.CarbonIconType) => {
    const Icon = icon;
    return <Icon size={33} />;
  };

  return (
    heliosInsights && (
      <div
        className={classNames(
          ...["w-full", ...(!monitorId ? ["grid grid-cols-3 gap-4 pb-4"] : [])],
        )}
      >
        {statistics.map(({ total_monitors = 0, monitor_type, ...response }) =>
          total_monitors > 0 ? (
            <ProgressCard
              {...transformStatisticsResponseToCardProps({
                total_monitors,
                monitor_type,
                ...response,
              })}
              key={monitor_type}
              compact={!!monitorId}
            />
          ) : (
            <Card
              title={<span>{MONITOR_TYPE_TO_LABEL[monitor_type]}</span>}
              key={monitor_type}
              size="small"
            >
              <Flex vertical gap="middle" align="center" justify="center">
                <Text>{renderIcon(MONITOR_TYPE_TO_ICON[monitor_type])}</Text>
                <Text type="secondary" className="text-center">
                  {MONITOR_TYPE_TO_EMPTY_TEXT[monitor_type]}
                </Text>
                <Link href={INTEGRATION_MANAGEMENT_ROUTE}>
                  <Button type="primary">Create</Button>
                </Link>
              </Flex>
            </Card>
          ),
        )}
      </div>
    )
  );
};

export default MonitorStats;
