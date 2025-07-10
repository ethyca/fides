import { formatDistance } from "date-fns";
import {
  AntAvatar as Avatar,
  AntCol as Col,
  AntFlex as Flex,
  AntList as List,
  AntListItemProps as ListItemProps,
  AntRow as Row,
  AntSkeleton as Skeleton,
  AntTooltip as Tooltip,
  AntTypography as Typography,
  Icons,
} from "fidesui";
import NextLink from "next/link";
import { useMemo } from "react";

import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import {
  formatDate,
  getDomain,
  getWebsiteIconUrl,
} from "~/features/common/utils";

import { DiscoveryStatusIcon } from "./DiscoveryStatusIcon";
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
  const {
    name,
    consent_status: consentStatus,
    total_updates: totalUpdates,
    updates,
    last_monitored: lastMonitored,
    secrets,
    key,
  } = monitorSummary;

  const property = useMemo(() => {
    return secrets?.url ? getDomain(secrets.url) : undefined;
  }, [secrets?.url]);

  const iconUrl = useMemo(() => {
    return property ? getWebsiteIconUrl(property, 60) : undefined;
  }, [property]);

  const assetCountString = Object.entries(updates)
    .map((update) => {
      return `${update[1]} ${update[0]}s`;
    })
    .join(", ");

  const formattedLastMonitored = lastMonitored
    ? formatDate(new Date(lastMonitored))
    : undefined;

  const lastMonitoredDistance = lastMonitored
    ? formatDistance(new Date(lastMonitored), new Date())
    : undefined;

  return (
    <List.Item data-testid={`monitor-result-${key}`} {...props}>
      <Skeleton avatar title={false} loading={showSkeleton} active>
        <Row gutter={12} className="w-full">
          <Col span={17} className="align-middle">
            <List.Item.Meta
              avatar={
                <Avatar
                  src={iconUrl}
                  size={30}
                  icon={<Icons.Wikis size={30} />}
                  style={{
                    backgroundColor: "transparent",
                    color: "var(--ant-color-text)",
                  }}
                  alt={`${property} icon`}
                />
              }
              title={
                <Flex align="center" gap={4}>
                  <NextLink
                    href={`${ACTION_CENTER_ROUTE}/${key}`}
                    className="whitespace-nowrap"
                  >
                    {`${totalUpdates} assets detected${property ? ` on ${property}` : ""}`}
                  </NextLink>
                  <DiscoveryStatusIcon consentStatus={consentStatus} />
                </Flex>
              }
              description={`${assetCountString} detected.`}
            />
          </Col>
          <Col span={4} className="flex items-center justify-end">
            <Text ellipsis={{ tooltip: name }}>{name}</Text>
          </Col>
          <Col span={3} className="flex items-center justify-end">
            {!!lastMonitoredDistance && (
              <Tooltip title={formattedLastMonitored}>
                <Text
                  data-testid="monitor-date"
                  ellipsis={{ tooltip: formattedLastMonitored }}
                >
                  {lastMonitoredDistance} ago
                </Text>
              </Tooltip>
            )}
          </Col>
        </Row>
      </Skeleton>
    </List.Item>
  );
};
