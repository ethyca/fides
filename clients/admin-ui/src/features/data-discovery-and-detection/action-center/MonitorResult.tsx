import { formatDistance } from "date-fns";
import {
  AntAvatar as Avatar,
  AntCol as Col,
  AntList as List,
  AntListItemProps as ListItemProps,
  AntRow as Row,
  AntSkeleton as Skeleton,
  AntTooltip as Tooltip,
  AntTypography as Typography,
  Icons,
} from "fidesui";
import NextLink from "next/link";
import { useEffect, useState } from "react";

import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import { formatDate, getWebsiteIconUrl } from "~/features/common/utils";

import { MonitorAggregatedResults } from "./types";

const { Text } = Typography;

interface MonitorResultProps extends ListItemProps {
  monitorSummary: MonitorAggregatedResults;
  showSkeleton?: boolean;
}

export const MonitorResult = ({
  monitorSummary,
  showSkeleton,
  ...props
}: MonitorResultProps) => {
  const [iconUrl, setIconUrl] = useState<string | undefined>(undefined);

  const {
    name,
    property,
    total_updates: totalUpdates,
    updates,
    last_monitored: lastMonitored,
    warning,
    key,
  } = monitorSummary;

  const assetCountString = Object.entries(updates)
    .map((update) => {
      return `${update[1]} ${update[0]}s`;
    })
    .join(", ");

  const formattedLastMonitored = lastMonitored
    ? formatDate(new Date(lastMonitored))
    : undefined;

  const lastMonitoredDistance = lastMonitored
    ? formatDistance(new Date(lastMonitored), new Date(), {
        addSuffix: true,
      })
    : undefined;

  useEffect(() => {
    if (property) {
      setIconUrl(getWebsiteIconUrl(property));
    }
  }, [property]);

  return (
    <List.Item data-testid={`monitor-result-${key}`} {...props}>
      <Skeleton avatar title={false} loading={showSkeleton} active>
        <Row gutter={12} className="w-full">
          <Col span={18} className="align-middle">
            <List.Item.Meta
              avatar={
                <Avatar
                  src={iconUrl}
                  size="small"
                  icon={<Icons.Wikis />}
                  style={{
                    backgroundColor: "transparent",
                    color: "var(--ant-color-text)",
                  }}
                />
              }
              title={
                <NextLink
                  href={`${ACTION_CENTER_ROUTE}/${key}`}
                  className="whitespace-nowrap"
                >
                  {`${totalUpdates} assets detected${property ? ` on ${property}` : ""}`}
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
          </Col>
          <Col span={3} className="flex items-center justify-end">
            <Text ellipsis={{ tooltip: name }}>{name}</Text>
          </Col>
          <Col span={3} className="flex items-center justify-end">
            {!!lastMonitoredDistance && (
              <Tooltip title={formattedLastMonitored}>
                <Text
                  data-testid="monitor-date"
                  ellipsis={{ tooltip: formattedLastMonitored }}
                >
                  {lastMonitoredDistance}
                </Text>
              </Tooltip>
            )}
          </Col>
        </Row>
      </Skeleton>
    </List.Item>
  );
};
