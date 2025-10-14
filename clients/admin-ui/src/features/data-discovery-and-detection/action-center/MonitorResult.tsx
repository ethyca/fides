import { formatDistanceStrict } from "date-fns";
import {
  AntAvatar as Avatar,
  AntCol as Col,
  AntFlex as Flex,
  AntList as List,
  AntListItemProps as ListItemProps,
  AntRow as Row,
  AntSkeleton as Skeleton,
  AntTag as Tag,
  AntTypography as Typography,
  Icons,
} from "fidesui";
import NextLink from "next/link";
import { useMemo } from "react";

import {
  formatDate,
  getDomain,
  getWebsiteIconUrl,
  nFormatter,
} from "~/features/common/utils";
import { ConnectionType } from "~/types/api";

import { DiscoveryStatusIcon } from "./DiscoveryStatusIcon";
import styles from "./MonitorResult.module.scss";
import { MonitorResultDescription } from "./MonitorResultDescription";
import { MonitorAggregatedResults } from "./types";

const { Text } = Typography;

interface MonitorResultProps extends ListItemProps {
  monitorSummary: MonitorAggregatedResults;
  showSkeleton?: boolean;
  href: string;
}

export const MonitorResult = ({
  monitorSummary,
  showSkeleton,
  href,
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
    connection_type: connectionType,
  } = monitorSummary;

  const isWebMonitor =
    connectionType === ConnectionType.TEST_WEBSITE ||
    connectionType === ConnectionType.WEBSITE;

  const property = useMemo(() => {
    return secrets?.url ? getDomain(secrets.url) : undefined;
  }, [secrets?.url]);

  const iconUrl = useMemo(() => {
    return property ? getWebsiteIconUrl(property, 60) : undefined;
  }, [property]);

  const formattedLastMonitored = lastMonitored
    ? formatDate(new Date(lastMonitored))
    : undefined;

  const lastMonitoredDistance = lastMonitored
    ? formatDistanceStrict(new Date(lastMonitored), new Date(), {
        addSuffix: true,
      })
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
                  alt={property ? `${property} icon` : "Monitor icon"}
                />
              }
              title={
                <Flex
                  align="center"
                  gap={4}
                  className={styles["monitor-result__title"]}
                >
                  {isWebMonitor ? (
                    <>
                      <NextLink
                        href={href}
                      >{`${totalUpdates} assets detected${property ? ` on ${property}` : ""}`}</NextLink>
                      <DiscoveryStatusIcon consentStatus={consentStatus} />
                      {connectionType === ConnectionType.TEST_WEBSITE && (
                        <Tag color="nectar">test monitor</Tag>
                      )}
                    </>
                  ) : (
                    <>
                      <NextLink href={href}>{name}</NextLink>
                      <Text type="secondary">
                        {nFormatter(totalUpdates)}{" "}
                        {totalUpdates === 1 ? "field" : "fields"}
                      </Text>
                    </>
                  )}
                </Flex>
              }
              description={
                <MonitorResultDescription
                  updates={updates}
                  monitorType={connectionType}
                />
              }
            />
          </Col>
          <Col span={4} className="flex items-center justify-end">
            {isWebMonitor && <Text ellipsis={{ tooltip: name }}>{name}</Text>}
          </Col>
          <Col span={3} className="flex items-center justify-end">
            {!!lastMonitoredDistance && (
              <Text
                data-testid="monitor-date"
                ellipsis={{ tooltip: formattedLastMonitored }}
              >
                {lastMonitoredDistance}
              </Text>
            )}
          </Col>
        </Row>
      </Skeleton>
    </List.Item>
  );
};
