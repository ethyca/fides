import {
  Button,
  Card,
  Col,
  CUSTOM_TAG_COLOR,
  Flex,
  Icons,
  Row,
  Segmented,
  Select,
  SparkleIcon,
  Tag,
  Text,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import Link from "next/link";
import { useMemo, useState } from "react";

import {
  DATA_CONSUMERS_ROUTE,
  DATA_PURPOSES_ROUTE,
} from "~/features/common/nav/routes";

import type { FindingSeverity, GapCard, ViolationCard } from "./mockData";
import { MOCK_GAP_CARDS, MOCK_VIOLATION_CARDS } from "./mockData";

// ─── Helpers ─────────────────────────────────────────────────────────────────

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
  if (diffWeeks < 5)
    return `${diffWeeks} week${diffWeeks !== 1 ? "s" : ""} ago`;
  return new Date(isoStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
};

const SEVERITY_ORDER: Record<FindingSeverity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

const SEVERITY_COLORS: Record<FindingSeverity, string> = {
  critical: palette.FIDESUI_ERROR,
  high: palette.FIDESUI_ERROR,
  medium: palette.FIDESUI_WARNING,
  low: palette.FIDESUI_MINOS,
};

// ─── Briefing banner (matches SystemBriefingBanner styling) ──────────────────

interface BriefingBannerProps {
  unresolvedCount: number;
  onReviewIdentities?: () => void;
}

export const UnresolvedBanner = ({
  unresolvedCount,
  onReviewIdentities,
}: BriefingBannerProps) => {
  const [dismissed, setDismissed] = useState(false);

  if (unresolvedCount === 0 || dismissed) return null;

  return (
    <div
      className="mb-4 rounded-lg px-5 py-4"
      style={{ backgroundColor: palette.FIDESUI_BG_DEFAULT }}
    >
      <Flex gap={12} align="flex-start" className="min-w-0">
        <SparkleIcon size={16} className="mt-1 shrink-0" />
        <Flex vertical gap={6} className="min-w-0 flex-1">
          <Text className="text-sm leading-relaxed">
            We've detected{" "}
            <strong>
              {unresolvedCount} unresolved{" "}
              {unresolvedCount === 1 ? "identity" : "identities"}
            </strong>{" "}
            in your query logs — these are service accounts or users accessing
            data that haven't been registered as consumers yet. Until they're
            resolved, some findings below may be incomplete.
          </Text>

          <Flex align="center" gap={6}>
            <div
              className="size-2 shrink-0 rounded-full"
              style={{ backgroundColor: palette.FIDESUI_WARNING }}
            />
            <Text className="min-w-0 flex-1 text-xs">
              {unresolvedCount} pending{" "}
              {unresolvedCount === 1
                ? "identity needs"
                : "identities need"}{" "}
              registration
            </Text>
            <Button
              type="text"
              size="small"
              className="!px-0 !text-xs"
              style={{ color: palette.FIDESUI_MINOS }}
              onClick={() => onReviewIdentities?.()}
            >
              Review
            </Button>
            <span
              role="button"
              aria-label="Dismiss"
              tabIndex={0}
              className="shrink-0 cursor-pointer"
              onClick={() => setDismissed(true)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") setDismissed(true);
              }}
            >
              <Icons.Close
                size={12}
                style={{ color: palette.FIDESUI_NEUTRAL_500 }}
              />
            </span>
          </Flex>
        </Flex>
      </Flex>
    </div>
  );
};

// ─── Grouped data types ──────────────────────────────────────────────────────

interface PolicyGroup {
  kind: "violation";
  purpose: string;
  severity: FindingSeverity;
  consumers: { id: string; name: string; queryCount: number; lastSeen: string }[];
  totalQueries: number;
  lastSeen: string;
}

interface ConsumerGapGroup {
  kind: "gap";
  consumerName: string;
  consumerId: string | null;
  severity: FindingSeverity;
  datasets: { name: string; tables: string[]; queryCount: number; lastSeen: string }[];
  totalQueries: number;
  lastSeen: string;
}

type GroupedCard = PolicyGroup | ConsumerGapGroup;

function buildGroupedCards(): GroupedCard[] {
  // Group violations by policy
  const policyMap = new Map<string, ViolationCard[]>();
  for (const v of MOCK_VIOLATION_CARDS) {
    const existing = policyMap.get(v.purpose) ?? [];
    existing.push(v);
    policyMap.set(v.purpose, existing);
  }

  const policyGroups: PolicyGroup[] = [...policyMap.entries()].map(
    ([purpose, violations]) => {
      const consumers = violations.map((v) => ({
        id: v.consumer_id,
        name: v.consumer_name,
        queryCount: v.query_count,
        lastSeen: v.last_seen,
      }));
      const totalQueries = violations.reduce((s, v) => s + v.query_count, 0);
      const lastSeen = violations.reduce(
        (latest, v) => (v.last_seen > latest ? v.last_seen : latest),
        "",
      );
      const highestSeverity = violations.reduce(
        (best, v) =>
          SEVERITY_ORDER[v.severity] < SEVERITY_ORDER[best]
            ? v.severity
            : best,
        "low" as FindingSeverity,
      );
      return {
        kind: "violation" as const,
        purpose,
        severity: highestSeverity,
        consumers,
        totalQueries,
        lastSeen,
      };
    },
  );

  // Group gaps by consumer
  const consumerMap = new Map<string, GapCard[]>();
  for (const g of MOCK_GAP_CARDS) {
    const key = g.consumer_id ?? g.consumer_name;
    const existing = consumerMap.get(key) ?? [];
    existing.push(g);
    consumerMap.set(key, existing);
  }

  const gapGroups: ConsumerGapGroup[] = [...consumerMap.entries()].map(
    ([, gaps]) => {
      const datasets = gaps.map((g) => ({
        name: g.dataset,
        tables: g.tables,
        queryCount: g.query_count,
        lastSeen: g.last_seen,
      }));
      const totalQueries = gaps.reduce((s, g) => s + g.query_count, 0);
      const lastSeen = gaps.reduce(
        (latest, g) => (g.last_seen > latest ? g.last_seen : latest),
        "",
      );
      const highestSeverity = gaps.reduce(
        (best, g) =>
          SEVERITY_ORDER[g.severity] < SEVERITY_ORDER[best]
            ? g.severity
            : best,
        "low" as FindingSeverity,
      );
      return {
        kind: "gap" as const,
        consumerName: gaps[0].consumer_name,
        consumerId: gaps[0].consumer_id,
        severity: highestSeverity,
        datasets,
        totalQueries,
        lastSeen,
      };
    },
  );

  return [...policyGroups, ...gapGroups].sort(
    (a, b) =>
      SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity] ||
      b.lastSeen.localeCompare(a.lastSeen),
  );
}

// ─── Violation card (grouped by policy) ──────────────────────────────────────

const PolicyViolationCard = ({ group }: { group: PolicyGroup }) => (
  <Card
    size="small"
    className="h-full transition-shadow hover:shadow-[0_2px_6px_rgba(0,0,0,0.08)]"
    style={{
      backgroundColor: "#fafafa",
      borderLeft: `3px solid ${palette.FIDESUI_ERROR}`,
    }}
  >
    <Flex vertical gap={8} className="h-full">
      <Flex justify="space-between" align="center">
        <Tag color={CUSTOM_TAG_COLOR.ERROR}>Violation</Tag>
        <Flex align="center" gap={4}>
          <div
            className="size-1.5 rounded-full"
            style={{ backgroundColor: SEVERITY_COLORS[group.severity] }}
          />
          <Text type="secondary" className="text-[10px] capitalize">
            {group.severity}
          </Text>
        </Flex>
      </Flex>

      <Text strong className="text-xs">
        {group.purpose}
      </Text>

      <Flex vertical gap={2}>
        {group.consumers.map((c) => (
          <Flex key={c.id} align="center" justify="space-between">
            <Link href={`${DATA_CONSUMERS_ROUTE}/${c.id}`}>
              <Text className="text-xs" style={{ color: palette.FIDESUI_MINOS }}>
                {c.name}
              </Text>
            </Link>
            <Text type="secondary" className="text-[10px]">
              {c.queryCount.toLocaleString()} queries
            </Text>
          </Flex>
        ))}
      </Flex>

      <div className="mt-auto">
        <Text type="secondary" className="text-[10px]">
          {group.totalQueries.toLocaleString()} total queries · last{" "}
          {formatRelativeTime(group.lastSeen)}
        </Text>
      </div>
    </Flex>
  </Card>
);

// ─── Gap card (grouped by consumer) ──────────────────────────────────────────

const ConsumerGapCard = ({ group }: { group: ConsumerGapGroup }) => {
  const isUnknown = !group.consumerId;

  return (
    <Card
      size="small"
      className="h-full transition-shadow hover:shadow-[0_2px_6px_rgba(0,0,0,0.08)]"
      style={{
        backgroundColor: "#fafafa",
        borderLeft: "3px solid #faad14",
        ...(isUnknown
          ? { borderStyle: "dashed", borderLeftStyle: "solid" }
          : {}),
      }}
    >
      <Flex vertical gap={8} className="h-full">
        <Flex justify="space-between" align="center">
          <Tag color={CUSTOM_TAG_COLOR.WARNING}>No policy</Tag>
          <Flex align="center" gap={4}>
            <div
              className="size-1.5 rounded-full"
              style={{ backgroundColor: SEVERITY_COLORS[group.severity] }}
            />
            <Text type="secondary" className="text-[10px] capitalize">
              {group.severity}
            </Text>
          </Flex>
        </Flex>

        <Text strong className="text-xs">
          {group.consumerName}
        </Text>

        <Flex vertical gap={2}>
          {group.datasets.map((ds) => (
            <Flex key={ds.name} align="center" justify="space-between">
              <Text type="secondary" className="text-xs">
                {ds.name}
              </Text>
              <Text type="secondary" className="text-[10px]">
                {ds.queryCount.toLocaleString()} queries
              </Text>
            </Flex>
          ))}
        </Flex>

        <div className="mt-auto">
          <Text type="secondary" className="text-[10px]">
            {group.totalQueries.toLocaleString()} total queries · last{" "}
            {formatRelativeTime(group.lastSeen)}
          </Text>
          <div className="mt-1">
            <Link href={DATA_PURPOSES_ROUTE}>
              <Text
                className="text-xs"
                style={{ color: palette.FIDESUI_MINOS }}
              >
                Create policy →
              </Text>
            </Link>
          </div>
        </div>
      </Flex>
    </Card>
  );
};

// ─── Consumers table ─────────────────────────────────────────────────────────

export { formatRelativeTime };

export const consumerColumns = [
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
          className="text-xs whitespace-nowrap"
          style={{ color: palette.FIDESUI_MINOS }}
        >
          Register consumer →
        </Text>
      </Link>
    ),
  },
];

// ─── Root component ──────────────────────────────────────────────────────────

type FindingFilter = "all" | "violations" | "gaps";

export const SummaryCards = () => {
  const [findingFilter, setFindingFilter] = useState<FindingFilter>("all");
  const [severityFilter, setSeverityFilter] = useState<FindingSeverity | null>(
    null,
  );

  const allCards = useMemo(() => buildGroupedCards(), []);

  const filtered = useMemo(() => {
    let result = allCards;
    if (findingFilter === "violations") {
      result = result.filter((c) => c.kind === "violation");
    } else if (findingFilter === "gaps") {
      result = result.filter((c) => c.kind === "gap");
    }
    if (severityFilter) {
      result = result.filter((c) => c.severity === severityFilter);
    }
    return result;
  }, [allCards, findingFilter, severityFilter]);

  const severityOptions: { label: string; value: FindingSeverity }[] = [
    { label: "Critical", value: "critical" },
    { label: "High", value: "high" },
    { label: "Medium", value: "medium" },
    { label: "Low", value: "low" },
  ];

  if (allCards.length === 0) {
    return <Text type="secondary">No findings detected.</Text>;
  }

  return (
    <Flex vertical gap={16}>
      {/* Toolbar */}
      <Flex justify="space-between" align="center">
        <Segmented
          size="small"
          value={findingFilter}
          onChange={(v) => setFindingFilter(v as FindingFilter)}
          options={[
            { label: "All", value: "all" },
            { label: "Violations", value: "violations" },
            { label: "Gaps", value: "gaps" },
          ]}
        />
        <Select
          placeholder="Severity"
          allowClear
          size="small"
          style={{ width: 140 }}
          options={severityOptions}
          value={severityFilter}
          onChange={(v) => setSeverityFilter(v ?? null)}
        />
      </Flex>

      {/* Card grid */}
      {filtered.length > 0 ? (
        <Row gutter={[16, 16]}>
          {filtered.map((card) => (
            <Col
              key={
                card.kind === "violation"
                  ? `v-${card.purpose}`
                  : `g-${card.consumerName}`
              }
              xs={24}
              sm={12}
              lg={8}
            >
              {card.kind === "violation" ? (
                <PolicyViolationCard group={card} />
              ) : (
                <ConsumerGapCard group={card} />
              )}
            </Col>
          ))}
        </Row>
      ) : (
        <Flex justify="center" className="py-8">
          <Text type="secondary">No findings match the current filters.</Text>
        </Flex>
      )}
    </Flex>
  );
};
