import { Col, Flex, Row } from "fidesui";
import { useState } from "react";

import { useGetAgentBriefingQuery } from "~/features/dashboard/dashboard.slice";

import { AgentBriefingBanner } from "./AgentBriefingBanner";
import { DashboardDrawer } from "./DashboardDrawer";
import { PostureCard } from "./PostureCard";
import { PriorityActionsCard } from "./PriorityActionsCard";

export const HomeDashboard = () => {
  const [showBriefing, setShowBriefing] = useState(true);

  const { data: briefing } = useGetAgentBriefingQuery();

  return (
    <Flex vertical gap={24} className="px-10 py-6">
      {briefing && showBriefing && (
        <AgentBriefingBanner
          briefing={briefing.briefing}
          quickActions={briefing.quick_actions}
          onClose={() => setShowBriefing(false)}
        />
      )}
      <Row
        gutter={24}
        className="h-[350px] items-stretch lg:h-[400px] xl:h-[500px]"
      >
        <Col xs={24} md={8} lg={8} xxl={8} className="h-full">
          <PostureCard />
        </Col>
        <Col xs={24} md={16} lg={16} xxl={16} className="h-full">
          <PriorityActionsCard />
        </Col>
      </Row>
      <DashboardDrawer />
    </Flex>
  );
};
