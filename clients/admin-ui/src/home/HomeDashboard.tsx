import { Col, Flex, Row } from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import {
  useGetAgentBriefingQuery,
  useGetAstralisQuery,
  useGetDashboardPostureQuery,
  useGetDashboardTrendsQuery,
  useResetDashboardMutation,
} from "~/features/dashboard/dashboard.slice";

import ActivityFeedCard from "./ActivityFeedCard";
import AgentBriefingBanner from "./AgentBriefingBanner";
import AstralisCard from "./AstralisCard";
import { MOCK_ACTIVITY_FEED, MOCK_PRIORITY_ACTIONS } from "./mock-data";
import PostureCard from "./PostureCard";
import PriorityActionsCard from "./PriorityActionsCard";
import TrendCards from "./TrendCards";

const HomeDashboard = () => {
  const router = useRouter();
  const [showBriefing, setShowBriefing] = useState(true);

  const [resetDashboard, { isSuccess: resetDone }] =
    useResetDashboardMutation();

  useEffect(() => {
    resetDashboard();
  }, [resetDashboard]);

  const skip = !resetDone;

  const { data: posture } = useGetDashboardPostureQuery(undefined, { skip });
  const { data: briefing } = useGetAgentBriefingQuery(undefined, { skip });
  const { data: trends } = useGetDashboardTrendsQuery(
    { period: "30d" },
    { skip },
  );
  const { data: astralis } = useGetAstralisQuery(undefined, { skip });

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
            actions={MOCK_PRIORITY_ACTIONS}
            loading={false}
          />
        </Col>
      </Row>

      <TrendCards metrics={metrics} />

      <Row gutter={24}>
        <Col xs={24} md={17}>
          <ActivityFeedCard activityFeed={MOCK_ACTIVITY_FEED} />
        </Col>
        <Col xs={24} md={7}>
          <AstralisCard astralis={astralis} />
        </Col>
      </Row>
    </Flex>
  );
};

export default HomeDashboard;
