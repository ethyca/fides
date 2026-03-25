import { Col, Flex, Row } from "fidesui";
import { useCallback, useEffect, useState } from "react";

import {
  useGetAgentBriefingQuery,
  useGetDashboardTrendsQuery,
} from "~/features/dashboard/dashboard.slice";
import { TrendPeriod } from "~/features/dashboard/types";

import { AgentBriefingBanner } from "./AgentBriefingBanner";
import { DashboardDrawer } from "./DashboardDrawer";
import { DSRStatusCard } from "./DSRStatusCard";
import { PostureCard } from "./PostureCard";
import { PriorityActionsCard } from "./PriorityActionsCard";
import { SystemCoverageCard } from "./SystemCoverageCard";
import { TREND_METRIC_KEYS, TrendCard } from "./TrendCard";

const BRIEFING_DISMISSED_KEY = "dashboard_briefing_dismissed";
const ROW_GUTTER = 24;

export const HomeDashboard = () => {
  const [showBriefing, setShowBriefing] = useState(true);

  useEffect(() => {
    if (sessionStorage.getItem(BRIEFING_DISMISSED_KEY) === "true") {
      setShowBriefing(false);
    }
  }, []);

  const { data: briefing } = useGetAgentBriefingQuery();
  const { data: trends, isLoading: isTrendsLoading } =
    useGetDashboardTrendsQuery({
      period: TrendPeriod.THIRTY_DAYS,
    });

  const metrics = trends?.metrics;

  const dismissBriefing = useCallback(() => {
    setShowBriefing(false);
    sessionStorage.setItem(BRIEFING_DISMISSED_KEY, "true");
  }, []);

  return (
    <Flex vertical gap={24} className="mx-auto w-full max-w-[1600px] py-6">
      {briefing && showBriefing && (
        <AgentBriefingBanner
          briefing={briefing.briefing}
          quickActions={briefing.quick_actions}
          onClose={dismissBriefing}
        />
      )}
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
      <DashboardDrawer />
    </Flex>
  );
};
