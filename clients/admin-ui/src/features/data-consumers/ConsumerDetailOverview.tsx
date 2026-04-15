import {
  Alert,
  Card,
  Col,
  CUSTOM_TAG_COLOR,
  Descriptions,
  Flex,
  Row,
  Tag,
  Text,
  Title,
} from "fidesui";
import Link from "next/link";
import { useMemo } from "react";

import {
  ACCESS_CONTROL_ROUTE,
  DATA_PURPOSES_ROUTE,
} from "~/features/common/nav/routes";

import { CONSUMER_TYPE_UI_LABELS, PLATFORM_LABELS } from "./constants";
import { MOCK_POLICY_GAPS, MOCK_VIOLATION_GROUPS } from "./mockData";
import type { MockDataConsumer } from "./types";

interface ConsumerDetailOverviewProps {
  consumer: MockDataConsumer;
}

const formatTableList = (tables: string[]): string => {
  if (tables.length === 0) return "";
  if (tables.length === 1) return tables[0];
  if (tables.length === 2) return `${tables[0]} and ${tables[1]}`;
  return `${tables.slice(0, -1).join(", ")}, and ${tables[tables.length - 1]}`;
};

const ConsumerDetailOverview = ({
  consumer,
}: ConsumerDetailOverviewProps) => {
  const violationGroups = useMemo(
    () => MOCK_VIOLATION_GROUPS[consumer.id] ?? [],
    [consumer.id],
  );

  const policyGaps = useMemo(
    () => MOCK_POLICY_GAPS[consumer.id] ?? [],
    [consumer.id],
  );

  const hasFindings = violationGroups.length > 0 || policyGaps.length > 0;

  return (
    <Flex vertical gap="large">
      {/* Details */}
      <Card size="small">
        <Descriptions column={2} size="small">
          <Descriptions.Item label="Platform">
            {consumer.platform
              ? (PLATFORM_LABELS[consumer.platform] ?? consumer.platform)
              : "—"}
          </Descriptions.Item>
          <Descriptions.Item label="Type">
            {CONSUMER_TYPE_UI_LABELS[consumer.type] ?? consumer.type}
          </Descriptions.Item>
          <Descriptions.Item label="Scope">
            {consumer.identifier}
          </Descriptions.Item>
          <Descriptions.Item label="Purposes">
            {consumer.purposes.length > 0
              ? consumer.purposes.join(", ")
              : "None assigned"}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* No-purposes warning */}
      {consumer.purposes.length === 0 && (
        <Alert
          type="warning"
          showIcon
          message="This consumer has no declared purposes"
          description="Without declared purposes, access violations cannot be evaluated. Assign purposes in the Configuration tab to enable monitoring."
        />
      )}

      {/* Activity */}
      {hasFindings && (
        <div>
          <Title level={5} style={{ marginBottom: 4 }}>
            Activity
          </Title>
          <Text type="secondary" style={{ display: "block", marginBottom: 16 }}>
            This consumer's data access, grouped by policy. Non-compliant
            entries show queries outside an approved purpose boundary. No policy
            entries show activity with no matching purpose at all.
          </Text>

          <Row gutter={[12, 12]}>
            {violationGroups.map((group) => {
              const allTables = group.datasets.flatMap((ds) => ds.tables);
              const tableList = formatTableList(allTables);
              const lastSeen = group.datasets.reduce((latest, ds) =>
                ds.lastSeen > latest.lastSeen ? ds : latest,
              ).lastSeen;

              return (
                <Col key={group.purpose} xs={24} sm={12}>
                  <Card
                    size="small"
                    className="h-full"
                    title={
                      <Flex align="center" gap="small">
                        <Tag color={CUSTOM_TAG_COLOR.ERROR}>Non-compliant</Tag>
                        <Text strong style={{ fontSize: 13 }}>
                          {group.purpose}
                        </Text>
                      </Flex>
                    }
                  >
                    <Text type="secondary" className="text-xs">
                      Accessed {tableList} outside this purpose&apos;s approved
                      boundary — {group.totalQueries.toLocaleString()} queries,
                      last seen {new Date(lastSeen).toLocaleDateString()}.
                    </Text>
                    <div style={{ marginTop: 10 }}>
                      <Link href={ACCESS_CONTROL_ROUTE}>
                        <Text type="secondary" className="text-xs">
                          View in Access Control →
                        </Text>
                      </Link>
                    </div>
                  </Card>
                </Col>
              );
            })}

            {policyGaps.map((gap) => {
              const tableList = formatTableList(gap.tables);

              return (
                <Col key={gap.dataset} xs={24} sm={12}>
                  <Card
                    size="small"
                    className="h-full"
                    title={
                      <Flex align="center" gap="small">
                        <Tag color={CUSTOM_TAG_COLOR.WARNING}>No policy</Tag>
                        <Text strong style={{ fontSize: 13 }}>
                          {gap.dataset}
                        </Text>
                      </Flex>
                    }
                  >
                    <Text type="secondary" className="text-xs">
                      Querying {tableList} with no matching declared purpose —{" "}
                      {gap.queryCount.toLocaleString()} queries, last seen{" "}
                      {new Date(gap.lastSeen).toLocaleDateString()}.
                    </Text>
                    <div style={{ marginTop: 10 }}>
                      <Link href={`${DATA_PURPOSES_ROUTE}/new`}>
                        <Text type="secondary" className="text-xs">
                          Create policy →
                        </Text>
                      </Link>
                    </div>
                  </Card>
                </Col>
              );
            })}
          </Row>
        </div>
      )}

      {/* Healthy state */}
      {consumer.purposes.length > 0 && !hasFindings && (
        <Card size="small">
          <Flex justify="center" className="py-4">
            <Text type="secondary">No policy deviations or gaps detected</Text>
          </Flex>
        </Card>
      )}
    </Flex>
  );
};

export default ConsumerDetailOverview;
