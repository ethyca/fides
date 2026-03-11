import { Col, Flex, Row } from "fidesui";

import { PostureCard } from "./PostureCard";
import { PriorityActionsCard } from "./PriorityActionsCard";

const HomeDashboard = () => (
  <Flex vertical gap={24} className="px-10 py-6">
    <Row gutter={24}>
      <Col xs={24} md={8} lg={8} xxl={8}>
        <PostureCard />
      </Col>
      <Col xs={24} md={16} lg={16} xxl={16}>
        <PriorityActionsCard />
      </Col>
    </Row>
  </Flex>
);

export default HomeDashboard;
