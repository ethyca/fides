import { Col, Flex, Row } from "fidesui";

import {
  useGetDashboardPostureQuery,
  useGetPriorityActionsQuery,
} from "~/features/dashboard/dashboard.slice";

import PostureCard from "./PostureCard";
import PriorityActionsCard from "./PriorityActionsCard";

const HomeDashboard = () => {
  const { data: posture } = useGetDashboardPostureQuery();
  const { data: priorityActions, isLoading: actionsLoading } =
    useGetPriorityActionsQuery();

  return (
    <Flex vertical gap={24} className="px-10 pb-6 pt-6">
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
    </Flex>
  );
};

export default HomeDashboard;
