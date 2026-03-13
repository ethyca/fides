import { Col, Flex, Row } from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";

import {
  useGetActivityFeedQuery,
  useGetAgentBriefingQuery,
  useGetAstralisQuery,
  useGetDashboardPostureQuery,
  useGetDashboardTrendsQuery,
} from "~/features/dashboard/dashboard.slice";

import ActivityFeedCard from "./ActivityFeedCard";
import AgentBriefingBanner from "./AgentBriefingBanner";
import AstralisCard from "./AstralisCard";
import PostureCard from "./PostureCard";
import { PriorityActionsCard } from "./PriorityActionsCard";
import TrendCard from "./TrendCard";

const HomeDashboard = () => {
  const router = useRouter();
  const [showBriefing, setShowBriefing] = useState(true);

  const { data: posture } = useGetDashboardPostureQuery();
  const { data: briefing } = useGetAgentBriefingQuery();
  const { data: trends } = useGetDashboardTrendsQuery({ period: "30d" });
  const { data: astralis } = useGetAstralisQuery();
  const { data: activityFeed } = useGetActivityFeedQuery();

  const metrics = trends?.metrics;

  return (
    <Flex vertical gap={24} className="px-10 py-6">
      {briefing && showBriefing && (
        <AgentBriefingBanner
          briefing={briefing.briefing}
          onClose={() => setShowBriefing(false)}
          onViewActions={() => router.push("/steward")}
        />
      )}

      <Row gutter={24}>
        <Col xs={24} md={8} lg={8} xxl={8}>
          <PostureCard posture={posture} />
        </Col>
        <Col xs={24} md={16} lg={16} xxl={16}>
          <PriorityActionsCard />
        </Col>
      </Row>

      <Row gutter={24}>
        <Col xs={24} sm={12} md={6}>
          <TrendCard
            title="Data sharing"
            metric={metrics?.data_sharing}
            format="percentage"
          />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <TrendCard
            title="Active users"
            metric={metrics?.active_users}
            format="percentage"
          />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <TrendCard title="Total requests" metric={metrics?.total_requests} />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <TrendCard
            title="Consent rate"
            metric={metrics?.consent_rate}
            format="percentage"
          />
        </Col>
      </Row>

      <Row gutter={24}>
        <Col xs={24} md={17}>
          <ActivityFeedCard activityFeed={activityFeed} />
        </Col>
        <Col xs={24} md={7}>
          <AstralisCard astralis={astralis} />
        </Col>
      </Row>
    </Flex>
  );
};

export default HomeDashboard;
