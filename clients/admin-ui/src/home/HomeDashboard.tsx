import { Col, Divider, Flex, Row, Text } from "fidesui";

import { useFlags } from "~/features/common/features";
import { ThemeModeToggle } from "~/features/common/ThemeModeToggle";
import { useGetDashboardTrendsQuery } from "~/features/dashboard/dashboard.slice";
import { TrendPeriod } from "~/features/dashboard/types";

import { ActivityFeedCard } from "./ActivityFeedCard";
import { AgentBriefingBanner } from "./AgentBriefingBanner";
import { AstralisPanel } from "./AstralisPanel";
import { DashboardDrawer } from "./DashboardDrawer";
import { DSRStatusCard } from "./DSRStatusCard";
import { PostureCard } from "./PostureCard";
import { PriorityActionsCard } from "./PriorityActionsCard";
import { SystemCoverageCard } from "./SystemCoverageCard";
import { TREND_METRIC_KEYS, TrendCard } from "./TrendCard";

const ROW_GUTTER = 24;

export const HomeDashboard = () => {
  const {
    flags: {
      alphaDarkMode,
      alphaDashboardActivityFeed,
      alphaDashboardAstralisCard,
      alphaDashboardAgentBriefing,
    },
  } = useFlags();
  const { data: trends, isLoading: isTrendsLoading } =
    useGetDashboardTrendsQuery({
      period: TrendPeriod.THIRTY_DAYS,
    });

  const metrics = trends?.metrics;

  return (
    <Flex
      vertical
      gap={24}
      className="mx-auto w-full max-w-[1600px] px-10 py-6"
    >
      {alphaDarkMode && (
        <Flex justify="end">
          <ThemeModeToggle />
        </Flex>
      )}
      {alphaDashboardAgentBriefing && <AgentBriefingBanner />}
      <Row gutter={ROW_GUTTER} className="h-[500px] items-stretch">
        <Col xs={24} md={10} className="h-full">
          <PostureCard />
        </Col>
        <Col xs={24} md={14} className="h-full">
          <PriorityActionsCard />
        </Col>
      </Row>
      <Divider titlePlacement="right" dashed className="!mb-0">
        <Text type="secondary" className="text-xs">
          Last 30 days
        </Text>
      </Divider>
      <Row gutter={ROW_GUTTER}>
        {TREND_METRIC_KEYS.map((key) => (
          <Col key={key} xs={24} sm={12} md={6}>
            <TrendCard
              metricKey={key}
              metric={metrics?.[key]}
              isLoading={isTrendsLoading}
            />
          </Col>
        ))}
      </Row>
      <Row gutter={ROW_GUTTER} className="items-stretch">
        <Col xs={24} md={8}>
          <SystemCoverageCard />
        </Col>
        <Col xs={24} md={16}>
          <DSRStatusCard />
        </Col>
      </Row>
      {(alphaDashboardActivityFeed || alphaDashboardAstralisCard) && (
        <Row gutter={ROW_GUTTER} className="h-[400px] items-stretch">
          {alphaDashboardActivityFeed && (
            <Col
              xs={24}
              md={alphaDashboardAstralisCard ? 16 : 24}
              className="h-full"
            >
              <ActivityFeedCard />
            </Col>
          )}
          {alphaDashboardAstralisCard && (
            <Col
              xs={24}
              md={alphaDashboardActivityFeed ? 8 : 24}
              className="h-full"
            >
              <AstralisPanel />
            </Col>
          )}
        </Row>
      )}
      <DashboardDrawer />
    </Flex>
  );
};
