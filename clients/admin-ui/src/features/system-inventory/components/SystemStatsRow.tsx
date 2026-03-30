import { Card, Col, Flex, Row, Text, Title } from "fidesui";

import type { SystemInventoryStats } from "../types";

interface SystemStatsRowProps {
  stats: SystemInventoryStats;
}

interface StatCardProps {
  value: number;
  label: string;
  subtitle: string;
}

const StatCard = ({ value, label, subtitle }: StatCardProps) => (
  <Card size="small">
    <Flex vertical gap={4}>
      <Text type="secondary" className="text-xs">
        {label}
      </Text>
      <Title level={2} className="!mb-0">
        {value}
      </Title>
      <Text type="secondary" className="text-xs">
        {subtitle}
      </Text>
    </Flex>
  </Card>
);

const SystemStatsRow = ({ stats }: SystemStatsRowProps) => (
  <Row gutter={[16, 16]} className="mb-4">
    <Col span={6}>
      <StatCard
        value={stats.total}
        label="Total systems"
        subtitle={`${stats.total} registered`}
      />
    </Col>
    <Col span={6}>
      <StatCard
        value={stats.violations}
        label="Policy violations"
        subtitle="Producer/consumer mismatches"
      />
    </Col>
    <Col span={6}>
      <StatCard
        value={stats.issues}
        label="Governance issues"
        subtitle={`Across ${stats.issues} systems`}
      />
    </Col>
    <Col span={6}>
      <StatCard
        value={stats.healthy}
        label="Healthy"
        subtitle="No issues detected"
      />
    </Col>
  </Row>
);

export default SystemStatsRow;
