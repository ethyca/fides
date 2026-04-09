import { Col, Divider, Flex, Row } from "fidesui";

import { useGetDashboardTrendsQuery } from "~/features/dashboard/dashboard.slice";
import { TrendPeriod } from "~/features/dashboard/types";

import { ActivityFeedCard } from "./ActivityFeedCard";
import { AgentBriefingBanner } from "./AgentBriefingBanner";
import { AstralisPanel } from "./AstralisPanel";
import { DashboardDrawer } from "./DashboardDrawer";
import { DSRStatusCard } from "./DSRStatusCard";
import { PostureRadar, PostureScore } from "./PostureCard";
import { PriorityActionsCard } from "./PriorityActionsCard";
import { SystemCoverageCard } from "./SystemCoverageCard";
import { TREND_METRIC_KEYS, TrendCard } from "./TrendCard";

const TREND_GUTTER = 16;

export const HomeDashboard = () => {
  const { data: trends, isLoading: isTrendsLoading } =
    useGetDashboardTrendsQuery({
      period: TrendPeriod.THIRTY_DAYS,
    });

  const metrics = trends?.metrics;

  return (
    <Flex vertical className="mx-auto w-full max-w-[1600px] px-10">
      <div className="pt-10">
        <AgentBriefingBanner />
      </div>
      <Row gutter={48} className="min-h-[80vh] items-center pb-16 pl-16">
        <Col xs={24} md={12}>
          <PostureScore />
        </Col>
        <Col xs={24} md={12}>
          <PostureRadar />
        </Col>
      </Row>
      <Divider />
      <div className="py-9">
        <PriorityActionsCard />
      </div>
      <Divider />

      <Row gutter={TREND_GUTTER} className="py-8">
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
      <Divider />

      <Row gutter={20} className="py-10">
        <Col xs={24} md={7}>
          <SystemCoverageCard />
        </Col>
        <Col md={1} className="flex justify-center">
          <Divider vertical className="h-full" />
        </Col>
        <Col xs={24} md={16}>
          <DSRStatusCard />
        </Col>
      </Row>
      <Row gutter={20} className="h-[400px] items-stretch">
        <Col xs={24} md={16} className="h-full">
          <ActivityFeedCard />
        </Col>
        <Col xs={24} md={8} className="h-full">
          <AstralisPanel />
        </Col>
      </Row>
      <DashboardDrawer />
    </Flex>
  );
};
