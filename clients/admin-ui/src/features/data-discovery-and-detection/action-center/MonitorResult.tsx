import { formatDistance } from "date-fns";
import {
  AntAvatar as Avatar,
  AntFlex as Flex,
  AntList as List,
  AntListItemProps as ListItemProps,
  AntSkeleton as Skeleton,
  AntTooltip as Tooltip,
  AntTypography as Typography,
  Icons,
} from "fidesui";
import NextLink from "next/link";

import { ACTION_CENTER_ROUTE } from "~/features/common/nav/v2/routes";
import { formatDate, getWebsiteIconUrl } from "~/features/common/utils";

import { MonitorSummary } from "./types";

const { Text } = Typography;

interface MonitorResultProps extends ListItemProps {
  monitorSummary: MonitorSummary;
  showSkeleton?: boolean;
}

export const MonitorResult = ({
  monitorSummary,
  showSkeleton,
  ...props
}: MonitorResultProps) => {
  if (!monitorSummary) {
    return null;
  }

  const {
    name,
    hostname,
    total_assets: totalAssets,
    asset_counts: assetCounts,
    last_monitored: lastMonitored,
    warning,
    monitor_config_id: monitorConfigId,
  } = monitorSummary;

  const assetCountString = assetCounts
    .map(({ type, count }) => {
      return `${count} ${type}`;
    })
    .join(", ");

  const lastMonitoredDistance = formatDistance(
    new Date(lastMonitored),
    new Date(),
    {
      addSuffix: true,
    },
  );

  const iconUrl = getWebsiteIconUrl(hostname);

  return (
    <List.Item {...props}>
      <Skeleton avatar title={false} loading={showSkeleton} active>
        <List.Item.Meta
          avatar={<Avatar src={iconUrl} size="small" />}
          title={
            <NextLink
              href={`${ACTION_CENTER_ROUTE}/${monitorConfigId}`}
              className="whitespace-nowrap"
            >
              {`${totalAssets} assets detected on ${hostname}`}
              {!!warning && (
                <Tooltip
                  title={typeof warning === "string" ? warning : undefined}
                >
                  <Icons.WarningAltFilled
                    className="ml-1 inline-block align-middle"
                    style={{ color: "var(--fidesui-error)" }}
                  />
                </Tooltip>
              )}
            </NextLink>
          }
          description={`${assetCountString} detected.`}
        />
        <Flex className="gap-12">
          <Text style={{ maxWidth: 300 }} ellipsis={{ tooltip: name }}>
            {name}
          </Text>
          <Tooltip title={formatDate(lastMonitored)}>
            <Text>{lastMonitoredDistance}</Text>
          </Tooltip>
        </Flex>
      </Skeleton>
    </List.Item>
  );
};
