import { ArrowDownOutlined, ArrowUpOutlined } from "@ant-design/icons";
import classNames from "classnames";
import { formatDistanceStrict } from "date-fns";
import {
  Alert,
  Badge,
  Button,
  Card,
  Col,
  Divider,
  Empty,
  Flex,
  Row,
  Skeleton,
  Statistic,
  Tag,
  Typography,
} from "fidesui";
import { RadarChart, Sparkline } from "fidesui";
import { useRouter } from "next/router";
import * as React from "react";
import { useMemo, useState, useEffect } from "react";

import { SparkleIcon } from "~/features/common/Icon/SparkleIcon";
import { nFormatter } from "~/features/common/utils";
import {
  type PriorityAction,
  type TrendMetric,
  useGetAgentBriefingQuery,
  useGetAstralisQuery,
  useGetDashboardPostureQuery,
  useGetDashboardTrendsQuery,
  useResetDashboardMutation,
} from "~/features/dashboard/dashboard.slice";

import styles from "./HomeDashboard.module.scss";

const now = new Date();
const hoursAgo = (h: number) =>
  new Date(now.getTime() - h * 3600_000).toISOString();

const MOCK_ACTIVITY_FEED = {
  items: [
    {
      actor_type: "agent" as const,
      message: "completed PIA for the new Marketing Analytics platform",
      timestamp: hoursAgo(0.5),
    },
    {
      actor_type: "user" as const,
      message: "approved data mapping for CRM system",
      timestamp: hoursAgo(1),
    },
    {
      actor_type: "agent" as const,
      message: "flagged consent anomaly in EU region — opt-in rate dropped 12%",
      timestamp: hoursAgo(2),
    },
    {
      actor_type: "user" as const,
      message: "resolved DSR #4821 (erasure request)",
      timestamp: hoursAgo(3),
    },
    {
      actor_type: "agent" as const,
      message: "auto-classified 38 new data fields in Warehouse schema",
      timestamp: hoursAgo(5),
    },
    {
      actor_type: "user" as const,
      message: "updated retention policy for HR records",
      timestamp: hoursAgo(8),
    },
    {
      actor_type: "agent" as const,
      message: "identified 3 systems sharing data without a legal basis",
      timestamp: hoursAgo(14),
    },
    {
      actor_type: "user" as const,
      message: "assigned steward role to J. Martinez for Finance dept",
      timestamp: hoursAgo(22),
    },
    {
      actor_type: "agent" as const,
      message: "generated monthly compliance summary report",
      timestamp: hoursAgo(36),
    },
    {
      actor_type: "user" as const,
      message: "added new vendor Snowflake to system registry",
      timestamp: hoursAgo(48),
    },
  ],
  total: 10,
  page: 1,
  size: 10,
  pages: 1,
};

const MOCK_PRIORITY_ACTIONS = {
  items: [
    {
      id: "pa-1",
      priority: 1,
      title: "Review classification changes",
      message:
        "38 fields auto-classified in Warehouse — 4 flagged as sensitive",
      agent_summary: "",
      due_date: hoursAgo(-24),
      action: "classification_review" as const,
      action_data: {},
      status: "pending" as const,
    },
    {
      id: "pa-2",
      priority: 2,
      title: "Consent anomaly in EU",
      message: "Opt-in rate for cookie consent dropped 12% week-over-week",
      agent_summary: "",
      due_date: hoursAgo(-48),
      action: "consent_anomaly" as const,
      action_data: {},
      status: "pending" as const,
    },
    {
      id: "pa-3",
      priority: 3,
      title: "DSR escalation — erasure #4910",
      message: "Erasure request approaching SLA deadline (2 days remaining)",
      agent_summary: "",
      due_date: hoursAgo(-36),
      action: "dsr_action" as const,
      action_data: {},
      status: "in_progress" as const,
    },
    {
      id: "pa-4",
      priority: 4,
      title: "Policy violation detected",
      message:
        "Marketing system sharing email data with 3rd party without legal basis",
      agent_summary: "",
      due_date: hoursAgo(-12),
      action: "policy_violation" as const,
      action_data: {},
      status: "pending" as const,
    },
    {
      id: "pa-5",
      priority: 5,
      title: "Assign steward for new Analytics dept",
      message: "New department created with 12 systems — no steward assigned",
      agent_summary: "",
      due_date: null,
      action: "steward_assignment" as const,
      action_data: {},
      status: "pending" as const,
    },
    {
      id: "pa-6",
      priority: 6,
      title: "PIA update needed for Payment Gateway",
      message: "System configuration changed since last assessment 90 days ago",
      agent_summary: "",
      due_date: null,
      action: "pia_update" as const,
      action_data: {},
      status: "pending" as const,
    },
    {
      id: "pa-7",
      priority: 7,
      title: "System review — new vendor Snowflake",
      message: "Newly registered system needs data flow and risk review",
      agent_summary: "",
      due_date: null,
      action: "system_review" as const,
      action_data: {},
      status: "pending" as const,
    },
    {
      id: "pa-8",
      priority: 8,
      title: "Review DSR automation rules",
      message:
        "Agent suggests updating auto-approval rules based on recent patterns",
      agent_summary: "",
      due_date: null,
      action: "dsr_action" as const,
      action_data: {},
      status: "pending" as const,
    },
  ],
  total: 8,
  page: 1,
  size: 8,
  pages: 1,
};

const SMALL_FONT = { fontSize: 14 };

const CARD_STYLES = {
  title: { color: "var(--ant-color-text-description)" },
  body: { paddingTop: 0 },
};

const BAND_STATUS: Record<string, "warning" | "error" | undefined> = {
  at_risk: "warning",
  critical: "error",
};

const TREND_CARD_TITLES = [
  "Data sharing",
  "Active users",
  "Total requests",
  "Consent rate",
];

const PERCENTAGE_INDICES = new Set([0, 1, 3]);

const formatTrendValue = (metric: TrendMetric, index: number): string => {
  if (PERCENTAGE_INDICES.has(index)) {
    return `${Math.round(metric.value * 100)}%`;
  }
  return nFormatter(metric.value);
};

const formatTrendDiff = (metric: TrendMetric, index: number): string => {
  const abs = Math.abs(metric.diff);
  if (PERCENTAGE_INDICES.has(index)) {
    return `${Math.round(abs * 100)}%`;
  }
  return nFormatter(abs);
};

function getPostureAlertType(score: number): "error" | "warning" | "success" {
  if (score < 40) return "error";
  if (score < 80) return "warning";
  return "success";
}

const HomeDashboardMockup = () => {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("act_now");
  const [showBriefing, setShowBriefing] = useState(true);

  const [resetDashboard, { isSuccess: resetDone }] =
    useResetDashboardMutation();

  useEffect(() => {
    resetDashboard();
  }, [resetDashboard]);

  const skip = !resetDone;
  // const skip = false;

  const { data: posture } = useGetDashboardPostureQuery(undefined, { skip });
  const { data: briefing } = useGetAgentBriefingQuery(undefined, { skip });
  const actions = MOCK_PRIORITY_ACTIONS;
  const actionsLoading = false;
  const { data: trends } = useGetDashboardTrendsQuery(
    { period: "30d" },
    { skip },
  );
  const { data: astralis } = useGetAstralisQuery(undefined, { skip });
  const activityFeed = MOCK_ACTIVITY_FEED;

  const radarData = posture?.dimensions.map((d) => ({
    subject: d.label,
    value: d.score,
    status: BAND_STATUS[d.band],
  }));

  const postureScore = posture?.score ?? 0;
  const postureDiff = posture?.diff_percent ?? 0;
  const diffDirection = posture?.diff_direction ?? "unchanged";

  const filteredActions = useMemo(() => {
    if (!actions?.items) return [];
    if (activeTab === "act_now") {
      return actions.items.filter((a: PriorityAction) => a.due_date !== null);
    }
    return actions.items.filter((a: PriorityAction) => a.due_date === null);
  }, [actions, activeTab]);

  const actNowCount = useMemo(
    () =>
      actions?.items?.filter((a: PriorityAction) => a.due_date !== null)
        .length ?? 0,
    [actions],
  );
  const dueLaterCount = useMemo(
    () =>
      actions?.items?.filter((a: PriorityAction) => a.due_date === null)
        .length ?? 0,
    [actions],
  );

  const metrics = trends?.metrics ? Object.values(trends.metrics) : [];
  console.log("METRICS", metrics);
  return (
    <Flex vertical gap={24} className="px-10 pb-6 pt-6">
      {/* Agent Briefing banner */}
      {briefing && showBriefing && (
        <Alert
          type="info"
          showIcon
          closable
          onClose={() => setShowBriefing(false)}
          message={briefing.briefing}
          action={
            <Button
              size="small"
              type="link"
              onClick={() => router.push("/steward")}
            >
              View actions
            </Button>
          }
          className={styles.alertSm}
        />
      )}

      {/* Middle row: Posture + Priority actions */}
      <Row gutter={24}>
        {/* Posture card */}
        <Col xs={24} md={8} lg={8} xxl={8}>
          <Card
            size="small"
            title="Posture"
            variant="borderless"
            className="h-full"
            showTitleDivider={false}
            styles={CARD_STYLES}
          >
            <>
              <Statistic valueVariant="display" value={postureScore} />
              <Statistic
                trend={diffDirection === "down" ? "down" : "up"}
                value={postureDiff}
                prefix={
                  diffDirection === "down" ? (
                    <ArrowDownOutlined />
                  ) : (
                    <ArrowUpOutlined />
                  )
                }
                valueStyle={SMALL_FONT}
              />
              <div className={classNames(styles.radarChartWrapper)}>
                <RadarChart data={radarData} outerRadius="90%" />
              </div>
              {posture?.agent_annotation && (
                <Alert
                  type={getPostureAlertType(postureScore)}
                  message={posture.agent_annotation}
                  className={styles.alertSm}
                />
              )}
            </>
          </Card>
        </Col>

        {/* Priority actions card with inline tabs */}
        <Col xs={24} md={16} lg={16} xxl={16}>
          <Card
            title="Priority actions"
            variant="borderless"
            className="h-full"
            headerLayout="inline"
            showTitleDivider={false}
            size="small"
            styles={CARD_STYLES}
            tabList={[
              {
                key: "act_now",
                label: (
                  <span>
                    Act now <Tag color="default">{actNowCount}</Tag>
                  </span>
                ),
              },
              {
                key: "due_later",
                label: (
                  <span>
                    Due later <Tag color="default">{dueLaterCount}</Tag>
                  </span>
                ),
              },
            ]}
            activeTabKey={activeTab}
            onTabChange={setActiveTab}
          >
            {actionsLoading ? (
              <Skeleton active />
            ) : filteredActions.length === 0 ? (
              <Flex
                align="center"
                justify="center"
                className={styles.emptyActions}
              >
                <Empty
                  description={`No ${activeTab === "act_now" ? "urgent" : "upcoming"} actions`}
                />
              </Flex>
            ) : (
              <Flex vertical gap={8} className="pt-3">
                {filteredActions.map((action: PriorityAction) => (
                  <Card
                    key={action.id}
                    size="small"
                    variant="borderless"
                    hoverable
                    onClick={() => router.push("/steward")}
                    style={{ cursor: "pointer" }}
                  >
                    <Flex justify="space-between" align="start">
                      <div>
                        <Typography.Text strong>{action.title}</Typography.Text>
                        <br />
                        <Typography.Text type="secondary">
                          {action.message}
                        </Typography.Text>
                      </div>
                      <Flex gap={8} align="center">
                        {action.due_date && (
                          <Typography.Text
                            type="secondary"
                            className={styles.smallFont}
                          >
                            {new Date(action.due_date).toLocaleDateString()}
                          </Typography.Text>
                        )}
                        <Tag>{action.action.replace(/_/g, " ")}</Tag>
                      </Flex>
                    </Flex>
                  </Card>
                ))}
              </Flex>
            )}
          </Card>
        </Col>
      </Row>

      {/* Bottom row: 4 stat cards */}
      <Row gutter={24}>
        {TREND_CARD_TITLES.map((title, i) => {
          const metric = metrics[i];
          return (
            <Col key={title} xs={24} sm={12} md={6}>
              <Card
                size="small"
                variant="borderless"
                title={title}
                className="overflow-clip h-full"
                showTitleDivider={false}
                styles={CARD_STYLES}
                cover={
                  metric?.history ? (
                    <div className="h-16">
                      <Sparkline data={metric.history} />
                    </div>
                  ) : undefined
                }
                coverPosition="bottom"
              >
                {metric ? (
                  <>
                    <Statistic
                      valueVariant="display"
                      value={formatTrendValue(metric, i)}
                    />
                    {metric.diff !== 0 && (
                      <Statistic
                        trend={metric.diff > 0 ? "up" : "down"}
                        value={formatTrendDiff(metric, i)}
                        prefix={
                          metric.diff > 0 ? (
                            <ArrowUpOutlined />
                          ) : (
                            <ArrowDownOutlined />
                          )
                        }
                        valueStyle={SMALL_FONT}
                      />
                    )}
                  </>
                ) : (
                  <Skeleton active paragraph={false} />
                )}
              </Card>
            </Col>
          );
        })}
      </Row>

      {/* Activity Feed + Astralis Agent Panel */}
      <Row gutter={24}>
        <Col xs={24} md={17}>
          <Card
            variant="borderless"
            title="Activity"
            className="overflow-clip h-full"
            showTitleDivider={false}
            styles={CARD_STYLES}
          >
            {activityFeed?.items ? (
              <Flex vertical gap={0} className={styles.activityList}>
                {activityFeed.items.map((item, idx) => {
                  const isAgent = item.actor_type === "agent";
                  const relativeTime = formatDistanceStrict(
                    new Date(item.timestamp),
                    new Date(),
                  )
                    .replace(/ seconds?/, "s")
                    .replace(/ minutes?/, "m")
                    .replace(/ hours?/, "h")
                    .replace(/ days?/, "d")
                    .replace(/ months?/, "mo")
                    .replace(/ years?/, "y");

                  return (
                    <Flex
                      key={idx}
                      align="center"
                      gap={12}
                      className={classNames(styles.activityRow, {
                        [styles.activityRowAgent]: isAgent,
                      })}
                    >
                      {isAgent ? (
                        <SparkleIcon className={styles.sparkleIcon} />
                      ) : (
                        <span className={styles.activityDot} />
                      )}
                      <Typography.Text className={styles.activityMessage}>
                        <Typography.Text
                          strong
                          className={isAgent ? styles.actorAgent : undefined}
                        >
                          {isAgent ? "Astralis" : "User"}
                        </Typography.Text>{" "}
                        {item.message}
                      </Typography.Text>
                      <Typography.Text
                        type="secondary"
                        className={styles.relativeTime}
                      >
                        {relativeTime}
                      </Typography.Text>
                    </Flex>
                  );
                })}
                {activityFeed.items.length === 0 && (
                  <Empty description="No recent activity" />
                )}
              </Flex>
            ) : (
              <Skeleton active />
            )}
          </Card>
        </Col>
        <Col xs={24} md={7}>
          <Card
            variant="borderless"
            className="overflow-clip h-full"
            showTitleDivider={false}
            styles={CARD_STYLES}
            title="Astralis"
          >
            {astralis ? (
              <Flex vertical gap={0}>
                {(
                  [
                    ["PIA active", astralis.active_conversations],
                    ["Auto-approvals", astralis.completed_assessments],
                    ["Risks found", astralis.risks_identified],
                  ] as const
                ).map(([label, value]) => (
                  <Flex
                    key={label}
                    justify="space-between"
                    align="center"
                    className={styles.statRow}
                  >
                    <Typography.Text>{label}</Typography.Text>
                    <Typography.Text strong className={styles.statValue}>
                      {value}
                    </Typography.Text>
                  </Flex>
                ))}
                <Divider className={styles.astralisDivider} />
                <Flex vertical align="center" className={styles.autonomyBox}>
                  <Typography.Text
                    type="secondary"
                    className={styles.autonomyLabel}
                  >
                    AUTONOMY
                  </Typography.Text>
                  <Typography.Text strong className={styles.autonomyValue}>
                    {astralis.active_conversations +
                      astralis.awaiting_response >
                    0
                      ? Math.round(
                          (astralis.completed_assessments /
                            (astralis.completed_assessments +
                              astralis.awaiting_response)) *
                            100,
                        )
                      : 0}
                    <span className={styles.autonomyPercent}>%</span>
                  </Typography.Text>
                  <Typography.Text
                    type="secondary"
                    className={styles.autonomySubtitle}
                  >
                    of actions this month
                  </Typography.Text>
                </Flex>
              </Flex>
            ) : (
              <Skeleton active />
            )}
          </Card>
        </Col>
      </Row>
    </Flex>
  );
};

export default HomeDashboardMockup;
