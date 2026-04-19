import { Button, Flex, Icons, Text, Title } from "fidesui";
import { useQueryStates } from "nuqs";

import { useFlags } from "~/features/common/features";
import { RouterLink } from "~/features/common/nav/RouterLink";
import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import { APIMonitorType } from "~/types/api/models/APIMonitorType";

import { useGetAggregateStatisticsQuery } from "./action-center.slice";
import { SearchFormQueryState } from "./MonitorList.const";
import { ProgressCard } from "./ProgressCard/ProgressCard";
import {
  buildWidgetProps,
  MONITOR_TYPE_TO_EMPTY_TEXT,
  MONITOR_TYPE_TO_ICON,
  MONITOR_TYPE_TO_LABEL,
} from "./ProgressCard/utils";

export interface MonitorProgressWidgetProps {
  monitorId?: string;
  monitorType: APIMonitorType;
  disabled?: boolean;
}

const renderIcon = (icon: Icons.CarbonIconType) => {
  const Icon = icon;
  return <Icon size={33} />;
};

const MonitorProgressWidget = ({
  monitorId,
  monitorType,
}: MonitorProgressWidgetProps) => {
  const {
    flags: { heliosInsights },
  } = useFlags();
  const [filters] = useQueryStates(
    SearchFormQueryState(Object.values(APIMonitorType)),
  );

  const { data, isLoading } = useGetAggregateStatisticsQuery(
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

  return (
    heliosInsights && (
      <Flex className="w-full" gap="middle">
        {(data && totalMonitors > 0) || !!filters.steward_key || isLoading ? (
          <ProgressCard
            {...buildWidgetProps({
              monitor_type: monitorType,
              total_monitors: totalMonitors,
              ...data,
            })}
            compact={!!monitorId}
            disabled={
              (!!filters.monitor_type &&
                monitorType !== filters.monitor_type) ||
              (!!filters.steward_key && totalMonitors <= 0)
            }
          />
        ) : (
          <div>
            <Flex vertical gap="small" justify="center">
              <Title level={5}>{MONITOR_TYPE_TO_LABEL[monitorType]}</Title>
              <Text>{renderIcon(MONITOR_TYPE_TO_ICON[monitorType])}</Text>
              <Text type="secondary">
                {MONITOR_TYPE_TO_EMPTY_TEXT[monitorType]}
              </Text>
              <RouterLink href={INTEGRATION_MANAGEMENT_ROUTE}>
                <Button type="primary">Create</Button>
              </RouterLink>
            </Flex>
          </div>
        )}
      </Flex>
    )
  );
};

export default MonitorProgressWidget;
