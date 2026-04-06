import { Col, Flex, Row } from "fidesui";

import { useGetDashboardTrendsQuery } from "~/features/dashboard/dashboard.slice";
import { TrendPeriod } from "~/features/dashboard/types";

import { ActivityFeedCard } from "./ActivityFeedCard";
import { AgentBriefingBanner } from "./AgentBriefingBanner";
import { DashboardDrawer } from "./DashboardDrawer";
import { DSRStatusCard } from "./DSRStatusCard";
import { PostureCard } from "./PostureCard";
import { PriorityActionsCard } from "./PriorityActionsCard";
import { SystemCoverageCard } from "./SystemCoverageCard";
import { TREND_METRIC_KEYS, TrendCard } from "./TrendCard";

const ROW_GUTTER = 24;

export const HomeDashboard = () => {
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
      <AgentBriefingBanner />
      <Row
        gutter={ROW_GUTTER}
        className="h-[350px] items-stretch lg:h-[400px] xl:h-[500px]"
      >
        <Col xs={24} md={8} lg={8} xxl={8} className="h-full">
          <PostureCard />
        </Col>
        <Col xs={24} md={16} lg={16} xxl={16} className="h-full">
          <PriorityActionsCard />
        </Col>
      </Row>
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
      <Row gutter={ROW_GUTTER} className="h-[400px] items-stretch">
        <Col xs={24} md={16} className="h-full">
          <ActivityFeedCard />
        </Col>
      </Row>
      <DashboardDrawer />
    </Flex>
  );
};
