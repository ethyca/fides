import { useQuery } from "@apollo/client";
import { Alert, Col, Flex, Row, Spin, Text, Typography } from "fidesui";

import { DashboardOverviewDocument } from "~/__generated__/graphql/graphql";

const { Title } = Typography;

const Section = ({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) => (
  <Flex vertical gap={8} className="rounded border border-gray-200 p-4">
    <Text strong>{title}</Text>
    {children}
  </Flex>
);

const Metric = ({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) => (
  <Flex vertical gap={2}>
    <Text type="secondary" className="text-xs">
      {label}
    </Text>
    <Text className="font-mono text-base">{value}</Text>
  </Flex>
);

export const DashboardGraphqlView = () => {
  const { data, loading, error } = useQuery(DashboardOverviewDocument);

  if (loading && !data) {
    return (
      <Flex justify="center" align="center" className="h-64">
        <Spin tip="Loading dashboard..." />
      </Flex>
    );
  }
  if (error) {
    return <Alert type="error" message={error.message} />;
  }
  if (!data) {
    return null;
  }

  const {
    posture,
    systemCoverage,
    privacyRequests,
    priorityActions,
    astralis,
    agentBriefing,
    trends,
    activityFeed,
  } = data;

  return (
    <Flex
      vertical
      gap={24}
      className="mx-auto w-full max-w-[1600px] px-10 py-6"
    >
      <Title level={3}>Dashboard (GraphQL / Apollo)</Title>

      <Alert
        type="info"
        showIcon
        message={agentBriefing.briefing}
        description={
          agentBriefing.quickActions.length > 0 ? (
            <Text type="secondary">
              {agentBriefing.quickActions.map((qa) => qa.label).join(" · ")}
            </Text>
          ) : null
        }
      />

      <Row gutter={24}>
        <Col xs={24} md={10}>
          <Section title={`Posture: ${posture.band} (${posture.score})`}>
            <Text type="secondary">{posture.agentAnnotation}</Text>
            <Flex vertical gap={4}>
              {posture.dimensions.map((d) => (
                <Flex key={d.dimension} justify="space-between">
                  <Text>{d.label}</Text>
                  <Text className="font-mono">
                    {d.score} · {d.band}
                  </Text>
                </Flex>
              ))}
            </Flex>
          </Section>
        </Col>
        <Col xs={24} md={14}>
          <Section
            title={`Priority actions (${priorityActions.total} total, page ${priorityActions.page}/${priorityActions.pages})`}
          >
            <Flex vertical gap={4}>
              {priorityActions.items.map((a) => (
                <Flex key={a.id} vertical>
                  <Text strong>
                    [{a.severity}] {a.title}
                  </Text>
                  <Text type="secondary">{a.message}</Text>
                </Flex>
              ))}
            </Flex>
          </Section>
        </Col>
      </Row>

      <Row gutter={24}>
        {trends.metrics.map((m) => (
          <Col key={m.key} xs={12} md={6}>
            <Section title={m.key}>
              <Metric label="Value" value={m.value} />
              <Metric label="Δ" value={m.diff} />
            </Section>
          </Col>
        ))}
      </Row>

      <Row gutter={24}>
        <Col xs={24} md={8}>
          <Section title="System coverage">
            <Metric
              label="Coverage %"
              value={systemCoverage.coveragePercentage}
            />
            <Metric label="Total systems" value={systemCoverage.totalSystems} />
            <Metric
              label="Fully classified"
              value={systemCoverage.fullyClassified}
            />
            <Metric
              label="Without steward"
              value={systemCoverage.withoutSteward}
            />
          </Section>
        </Col>
        <Col xs={24} md={8}>
          <Section title="Privacy requests">
            <Metric label="Active" value={privacyRequests.activeCount} />
            <Metric label="Overdue" value={privacyRequests.overdueCount} />
            <Metric
              label="In progress"
              value={privacyRequests.statuses.inProgress}
            />
            <Metric
              label="Pending action"
              value={privacyRequests.statuses.pendingAction}
            />
          </Section>
        </Col>
        <Col xs={24} md={8}>
          <Section title="Astralis">
            <Metric
              label="Active conversations"
              value={astralis.activeConversations}
            />
            <Metric
              label="Completed assessments"
              value={astralis.completedAssessments}
            />
            <Metric
              label="Awaiting response"
              value={astralis.awaitingResponse}
            />
            <Metric label="Risks identified" value={astralis.risksIdentified} />
          </Section>
        </Col>
      </Row>

      <Section
        title={`Activity feed (${activityFeed.total} total, page ${activityFeed.page}/${activityFeed.pages})`}
      >
        <Flex vertical gap={4}>
          {activityFeed.items.map((item) => (
            <Flex
              key={`${item.timestamp}-${item.message}`}
              justify="space-between"
            >
              <Text>{item.message}</Text>
              <Text type="secondary" className="font-mono text-xs">
                {item.actorType} · {item.timestamp}
              </Text>
            </Flex>
          ))}
        </Flex>
      </Section>
    </Flex>
  );
};
