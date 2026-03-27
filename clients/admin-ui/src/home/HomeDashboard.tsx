import { Col, Divider, Flex, Row } from "fidesui";

import { useGetDashboardTrendsQuery } from "~/features/dashboard/dashboard.slice";
import { TrendPeriod } from "~/features/dashboard/types";

import { AgentBriefingBanner } from "./AgentBriefingBanner";
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
      <Row
        gutter={48}
        className="relative min-h-[80vh] items-center pb-16 pt-14 pl-16"
      >
        <Col xs={24} md={12}>
          <PostureScore />
          <div className="absolute left-0 right-0 pr-6">
            <AgentBriefingBanner />
          </div>
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

      <DashboardDrawer />
    </Flex>
  );
};
