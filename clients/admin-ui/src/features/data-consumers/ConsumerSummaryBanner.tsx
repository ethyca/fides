import {
  Alert,
  Button,
  Card,
  CUSTOM_TAG_COLOR,
  Descriptions,
  Flex,
  Table,
  Tag,
  Typography,
} from "fidesui";
import Link from "next/link";
import { useMemo } from "react";

import { ACCESS_CONTROL_ROUTE } from "~/features/common/nav/routes";

import { CONSUMER_TYPE_UI_LABELS, PLATFORM_LABELS } from "./constants";
import { MOCK_VIOLATIONS } from "./mockData";
import type { ConsumerViolation, MockDataConsumer } from "./types";

interface ConsumerSummaryBannerProps {
  consumer: MockDataConsumer;
}

const violationColumns = [
  {
    title: "Dataset / Table",
    key: "location",
    render: (_: unknown, v: ConsumerViolation) => (
      <Flex vertical gap={2}>
        <Typography.Text strong>{v.dataset}</Typography.Text>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          {v.table}
        </Typography.Text>
      </Flex>
    ),
  },
  {
    title: "Description",
    dataIndex: "description",
    key: "description",
    render: (text: string) => (
      <Typography.Text ellipsis={{ tooltip: text }}>{text}</Typography.Text>
    ),
  },
  {
    title: "Detected",
    key: "accessedAt",
    width: 160,
    render: (_: unknown, v: ConsumerViolation) => {
      const date = new Date(v.accessedAt);
      return (
        <Typography.Text type="secondary">
          {date.toLocaleDateString()} {date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </Typography.Text>
      );
    },
  },
];

const ConsumerSummaryBanner = ({ consumer }: ConsumerSummaryBannerProps) => {
  const violations = useMemo(
    () => MOCK_VIOLATIONS.filter((v) => v.consumerId === consumer.id),
    [consumer.id],
  );

  const statusColor =
    consumer.violationCount > 0
      ? CUSTOM_TAG_COLOR.ERROR
      : consumer.purposes.length === 0
        ? CUSTOM_TAG_COLOR.WARNING
        : CUSTOM_TAG_COLOR.SUCCESS;

  const statusLabel =
    consumer.violationCount > 0
      ? `${consumer.violationCount} violations`
      : consumer.purposes.length === 0
        ? "No purposes"
        : "Healthy";

  return (
    <Flex vertical gap="middle">
      {/* Overview card */}
      <Card size="small">
        <Flex justify="space-between" align="start">
          <Descriptions column={2} size="small" style={{ flex: 1 }}>
            <Descriptions.Item label="Type">
              {CONSUMER_TYPE_UI_LABELS[consumer.type] ?? consumer.type}
            </Descriptions.Item>
            <Descriptions.Item label="Status">
              <Tag color={statusColor}>{statusLabel}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Identifier">
              {consumer.identifier}
            </Descriptions.Item>
            <Descriptions.Item label="Platform">
              {consumer.platform
                ? (PLATFORM_LABELS[consumer.platform] ?? consumer.platform)
                : "—"}
            </Descriptions.Item>
            <Descriptions.Item label="Purposes" span={2}>
              {consumer.purposes.length > 0
                ? consumer.purposes.join(", ")
                : "None assigned"}
            </Descriptions.Item>
          </Descriptions>
          <Link href={ACCESS_CONTROL_ROUTE}>
            <Button type="default">View in Access Control ↗</Button>
          </Link>
        </Flex>
      </Card>

      {/* Violations section */}
      {violations.length > 0 && (
        <Card
          size="small"
          title={
            <Flex align="center" gap="small">
              <span>Violations</span>
              <Tag color={CUSTOM_TAG_COLOR.ERROR}>{violations.length}</Tag>
            </Flex>
          }
        >
          <Table<ConsumerViolation>
            dataSource={violations}
            columns={violationColumns}
            rowKey="id"
            size="small"
            pagination={false}
          />
        </Card>
      )}

      {/* No-purposes warning */}
      {consumer.purposes.length === 0 && (
        <Alert
          type="warning"
          showIcon
          message="This consumer has no declared purposes"
          description="Without declared purposes, access violations cannot be evaluated. Assign purposes to enable access control monitoring."
        />
      )}
    </Flex>
  );
};

export default ConsumerSummaryBanner;
