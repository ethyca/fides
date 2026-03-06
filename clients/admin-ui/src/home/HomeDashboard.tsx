import {
  ArrowDownOutlined,
  ArrowUpOutlined,
  RobotOutlined,
  UserOutlined,
} from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Flex,
  Row,
  Skeleton,
  Statistic,
  Tag,
  Typography,
} from "fidesui";
import { RadarChart, Sparkline } from "fidesui";
import * as React from "react";
import { useEffect, useMemo, useState } from "react";

import {
  type PriorityAction,
  type TrendMetric,
  useGetActivityFeedQuery,
  useGetAgentBriefingQuery,
  useGetAstralisQuery,
  useGetDashboardPostureQuery,
  useGetDashboardTrendsQuery,
  useGetPriorityActionsQuery,
  useGetPrivacyRequestsQuery,
  useResetDashboardMutation,
} from "~/features/dashboard/dashboard.slice";

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

const formatTrendValue = (metric: TrendMetric, index: number): string => {
  if (index === 3) {
    return `${(metric.value * 100).toFixed(1)}%`;
  }
  return metric.value.toLocaleString();
};

const formatTrendDiff = (metric: TrendMetric, index: number): string => {
  const abs = Math.abs(metric.diff);
  if (index === 3) {
    return `${(abs * 100).toFixed(1)}%`;
  }
  return abs.toLocaleString();
};

const HomeDashboardMockup = () => {
  const [activeTab, setActiveTab] = useState("act_now");

  const [resetDashboard, { isSuccess: resetDone }] =
    useResetDashboardMutation();

  useEffect(() => {
    resetDashboard();
  }, [resetDashboard]);

  const skip = !resetDone;

  const { data: posture } = useGetDashboardPostureQuery(undefined, { skip });
  const { data: briefing } = useGetAgentBriefingQuery(undefined, { skip });
  const { data: actions, isLoading: actionsLoading } =
    useGetPriorityActionsQuery({ page: 1, size: 8 }, { skip });
  const { data: trends } = useGetDashboardTrendsQuery(
    { period: "30d" },
    { skip },
  );
  const { data: astralis } = useGetAstralisQuery(undefined, { skip });
  const { data: activityFeed } = useGetActivityFeedQuery(undefined, { skip });
  const { data: privacyRequests } = useGetPrivacyRequestsQuery(undefined, {
    skip,
  });

  const radarData = posture?.dimensions.map((d) => ({
    subject: d.label,
    value: d.score,
    status: BAND_STATUS[d.band],
  }));

  const postureScore = posture?.score ?? 0;
  const postureDiff = posture?.diff ?? 0;
  const diffDirection = posture?.diff_direction ?? "unchanged";

  const filteredActions = useMemo(() => {
    if (!actions?.items) return [];
    if (activeTab === "act_now") {
      return actions.items.filter((a: PriorityAction) => a.due_date !== null);
    }
    return actions.items.filter((a: PriorityAction) => a.due_date === null);
  }, [actions, activeTab]);

  const metrics = trends?.metrics ?? [];

  return (
    <Flex vertical gap={24} className="px-10 pb-6 pt-6">
      {/* Agent Briefing banner */}
      {briefing && (
        <Alert
          type="info"
          banner
          showIcon
          message={briefing.briefing}
          description={
            briefing.quick_actions.length > 0 ? (
              <Flex gap={8} className="mt-2">
                {briefing.quick_actions.map((qa) => (
                  <Button key={qa.id} size="small" type="link" href={qa.action_url}>
                    {qa.title}
                  </Button>
                ))}
              </Flex>
            ) : undefined
          }
        />
      )}

      {/* Middle row: Posture + Priority actions */}
      <Row gutter={24}>
        {/* Posture card */}
        <Col xs={24} md={8} lg={8} xxl={5}>
          <Card
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
              <div
                className="aspect-square"
                style={{ marginLeft: -12, marginRight: -12 }}
              >
                <RadarChart data={radarData} />
              </div>
              {posture?.agent_annotation && (
                <Alert type="info" message={posture.agent_annotation} />
              )}
            </>
          </Card>
        </Col>

        {/* Priority actions card with inline tabs */}
        <Col xs={24} md={16} lg={16} xxl={19}>
          <Card
            title="Priority actions"
            variant="borderless"
            className="h-full"
            headerLayout="inline"
            showTitleDivider={false}
            styles={CARD_STYLES}
            tabList={[
              { key: "act_now", label: "Act now" },
              { key: "due_later", label: "Due later" },
            ]}
            activeTabKey={activeTab}
            onTabChange={setActiveTab}
          >
            {actionsLoading ? (
              <Skeleton active />
            ) : filteredActions.length === 0 ? (
              <Flex align="center" justify="center" style={{ minHeight: 200 }}>
                <Empty
                  description={`No ${activeTab === "act_now" ? "urgent" : "upcoming"} actions`}
                />
              </Flex>
            ) : (
              <Flex vertical gap={8}>
                {filteredActions.map((action: PriorityAction) => (
                  <Card key={action.id} size="small" variant="borderless">
                    <Flex justify="space-between" align="start">
                      <div>
                        <Typography.Text strong>
                          {action.title}
                        </Typography.Text>
                        <br />
                        <Typography.Text type="secondary">
                          {action.message}
                        </Typography.Text>
                      </div>
                      <Flex gap={8} align="center">
                        {action.due_date && (
                          <Typography.Text type="secondary" style={SMALL_FONT}>
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

      {/* System Health + DSR Timeline */}
      <Row gutter={24}>
        <Col xs={24} sm={12} md={7}>
          <Card
            variant="borderless"
            title="System Health"
            className="overflow-clip h-full"
            showTitleDivider={false}
            styles={CARD_STYLES}
          >
            {astralis ? (
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Statistic
                    title="Active conversations"
                    value={astralis.active_conversations}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Completed assessments"
                    value={astralis.completed_assessments}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Awaiting response"
                    value={astralis.awaiting_response}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Risks identified"
                    value={astralis.risks_identified}
                  />
                </Col>
              </Row>
            ) : (
              <Skeleton active />
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} md={17}>
          <Card
            variant="borderless"
            title="DSR Timeline"
            className="overflow-clip h-full"
            showTitleDivider={false}
            styles={CARD_STYLES}
          >
            {privacyRequests ? (
              <Flex vertical gap={12}>
                <Statistic
                  title="Month over month"
                  value={`${privacyRequests.diff_month_over_month > 0 ? "+" : ""}${(privacyRequests.diff_month_over_month * 100).toFixed(1)}%`}
                  trend={
                    privacyRequests.diff_month_over_month > 0 ? "up" : "down"
                  }
                />
                <Flex vertical gap={4}>
                  {privacyRequests.regions.map((region) => (
                    <Flex key={region.name} justify="space-between">
                      <Typography.Text>{region.name}</Typography.Text>
                      <Flex gap={16}>
                        <Typography.Text type="secondary">
                          Access: {region.access_count.toLocaleString()}
                        </Typography.Text>
                        <Typography.Text type="secondary">
                          Erasure: {region.erasure_count.toLocaleString()}
                        </Typography.Text>
                      </Flex>
                    </Flex>
                  ))}
                </Flex>
              </Flex>
            ) : (
              <Skeleton active />
            )}
          </Card>
        </Col>
      </Row>

      {/* Activity Feed */}
      <Row gutter={24}>
        <Col span={24}>
          <Card
            variant="borderless"
            title="Activity Feed"
            className="overflow-clip"
            showTitleDivider={false}
            styles={CARD_STYLES}
          >
            {activityFeed?.items ? (
              <Flex vertical gap={8}>
                {activityFeed.items.map((item, idx) => (
                  <Flex key={idx} gap={12} align="start">
                    {item.actor_type === "agent" ? (
                      <RobotOutlined />
                    ) : (
                      <UserOutlined />
                    )}
                    <div>
                      <Typography.Text>{item.message}</Typography.Text>
                      <br />
                      <Typography.Text type="secondary" style={SMALL_FONT}>
                        {new Date(item.timestamp).toLocaleString()}
                      </Typography.Text>
                    </div>
                  </Flex>
                ))}
                {activityFeed.items.length === 0 && (
                  <Empty description="No recent activity" />
                )}
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
