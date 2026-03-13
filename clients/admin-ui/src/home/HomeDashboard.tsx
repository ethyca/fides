import { Col, Flex, Row } from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";

import {
  useGetActivityFeedQuery,
  useGetAgentBriefingQuery,
  useGetAstralisQuery,
  useGetDashboardPostureQuery,
  useGetDashboardTrendsQuery,
  useGetPriorityActionsQuery,
} from "~/features/dashboard/dashboard.slice";

import ActivityFeedCard from "./ActivityFeedCard";
import AgentBriefingBanner from "./AgentBriefingBanner";
import AstralisCard from "./AstralisCard";
import PostureCard from "./PostureCard";
import PriorityActionsCard from "./PriorityActionsCard";
import TrendCards from "./TrendCards";

const HomeDashboard = () => {
  const router = useRouter();
  const [showBriefing, setShowBriefing] = useState(true);

  const { data: posture } = useGetDashboardPostureQuery();
  const { data: briefing } = useGetAgentBriefingQuery();
  const { data: trends } = useGetDashboardTrendsQuery({ period: "30d" });
  const { data: astralis } = useGetAstralisQuery();
  const { data: priorityActions, isLoading: actionsLoading } =
    useGetPriorityActionsQuery();
  const { data: activityFeed } = useGetActivityFeedQuery();

  const metrics = trends?.metrics ? Object.values(trends.metrics) : [];

  return (
    <Flex vertical gap={24} className="px-10 pb-6 pt-6">
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
          <PriorityActionsCard
            actions={priorityActions}
            loading={actionsLoading}
          />
        </Col>
      </Row>

      <TrendCards metrics={metrics} />

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
