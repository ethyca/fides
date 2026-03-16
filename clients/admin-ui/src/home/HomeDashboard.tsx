import { Col, Flex, Row } from "fidesui";

import { PostureCard } from "./PostureCard";
import { PriorityActionsCard } from "./PriorityActionsCard";

export const HomeDashboard = () => (
  <Flex vertical gap={24} className="px-10 py-6">
    <Row gutter={24} className="max-h-[500px] items-stretch">
      <Col xs={24} md={8} lg={8} xxl={8} className="max-h-[inherit]">
        <PostureCard />
      </Col>
      <Col xs={24} md={16} lg={16} xxl={16} className="max-h-[inherit]">
        <PriorityActionsCard />
      </Col>
    </Row>
  </Flex>
);

export default HomeDashboard;
