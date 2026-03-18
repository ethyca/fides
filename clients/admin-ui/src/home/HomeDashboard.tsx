import { Col, Flex, Row } from "fidesui";

import { DashboardDrawer } from "./DashboardDrawer";
import { DSRStatusCard } from "./DSRStatusCard";
import { PostureCard } from "./PostureCard";
import { PriorityActionsCard } from "./PriorityActionsCard";
import { SystemCoverageCard } from "./SystemCoverageCard";

export const HomeDashboard = () => (
  <Flex vertical gap={24} className="px-10 py-6">
    <Row gutter={24} className="h-[400px] items-stretch lg:h-[500px]">
      <Col xs={24} md={8} lg={8} xxl={8} className="h-full">
        <PostureCard />
      </Col>
      <Col xs={24} md={16} lg={16} xxl={16} className="h-full">
        <PriorityActionsCard />
      </Col>
    </Row>
    <Row gutter={24}>
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
