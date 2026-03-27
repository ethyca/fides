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
      {/* Tier 1: Hero — Score + Radar centered vertically, agent card absolute under score */}
      <Row
        gutter={48}
        className="relative min-h-[80vh] items-center pb-16 pt-14 pl-16"
      >
        <Col xs={24} md={12}>
          <PostureScore></PostureScore>
          <div className="absolute left-0 right-0 pr-6">
            <AgentBriefingBanner />
          </div>
        </Col>
        <Col xs={24} md={12}>
          <PostureRadar />
        </Col>
      </Row>
      {/* Tier 2: Priority Actions — full width, capped list */}
      <div className="py-9">
        <PriorityActionsCard />
      </div>
      <Divider className="!my-0" />

      {/* Tier 3: Dimension Trend Cards */}
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
      <Divider className="!my-0" />

      {/* Tier 4: System Coverage (narrow) + DSR Status (wide) */}
      <Row gutter={0} className="py-10">
        <Col
          xs={24}
          md={7}
          className="border-r border-solid border-neutral-100 pr-10"
        >
          <SystemCoverageCard />
        </Col>
        <Col xs={24} md={17} className="pl-10">
          <DSRStatusCard />
        </Col>
      </Row>

      <DashboardDrawer />
    </Flex>
  );
};
