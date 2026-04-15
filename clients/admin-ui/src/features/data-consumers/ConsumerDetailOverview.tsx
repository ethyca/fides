import {
  Alert,
  Card,
  Col,
  CUSTOM_TAG_COLOR,
  Flex,
  Input,
  Row,
  Segmented,
  Tag,
  Text,
  Title,
} from "fidesui";
import Link from "next/link";
import { useMemo, useState } from "react";

import {
  ACCESS_CONTROL_ROUTE,
  DATA_PURPOSES_ROUTE,
} from "~/features/common/nav/routes";
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
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<
    "all" | "non_compliant" | "no_policy"
  >("all");

  const allViolationGroups = useMemo(
    () => MOCK_VIOLATION_GROUPS[consumer.id] ?? [],
    [consumer.id],
  );

  const allPolicyGaps = useMemo(
    () => MOCK_POLICY_GAPS[consumer.id] ?? [],
    [consumer.id],
  );

  const hasFindings = allViolationGroups.length > 0 || allPolicyGaps.length > 0;

  const needle = search.toLowerCase();

  const violationGroups =
    statusFilter === "no_policy"
      ? []
      : allViolationGroups.filter((g) =>
          g.purpose.toLowerCase().includes(needle),
        );

  const policyGaps =
    statusFilter === "non_compliant"
      ? []
      : allPolicyGaps.filter((g) =>
          g.dataset.toLowerCase().includes(needle),
        );

  return (
    <Flex vertical gap="large">
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
            This consumer's data access, grouped by policy. Violation
            entries show queries outside an approved purpose boundary. No policy
            entries show activity with no matching purpose at all.
          </Text>

          <Flex gap="small" align="center" justify="space-between" style={{ marginBottom: 12 }}>
            <Input
              placeholder="Search policies…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              allowClear
              style={{ maxWidth: 240 }}
            />
            <Segmented
              value={statusFilter}
              onChange={(v) =>
                setStatusFilter(v as "all" | "non_compliant" | "no_policy")
              }
              options={[
                { label: "All", value: "all" },
                { label: "Violation", value: "non_compliant" },
                { label: "No policy", value: "no_policy" },
              ]}
            />
          </Flex>

          <Row gutter={[12, 12]}>
            {violationGroups.map((group) => {
              const allTables = group.datasets.flatMap((ds) => ds.tables);
              const tableList = formatTableList(allTables);
              const lastSeen = group.datasets.reduce((latest, ds) =>
                ds.lastSeen > latest.lastSeen ? ds : latest,
              ).lastSeen;

              return (
                <Col key={group.purpose} xs={24} sm={12} md={8}>
                  <Card
                    size="small"
                    className="h-full transition-shadow hover:shadow-[0_2px_6px_rgba(0,0,0,0.08)]"
                    style={{
                      backgroundColor: "#fafafa",
                      borderLeft: "3px solid #ff4d4f",
                    }}
                  >
                    <Flex vertical gap={8} className="h-full">
                      <Tag
                        color={CUSTOM_TAG_COLOR.ERROR}
                        style={{ alignSelf: "flex-start" }}
                      >
                        Violation
                      </Tag>
                      <Text strong style={{ fontSize: 13 }}>
                        Policy: {group.purpose}
                      </Text>
                      <Text type="secondary" className="line-clamp-2 text-xs">
                        Accessed {tableList} outside this purpose&apos;s
                        approved boundary.
                      </Text>
                      <div className="mt-auto">
                        <Text type="secondary" className="text-xs">
                          {group.totalQueries.toLocaleString()} queries · last{" "}
                          {new Date(lastSeen).toLocaleDateString()}
                        </Text>
                        <div style={{ marginTop: 6 }}>
                          <Link href={ACCESS_CONTROL_ROUTE}>
                            <Text type="secondary" className="text-xs">
                              View in Access Control →
                            </Text>
                          </Link>
                        </div>
                      </div>
                    </Flex>
                  </Card>
                </Col>
              );
            })}

            {policyGaps.map((gap) => {
              const tableList = formatTableList(gap.tables);

              return (
                <Col key={gap.dataset} xs={24} sm={12} md={8}>
                  <Card
                    size="small"
                    className="h-full transition-shadow hover:shadow-[0_2px_6px_rgba(0,0,0,0.08)]"
                    style={{
                      backgroundColor: "#fafafa",
                      borderLeft: "3px solid #faad14",
                    }}
                  >
                    <Flex vertical gap={8} className="h-full">
                      <Tag
                        color={CUSTOM_TAG_COLOR.WARNING}
                        style={{ alignSelf: "flex-start" }}
                      >
                        No policy
                      </Tag>
                      <Text strong style={{ fontSize: 13 }}>
                        Policy: {gap.dataset}
                      </Text>
                      <Text type="secondary" className="line-clamp-2 text-xs">
                        Querying {tableList} with no matching declared purpose.
                      </Text>
                      <div className="mt-auto">
                        <Text type="secondary" className="text-xs">
                          {gap.queryCount.toLocaleString()} queries · last{" "}
                          {new Date(gap.lastSeen).toLocaleDateString()}
                        </Text>
                        <div style={{ marginTop: 6 }}>
                          <Link href={`${DATA_PURPOSES_ROUTE}/new`}>
                            <Text type="secondary" className="text-xs">
                              Create policy →
                            </Text>
                          </Link>
                        </div>
                      </div>
                    </Flex>
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
