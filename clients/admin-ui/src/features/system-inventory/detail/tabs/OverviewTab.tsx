import { Col, Flex, Row } from "fidesui";

import type { MockSystem } from "../../types";
import ClassificationCard from "../cards/ClassificationCard";
import DataPurposesCard from "../cards/DataPurposesCard";
import DatasetsCard from "../cards/DatasetsCard";
import IntegrationsSummaryCard from "../cards/IntegrationsSummaryCard";
import MonitorsCard from "../cards/MonitorsCard";
import PrivacyRequestsCard from "../cards/PrivacyRequestsCard";
import ProducerConsumerCard from "../cards/ProducerConsumerCard";
import SystemInfoCard from "../cards/SystemInfoCard";

interface OverviewTabProps {
  system: MockSystem;
}

const OverviewTab = ({ system }: OverviewTabProps) => (
  <Row gutter={[24, 24]}>
    <Col span={16}>
      <Flex vertical gap="large">
        <ProducerConsumerCard relationships={system.relationships} />
        <IntegrationsSummaryCard integrations={system.integrations} />
        <ClassificationCard classification={system.classification} />
        <MonitorsCard monitors={system.monitors} />
      </Flex>
    </Col>
    <Col span={8}>
      <Flex vertical gap="large">
        <DataPurposesCard purposes={system.purposes} />
        <SystemInfoCard system={system} />
        <PrivacyRequestsCard requests={system.privacyRequests} />
        <DatasetsCard datasets={system.datasets} roles={system.roles} />
      </Flex>
    </Col>
  </Row>
);

export default OverviewTab;
