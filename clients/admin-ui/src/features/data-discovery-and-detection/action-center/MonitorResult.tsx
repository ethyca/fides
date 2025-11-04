import { formatDistanceStrict } from "date-fns";
import {
  AntCol as Col,
  AntFlex as Flex,
  AntList as List,
  AntListItemProps as ListItemProps,
  AntRow as Row,
  AntSkeleton as Skeleton,
  AntTag as Tag,
  AntTooltip as Tooltip,
  AntTypography as Typography,
} from "fidesui";
import NextLink from "next/link";

import { formatDate, nFormatter } from "~/features/common/utils";
import ConnectionTypeLogo, {
  ConnectionLogoKind,
} from "~/features/datastore-connections/ConnectionTypeLogo";

import { DiscoveryStatusIcon } from "./DiscoveryStatusIcon";
import styles from "./MonitorResult.module.scss";
import { MonitorResultDescription } from "./MonitorResultDescription";
import { MonitorAggregatedResults } from "./types";
import { MONITOR_TYPES } from "./utils/getMonitorType";

const { Text } = Typography;

const MONITOR_RESULT_COUNT_TYPES = {
  [MONITOR_TYPES.WEBSITE]: "asset",
  [MONITOR_TYPES.DATASTORE]: "field",
  [MONITOR_TYPES.INFRASTRUCTURE]: "system",
} as const;

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
    saas_config: saasConfig,
    monitorType,
    isTestMonitor,
  } = monitorSummary;

  const formattedLastMonitored = lastMonitored
    ? formatDate(new Date(lastMonitored))
    : undefined;

  const lastMonitoredDistance = lastMonitored
    ? formatDistanceStrict(new Date(lastMonitored), new Date(), {
        addSuffix: true,
      })
    : undefined;

  const monitorResultCountType = MONITOR_RESULT_COUNT_TYPES[monitorType];

  return (
    <List.Item data-testid={`monitor-result-${key}`} {...props}>
      <Skeleton avatar title={false} loading={showSkeleton} active>
        <Row gutter={{ xs: 6, lg: 12 }} className="w-full">
          <Col span={18} className="align-middle">
            <List.Item.Meta
              avatar={
                <ConnectionTypeLogo
                  data={{
                    kind: ConnectionLogoKind.CONNECTION,
                    connectionType,
                    name,
                    key,
                    saasType: saasConfig?.type,
                    websiteUrl: secrets?.url,
                  }}
                />
              }
              title={
                <Flex
                  align="center"
                  gap={4}
                  className={styles["monitor-result__title"]}
                >
                  <NextLink href={href} data-testid="monitor-link">
                    {name}
                  </NextLink>
                  <Text type="secondary">
                    {nFormatter(totalUpdates)} {monitorResultCountType}
                    {totalUpdates === 1 ? "" : "s"}
                  </Text>
                  {consentStatus && (
                    <DiscoveryStatusIcon consentStatus={consentStatus} />
                  )}
                  {isTestMonitor && <Tag color="nectar">test monitor</Tag>}
                </Flex>
              }
              description={
                !!updates && (
                  <MonitorResultDescription
                    updates={updates}
                    isAssetList={monitorType === MONITOR_TYPES.WEBSITE}
                  />
                )
              }
            />
          </Col>
          <Col span={6} className="flex items-center justify-end">
            {!!lastMonitoredDistance && (
              <Tooltip title={formattedLastMonitored}>
                <Text type="secondary" data-testid="monitor-date">
                  <span className="hidden lg:inline">Last scan: </span>
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
