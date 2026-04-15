import { Avatar, Card, Col, Flex, Row, Text, Title } from "fidesui";

import type { MockSystem } from "../types";

interface SystemDetailStatsProps {
  system: MockSystem;
}

const SystemDetailStats = ({ system }: SystemDetailStatsProps) => {
  const totalFields =
    system.classification.approved +
    system.classification.pending +
    system.classification.unreviewed;
  const classPercent =
    totalFields > 0
      ? Math.round((system.classification.approved / totalFields) * 100)
      : 0;

  const totalDatasets = system.datasets.length;
  const totalCollections = system.datasets.reduce(
    (sum, d) => sum + d.collectionCount,
    0,
  );
  const totalFieldCount = system.datasets.reduce(
    (sum, d) => sum + d.fieldCount,
    0,
  );

  return (
    <Row gutter={[16, 16]} className="mb-4">
      <Col span={6}>
        <Card size="small">
          <Text type="secondary" className="text-xs">
            Stewards
          </Text>
          <Flex gap={-6} className="mt-1">
            {system.stewards.length > 0 ? (
              system.stewards.map((st) => (
                <Avatar
                  key={st.initials}
                  size="small"
                  style={{
                    backgroundColor: "#e6e6e8",
                    color: "#53575c",
                    fontSize: 10,
                    border: "2px solid #fafafa",
                  }}
                >
                  {st.initials}
                </Avatar>
              ))
            ) : (
              <Text type="secondary" className="text-xs">
                None assigned
              </Text>
            )}
          </Flex>
        </Card>
      </Col>
      <Col span={6}>
        <Card size="small">
          <Text type="secondary" className="text-xs">
            Classification
          </Text>
          <Title level={3} className="!mb-0">
            {classPercent}%
          </Title>
          <Text type="secondary" className="text-xs">
            {system.classification.approved} of {totalFields} fields
          </Text>
        </Card>
      </Col>
      <Col span={6}>
        <Card size="small">
          <Text type="secondary" className="text-xs">
            Privacy requests
          </Text>
          <Title level={3} className="!mb-0">
            {system.privacyRequests.open} open
          </Title>
          <Text type="secondary" className="text-xs">
            {system.privacyRequests.closed} closed &middot; avg{" "}
            {system.privacyRequests.avgAccessDays}d
          </Text>
        </Card>
      </Col>
      <Col span={6}>
        <Card size="small">
          <Text type="secondary" className="text-xs">
            Datasets
          </Text>
          <Title level={3} className="!mb-0">
            {totalDatasets}
          </Title>
          <Text type="secondary" className="text-xs">
            {totalCollections} collections &middot; {totalFieldCount} fields
          </Text>
        </Card>
      </Col>
    </Row>
  );
};

export default SystemDetailStats;
