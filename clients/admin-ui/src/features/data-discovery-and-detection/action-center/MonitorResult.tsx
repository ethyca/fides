import { formatDistanceStrict } from "date-fns";
import {
  AntButton as Button,
  AntCol as Col,
  AntDivider as Divider,
  AntFlex as Flex,
  AntList as List,
  AntListItemProps as ListItemProps,
  AntRow as Row,
  AntSpace as Space,
  AntTag as Tag,
  AntTooltip as Tooltip,
  AntTypography as Typography,
  ExpandCollapse,
  OpenCloseArrow,
  SparkleIcon,
} from "fidesui";
import NextLink from "next/link";
import { useState } from "react";

import { useFeatures } from "~/features/common/features";
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
  href: string;
}

export const MonitorResult = ({
  monitorSummary,
  href,
  ...props
}: MonitorResultProps) => {
  const { flags } = useFeatures();
  const { heliosV2: heliosV2Enabled } = flags;
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

  let confidenceCounts;
  if (monitorType === MONITOR_TYPES.DATASTORE) {
    const datastoreUpdates = updates as DatastoreMonitorUpdates | undefined;
    confidenceCounts = {
      highConfidenceCount: datastoreUpdates?.classified_high_confidence ?? 0,
      mediumConfidenceCount:
        datastoreUpdates?.classified_medium_confidence ?? 0,
      lowConfidenceCount: datastoreUpdates?.classified_low_confidence ?? 0,
    };
  }
  const [isConfidenceRowExpanded, setIsConfidenceRowExpanded] = useState(false);

  const hasConfidenceCounts =
    !!confidenceCounts &&
    (confidenceCounts.highConfidenceCount > 0 ||
      confidenceCounts.mediumConfidenceCount > 0 ||
      confidenceCounts.lowConfidenceCount > 0);

  const showConfidenceRow =
    monitorType === MONITOR_TYPES.DATASTORE && hasConfidenceCounts && !!key;

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
      <Flex vertical className="grow">
        <Row gutter={{ xs: 6, lg: 12 }} className="items-center">
          <Col span={heliosV2Enabled ? 14 : 17}>
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
          <Col span={5} className="flex justify-end">
            {!!lastMonitoredDistance && (
              <Tooltip title={formattedLastMonitored}>
                <Text type="secondary" data-testid="monitor-date">
                  <span className="hidden lg:inline">Last scan: </span>
                  {lastMonitoredDistance}
                </Text>
              </Tooltip>
            )}
          </Col>
          <Col
            span={heliosV2Enabled ? 5 : 2}
            className="flex items-center justify-end"
          >
            {heliosV2Enabled && showConfidenceRow && (
              <>
                <Button
                  type="link"
                  className="p-0"
                  icon={<OpenCloseArrow isOpen={isConfidenceRowExpanded} />}
                  iconPosition="end"
                  onClick={() =>
                    setIsConfidenceRowExpanded(!isConfidenceRowExpanded)
                  }
                  aria-haspopup="true"
                  aria-expanded={isConfidenceRowExpanded}
                  aria-controls={`confidence-row-${key}`}
                  aria-label={`${isConfidenceRowExpanded ? "Collapse" : "Expand"} findings`}
                >
                  <Space>
                    <SparkleIcon />
                    Findings
                  </Space>
                </Button>
                <Divider type="vertical" orientationMargin={0} />
              </>
            )}
            <NextLink key="review" href={href} passHref legacyBehavior>
              <Button
                type="link"
                className="p-0"
                data-testid={`review-button-${monitorSummary.key}`}
              >
                Review
              </Button>
            </NextLink>
          </Col>
        </Row>
        {heliosV2Enabled && showConfidenceRow && confidenceCounts && (
          <ExpandCollapse
            isExpanded={isConfidenceRowExpanded}
            motionKey={`confidence-row-${key}`}
          >
            <ConfidenceRow
              confidenceCounts={confidenceCounts}
              reviewHref={href}
              monitorId={key}
              className="mt-6"
              id={`confidence-row-${key}`}
            />
          </ExpandCollapse>
        )}
      </Flex>
    </List.Item>
  );
};
