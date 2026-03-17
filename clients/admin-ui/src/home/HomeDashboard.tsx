import { Col, Flex, Row } from "fidesui";

import { PostureCard } from "./PostureCard";
import { PriorityActionsCard } from "./PriorityActionsCard";

export const HomeDashboard = () => (
  <Flex vertical gap={24} className="px-10 py-6">
    <Row
      gutter={24}
      className="h-[420px] items-stretch lg:h-[500px] xl:h-[650px]"
    >
      <Col xs={24} md={8} lg={8} xxl={8} className="h-full">
        <PostureCard />
      </Col>
      <Col xs={24} md={16} lg={16} xxl={16} className="h-full">
        <PriorityActionsCard />
      </Col>
    </Row>
  </Flex>
);
