import { Card, Col, Flex, Row, Table, Tag, Text, Title } from "fidesui";
import Link from "next/link";
import { useMemo } from "react";

import {
  DATA_CONSUMERS_ROUTE,
  DATA_PURPOSES_ROUTE,
} from "~/features/common/nav/routes";

import type { GapCard, UnresolvedIdentity, ViolationCard } from "./mockData";
import {
  MOCK_GAP_CARDS,
  MOCK_UNRESOLVED_IDENTITIES,
  MOCK_VIOLATION_CARDS,
} from "./mockData";

const formatTableList = (tables: string[]): string => {
  if (tables.length === 0) return "";
  if (tables.length === 1) return tables[0];
  if (tables.length === 2) return `${tables[0]} and ${tables[1]}`;
  return `${tables.slice(0, -1).join(", ")}, and ${tables[tables.length - 1]}`;
};

const formatRelativeTime = (isoStr: string): string => {
  const diffMs = Date.now() - new Date(isoStr).getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 60)
    return `${diffMins} minute${diffMins !== 1 ? "s" : ""} ago`;
  const diffHrs = Math.floor(diffMins / 60);
  if (diffHrs < 24) return `${diffHrs} hour${diffHrs !== 1 ? "s" : ""} ago`;
  const diffDays = Math.floor(diffHrs / 24);
  if (diffDays === 1) return "yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  const diffWeeks = Math.floor(diffDays / 7);
  if (diffWeeks < 5) return `${diffWeeks} week${diffWeeks !== 1 ? "s" : ""} ago`;
  return new Date(isoStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
};

// ─── Triage strip ────────────────────────────────────────────────────────────

interface TriageStripProps {
  identityCount: number;
  issueCount: number;
}

const TriageStrip = ({ identityCount, issueCount }: TriageStripProps) => (
  <Flex
    className="mb-6 rounded border border-gray-100 bg-gray-50 px-5 py-4"
    gap={0}
    align="stretch"
  >
    <Flex vertical gap={2} className="flex-1">
      <Text className="text-xs font-semibold uppercase tracking-wide text-gray-400">
        Step 1
      </Text>
      <Text strong>Resolve unknown identities</Text>
      <Text
        type={identityCount > 0 ? "warning" : "secondary"}
        className="text-sm"
      >
        {identityCount} pending
      </Text>
    </Flex>
    <Flex align="center" className="px-6 text-gray-300 text-lg">
      →
    </Flex>
    <Flex vertical gap={2} className="flex-1">
      <Text className="text-xs font-semibold uppercase tracking-wide text-gray-400">
        Step 2
      </Text>
      <Text strong>Address access issues</Text>
      <Text
        type={issueCount > 0 ? "danger" : "secondary"}
        className="text-sm"
      >
        {issueCount} pending
      </Text>
    </Flex>
  </Flex>
);

// ─── Unresolved identities table ─────────────────────────────────────────────

const identityColumns = [
  {
    title: "Identity",
    dataIndex: "identifier",
    render: (id: string) => (
      <Text
        ellipsis={{ tooltip: id }}
        className="font-mono text-xs"
        style={{ maxWidth: 280, display: "block" }}
      >
        {id}
      </Text>
    ),
  },
  {
    title: "Queries",
    dataIndex: "query_count",
    align: "right" as const,
    render: (n: number) => n.toLocaleString(),
  },
  {
    title: "Datasets accessed",
    dataIndex: "datasets",
    render: (datasets: string[]) => {
      const visible = datasets.slice(0, 2).join(", ");
      const remaining = datasets.length - 2;
      return remaining > 0 ? `${visible} +${remaining} more` : visible;
    },
  },
  {
    title: "Last seen",
    dataIndex: "last_seen",
    render: (ts: string) => formatRelativeTime(ts),
  },
  {
    title: "",
    key: "action",
    render: () => (
      <Link href={DATA_CONSUMERS_ROUTE}>
        <Text
          type="secondary"
          className="text-xs whitespace-nowrap hover:text-blue-500"
        >
          Register consumer →
        </Text>
      </Link>
    ),
  },
];

const UnresolvedIdentitiesTable = ({
  items,
}: {
  items: UnresolvedIdentity[];
}) => (
  <Flex vertical gap={0}>
    <Flex align="center" gap={8} className="mb-1">
      <Title level={5} className="!mb-0">
        Unresolved identities
      </Title>
      <Tag>{items.length}</Tag>
    </Flex>
    <Text type="secondary" className="text-xs mb-4 block">
      Identifiers in query logs with no matching consumer record. Register
      them to begin compliance evaluation for their activity.
    </Text>
    <Table
      columns={identityColumns}
      dataSource={items}
      rowKey="id"
      size="small"
      pagination={false}
      bordered={false}
    />
  </Flex>
);

// ─── Access issues (merged violations + gaps) ─────────────────────────────────

type AccessIssue =
  | (ViolationCard & { kind: "violation" })
  | (GapCard & { kind: "gap" });

const cardStyle = { backgroundColor: "#fafafa", height: "100%" };

const AccessIssueCard = ({ item }: { item: AccessIssue }) => {
  const isViolation = item.kind === "violation";
  const title = isViolation
    ? `${item.consumer_name} — ${(item as ViolationCard).purpose}`
    : `${item.consumer_name} — ${(item as GapCard).dataset}`;
  const tables = isViolation
    ? (item as ViolationCard).tables
    : (item as GapCard).tables;
  const tableList = formatTableList(tables);
  const narrative = isViolation
    ? `Accessed ${tableList} outside approved purpose boundary — ${item.query_count.toLocaleString()} queries, last seen ${formatRelativeTime(item.last_seen)}.`
    : `Querying ${tableList} with no matching approved purpose — ${item.query_count.toLocaleString()} queries, last seen ${formatRelativeTime(item.last_seen)}.`;
  const ctaHref = isViolation
    ? `${DATA_CONSUMERS_ROUTE}/${item.consumer_id}`
    : DATA_PURPOSES_ROUTE;
  const ctaLabel = isViolation ? "View activity →" : "Create purpose →";

  return (
    <Card size="small" style={cardStyle}>
      <Flex vertical gap={8}>
        <Flex gap={8} align="center">
          <Tag color={isViolation ? "error" : "caution"}>
            {isViolation ? "Non-compliant" : "No policy"}
          </Tag>
          <Text strong className="text-xs">
            {title}
          </Text>
        </Flex>
        <Text type="secondary" className="text-xs">
          {narrative}
        </Text>
        <Link href={ctaHref}>
          <Text type="secondary" className="text-xs hover:text-blue-500">
            {ctaLabel}
          </Text>
        </Link>
      </Flex>
    </Card>
  );
};

const AccessIssuesSection = ({ items }: { items: AccessIssue[] }) => (
  <Flex vertical gap={0}>
    <Flex align="center" gap={8} className="mb-1">
      <Title level={5} className="!mb-0">
        Access issues
      </Title>
      <Tag>{items.length}</Tag>
    </Flex>
    <Text type="secondary" className="text-xs mb-4 block">
      Data access outside declared purposes, sorted by most recent.
      Non-compliant entries exceed a purpose boundary; no policy entries have
      no declared purpose at all.
    </Text>
    <Row gutter={[16, 16]}>
      {items.map((item) => (
        <Col key={item.id} xs={24} sm={12} lg={6}>
          <AccessIssueCard item={item} />
        </Col>
      ))}
    </Row>
  </Flex>
);

// ─── Root component ───────────────────────────────────────────────────────────

export const SummaryCards = () => {
  const identities = MOCK_UNRESOLVED_IDENTITIES;

  const accessIssues = useMemo<AccessIssue[]>(
    () =>
      [
        ...MOCK_VIOLATION_CARDS.map((v) => ({ ...v, kind: "violation" as const })),
        ...MOCK_GAP_CARDS.map((g) => ({ ...g, kind: "gap" as const })),
      ].sort((a, b) => b.last_seen.localeCompare(a.last_seen)),
    [],
  );

  if (identities.length === 0 && accessIssues.length === 0) {
    return <Text type="secondary">No findings detected.</Text>;
  }

  return (
    <Flex vertical gap={32}>
      <TriageStrip
        identityCount={identities.length}
        issueCount={accessIssues.length}
      />
      {identities.length > 0 && (
        <UnresolvedIdentitiesTable items={identities} />
      )}
      {accessIssues.length > 0 && (
        <AccessIssuesSection items={accessIssues} />
      )}
    </Flex>
  );
};
