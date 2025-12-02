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

import { formatDate, nFormatter, pluralize } from "~/features/common/utils";
import ConnectionTypeLogo, {
  ConnectionLogoKind,
} from "~/features/datastore-connections/ConnectionTypeLogo";
import { DatastoreMonitorUpdates } from "~/types/api/models/DatastoreMonitorUpdates";

import { ConfidenceRow } from "./ConfidenceRow";
import { DiscoveryStatusIcon } from "./DiscoveryStatusIcon";
import styles from "./MonitorResult.module.scss";
import { MonitorResultDescription } from "./MonitorResultDescription";
import { MonitorAggregatedResults } from "./types";
import { MONITOR_TYPES } from "./utils/getMonitorType";

const { Text } = Typography;

const MONITOR_RESULT_COUNT_TYPES = {
  [MONITOR_TYPES.WEBSITE]: ["asset", "assets"],
  [MONITOR_TYPES.DATASTORE]: ["field", "fields"],
  [MONITOR_TYPES.INFRASTRUCTURE]: ["system", "systems"],
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
  actions,
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

  const monitorResultCountType = pluralize(
    totalUpdates ?? 0,
    MONITOR_RESULT_COUNT_TYPES[monitorType][0],
    MONITOR_RESULT_COUNT_TYPES[monitorType][1],
  );

  return (
    <List.Item data-testid={`monitor-result-${key}`} {...props}>
      <Skeleton avatar title={false} loading={showSkeleton} active>
        <Flex vertical gap="large" className="grow">
          <Row gutter={{ xs: 6, lg: 12 }} className="items-center">
            <Col span={16}>
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
                      {nFormatter(totalUpdates ?? 0)} {monitorResultCountType}
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
            <Col span={6} className="flex justify-end">
              {!!lastMonitoredDistance && (
                <Tooltip title={formattedLastMonitored}>
                  <Text type="secondary" data-testid="monitor-date">
                    <span className="hidden lg:inline">Last scan: </span>
                    {lastMonitoredDistance}
                  </Text>
                </Tooltip>
              )}
            </Col>
            <Col span={2} className="flex justify-end">
              {actions}
            </Col>
          </Row>
          {monitorType === MONITOR_TYPES.DATASTORE && !!updates && !!key && (
            <ConfidenceRow
              highConfidenceCount={
                (updates as DatastoreMonitorUpdates)
                  .classified_high_confidence ?? 0
              }
              mediumConfidenceCount={
                (updates as DatastoreMonitorUpdates)
                  .classified_medium_confidence ?? 0
              }
              lowConfidenceCount={
                (updates as DatastoreMonitorUpdates)
                  .classified_low_confidence ?? 0
              }
              reviewHref={href}
              monitorId={key}
            />
          )}
        </Flex>
      </Skeleton>
    </List.Item>
  );
};
