import { Avatar, Card, Col, Descriptions, Flex, Row, Tag, Text, Title } from "fidesui";

import { CAPABILITY_TAG_COLORS } from "../../constants";
import type { MockSystem } from "../../types";
import { getSystemCapabilities } from "../../utils";
import ClassificationCard from "../cards/ClassificationCard";
import DatasetsCard from "../cards/DatasetsCard";
import IntegrationsSummaryCard from "../cards/IntegrationsSummaryCard";
import MonitorsCard from "../cards/MonitorsCard";
import PrivacyRequestsCard from "../cards/PrivacyRequestsCard";
import ProducerConsumerCard from "../cards/ProducerConsumerCard";

interface OverviewTabProps {
  system: MockSystem;
}

const OverviewTab = ({ system }: OverviewTabProps) => {
  const capabilities = getSystemCapabilities(system);

  return (
    <Flex vertical gap={24}>
      {/* About */}
      <Card size="small">
        <Title level={5} className="!mb-3">
          About
        </Title>
        <Descriptions column={2} size="small">
          <Descriptions.Item label="Type">{system.system_type}</Descriptions.Item>
          <Descriptions.Item label="Department">{system.department}</Descriptions.Item>
          <Descriptions.Item label="Responsibility">{system.responsibility}</Descriptions.Item>
          <Descriptions.Item label="Group">{system.group ?? "—"}</Descriptions.Item>
          <Descriptions.Item label="Roles">
            {system.roles.join(", ") || "—"}
          </Descriptions.Item>
          <Descriptions.Item label="Annotation">
            {system.annotation_percent}%
          </Descriptions.Item>
        </Descriptions>
        <Text type="secondary" className="mt-2 block text-sm">
          {system.description}
        </Text>
      </Card>

      {/* Purposes + Stewards + Capabilities side by side */}
      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Card size="small" className="h-full">
            <Title level={5} className="!mb-3">
              Purposes
            </Title>
            {system.purposes.length > 0 ? (
              <Flex gap={4} wrap>
                {system.purposes.map((p) => (
                  <Tag key={p.name} bordered={false}>
                    {p.name}
                  </Tag>
                ))}
              </Flex>
            ) : (
              <Text type="secondary">No purposes defined</Text>
            )}
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small" className="h-full">
            <Title level={5} className="!mb-3">
              Stewards
            </Title>
            {system.stewards.length > 0 ? (
              <Flex vertical gap={8}>
                {system.stewards.map((st) => (
                  <Flex key={st.initials} align="center" gap={8}>
                    <Avatar
                      size="small"
                      style={{
                        backgroundColor: "#e6e6e8",
                        color: "#53575c",
                        fontSize: 10,
                      }}
                    >
                      {st.initials}
                    </Avatar>
                    <Text>{st.name}</Text>
                  </Flex>
                ))}
              </Flex>
            ) : (
              <Text type="danger">No steward assigned</Text>
            )}
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small" className="h-full">
            <Title level={5} className="!mb-3">
              Capabilities
            </Title>
            {capabilities.length > 0 ? (
              <Flex gap={4} wrap>
                {capabilities.map((cap) => (
                  <Tag key={cap} color={CAPABILITY_TAG_COLORS[cap]}>
                    {cap}
                  </Tag>
                ))}
              </Flex>
            ) : (
              <Text type="secondary">No capabilities detected</Text>
            )}
          </Card>
        </Col>
      </Row>

      {/* Detailed cards in two columns */}
      <Row gutter={[24, 24]}>
        <Col span={12}>
          <Flex vertical gap="large">
            <ProducerConsumerCard relationships={system.relationships} />
            <ClassificationCard classification={system.classification} />
          </Flex>
        </Col>
        <Col span={12}>
          <Flex vertical gap="large">
            <IntegrationsSummaryCard integrations={system.integrations} />
            <MonitorsCard monitors={system.monitors} />
          </Flex>
        </Col>
      </Row>

      {/* Bottom row */}
      <Row gutter={[24, 24]}>
        <Col span={12}>
          <PrivacyRequestsCard requests={system.privacyRequests} />
        </Col>
        <Col span={12}>
          <DatasetsCard datasets={system.datasets} roles={system.roles} />
        </Col>
      </Row>
    </Flex>
  );
};

export default OverviewTab;
