import { Card, Divider, Flex, Icons, Input, Select, SparkleIcon, Tag, Text, Title } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import Link from "next/link";
import { useMemo, useState } from "react";

import { DATA_CONSUMERS_ROUTE } from "~/features/common/nav/routes";

import type { FindingSeverity } from "../access-control/mockData";
import { MOCK_QUERY_LOG, MOCK_VIOLATION_CARDS } from "../access-control/mockData";

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

const formatRelativeTime = (isoStr: string): string => {
  const diffMs = Date.now() - new Date(isoStr).getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHrs = Math.floor(diffMins / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  const diffDays = Math.floor(diffHrs / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return new Date(isoStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
};

const formatTimestamp = (isoStr: string): string =>
  new Date(isoStr).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });

// ─── Mock policy metadata ────────────────────────────────────────────────────

const POLICY_DETAILS: Record<
  string,
  { description: string; dataCategories: string[]; scope: string }
> = {
  "Campaign targeting": {
    description:
      "Controls access to data used for targeted advertising campaigns. Only authorized marketing systems may query user behavior and transaction data for campaign purposes.",
    dataCategories: ["user.behavior", "user.financial", "user.contact"],
    scope: "payment_transactions, user_sessions, identity_documents, ad_impressions",
  },
  "Audience segmentation": {
    description:
      "Governs access to user profile and behavioral data for building audience segments. Restricted to approved analytics consumers.",
    dataCategories: ["user.behavior", "user.demographic"],
    scope: "user_profiles, behavior_events",
  },
  "Ticket resolution": {
    description:
      "Limits access to customer PII and support data to authorized support and success teams resolving active tickets.",
    dataCategories: ["user.contact", "user.name", "user.content"],
    scope: "customer_pii, support_cases, customer_feedback",
  },
};

// ─── Component ───────────────────────────────────────────────────────────────

interface PolicyDrillDownProps {
  policyName: string;
  onBack: () => void;
}

const PolicyDrillDown = ({ policyName }: PolicyDrillDownProps) => {
  const [consumerFilter, setConsumerFilter] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const violations = useMemo(
    () =>
      MOCK_VIOLATION_CARDS.filter((v) => v.purpose === policyName).sort(
        (a, b) =>
          SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity] ||
          b.last_seen.localeCompare(a.last_seen),
      ),
    [policyName],
  );

  const queryLog = useMemo(() => {
    let result = MOCK_QUERY_LOG.filter((q) => q.policy === policyName).sort(
      (a, b) => b.timestamp.localeCompare(a.timestamp),
    );
    if (consumerFilter) {
      result = result.filter((q) => q.consumer_name === consumerFilter);
    }
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (entry) =>
          entry.table_accessed.toLowerCase().includes(q) ||
          entry.consumer_name.toLowerCase().includes(q) ||
          entry.query_type.toLowerCase().includes(q),
      );
    }
    return result;
  }, [policyName, consumerFilter, search]);

  const consumers = useMemo(() => {
    const map = new Map<
      string,
      { id: string; name: string; queryCount: number; rowsAccessed: number; lastSeen: string; severity: FindingSeverity }
    >();
    for (const v of violations) {
      const queries = MOCK_QUERY_LOG.filter(
        (q) => q.policy === policyName && q.consumer_id === v.consumer_id,
      );
      const totalRows = queries.reduce((s, q) => s + q.rows_accessed, 0);
      map.set(v.consumer_id, {
        id: v.consumer_id,
        name: v.consumer_name,
        queryCount: v.query_count,
        rowsAccessed: totalRows,
        lastSeen: v.last_seen,
        severity: v.severity,
      });
    }
    return [...map.values()].sort(
      (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity],
    );
  }, [violations, policyName]);

  const consumerOptions = consumers.map((c) => ({
    label: c.name,
    value: c.name,
  }));

  const totalQueries = violations.reduce((s, v) => s + v.query_count, 0);
  const highestSeverity = violations.reduce(
    (best, v) =>
      SEVERITY_ORDER[v.severity] < SEVERITY_ORDER[best] ? v.severity : best,
    "low" as FindingSeverity,
  );

  const details = POLICY_DETAILS[policyName] ?? {
    description: "No description available.",
    dataCategories: [],
    scope: "—",
  };

  return (
    <Flex vertical gap={20}>
      {/* Policy detail header */}
      <div
        className="rounded-lg px-5 py-4"
        style={{ backgroundColor: palette.FIDESUI_BG_DEFAULT }}
      >
        <Flex vertical gap={8}>
          <Flex align="center" gap={8}>
            <div
              className="size-2.5 rounded-full"
              style={{ backgroundColor: SEVERITY_COLORS[highestSeverity] }}
            />
            <Title level={4} className="!mb-0">
              {policyName}
            </Title>
          </Flex>
          <Text type="secondary" className="text-sm leading-relaxed">
            {details.description}
          </Text>
          <Flex gap={24} className="mt-1">
            <Flex vertical gap={2}>
              <Text type="secondary" className="text-[10px] uppercase tracking-wider">
                Data categories
              </Text>
              <Flex gap={4}>
                {details.dataCategories.map((c) => (
                  <Tag key={c} bordered={false} className="!m-0 !text-[10px]">
                    {c}
                  </Tag>
                ))}
              </Flex>
            </Flex>
            <div
              className="shrink-0 self-stretch border-l border-solid"
              style={{ borderColor: palette.FIDESUI_NEUTRAL_100 }}
            />
            <Flex vertical gap={2}>
              <Text type="secondary" className="text-[10px] uppercase tracking-wider">
                Scope
              </Text>
              <Text className="text-xs">{details.scope}</Text>
            </Flex>
          </Flex>
        </Flex>
      </div>

      {/* Stats bar */}
      <Flex gap={24} align="center" className="py-1">
        <Flex vertical>
          <Text strong className="text-sm">
            {consumers.length}
          </Text>
          <Text type="secondary" className="text-xs">
            {consumers.length === 1 ? "Consumer" : "Consumers"} violating
          </Text>
        </Flex>
        <div
          className="shrink-0 self-stretch border-l border-solid"
          style={{ borderColor: palette.FIDESUI_NEUTRAL_100 }}
        />
        <Flex vertical>
          <Text strong className="text-sm">
            {totalQueries.toLocaleString()}
          </Text>
          <Text type="secondary" className="text-xs">
            Total queries
          </Text>
        </Flex>
        <div
          className="shrink-0 self-stretch border-l border-solid"
          style={{ borderColor: palette.FIDESUI_NEUTRAL_100 }}
        />
        <Flex vertical>
          <Text strong className="text-sm">
            {queryLog.reduce((s, q) => s + q.rows_accessed, 0).toLocaleString()}
          </Text>
          <Text type="secondary" className="text-xs">
            Rows accessed
          </Text>
        </Flex>
      </Flex>

      <Divider className="!my-0" />

      {/* Consumer cards */}
      <Flex vertical gap={8}>
        <Text strong className="text-xs">
          Consumers
        </Text>
        <Flex gap={12}>
          {consumers.map((c) => (
            <Card
              key={c.id}
              size="small"
              className="cursor-pointer transition-shadow hover:shadow-[0_2px_6px_rgba(0,0,0,0.08)]"
              style={{
                backgroundColor:
                  consumerFilter === c.name ? palette.FIDESUI_BG_DEFAULT : "#fafafa",
                borderColor:
                  consumerFilter === c.name
                    ? palette.FIDESUI_MINOS
                    : palette.FIDESUI_NEUTRAL_100,
                borderWidth: consumerFilter === c.name ? 2 : 1,
                minWidth: 180,
              }}
              onClick={() =>
                setConsumerFilter((prev) =>
                  prev === c.name ? null : c.name,
                )
              }
            >
              <Flex vertical gap={4}>
                <Flex justify="space-between" align="center">
                  <Link
                    href={`${DATA_CONSUMERS_ROUTE}/${c.id}`}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Text
                      strong
                      className="text-xs"
                      style={{ color: palette.FIDESUI_MINOS }}
                    >
                      {c.name}
                    </Text>
                  </Link>
                  <div
                    className="size-2 rounded-full"
                    style={{ backgroundColor: SEVERITY_COLORS[c.severity] }}
                  />
                </Flex>
                <Flex justify="space-between">
                  <Text type="secondary" className="text-[10px]">
                    {c.queryCount.toLocaleString()} queries
                  </Text>
                  <Text type="secondary" className="text-[10px]">
                    {c.rowsAccessed.toLocaleString()} rows
                  </Text>
                </Flex>
                <Text type="secondary" className="text-[10px]">
                  Last seen {formatRelativeTime(c.lastSeen)}
                </Text>
              </Flex>
            </Card>
          ))}
        </Flex>
      </Flex>

      <Divider className="!my-0" />

      {/* Query log */}
      <Flex vertical gap={8}>
        <Flex justify="space-between" align="center">
          <Text strong className="text-xs">
            Query log
            {consumerFilter && (
              <Text type="secondary" className="ml-2 text-xs font-normal">
                filtered to {consumerFilter}
              </Text>
            )}
          </Text>
          <Flex gap={8} align="center">
            <Input
              placeholder="Search queries..."
              value={search}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setSearch(e.target.value)
              }
              allowClear
              size="small"
              style={{ width: 200 }}
            />
            <Select
              placeholder="Consumer"
              allowClear
              size="small"
              style={{ width: 180 }}
              options={consumerOptions}
              value={consumerFilter}
              onChange={(v) => setConsumerFilter(v ?? null)}
            />
          </Flex>
        </Flex>

        {/* Table header */}
        <Flex
          className="border-b border-solid px-3 py-2"
          align="center"
          style={{
            backgroundColor: palette.FIDESUI_CORINTH,
            borderColor: palette.FIDESUI_NEUTRAL_100,
          }}
        >
          <Text strong className="w-[4%] text-xs">
            Match
          </Text>
          <Text strong className="w-[15%] text-xs">
            Consumer
          </Text>
          <Text strong className="w-[14%] text-xs">
            Table
          </Text>
          <Text strong className="w-[8%] text-xs">
            Type
          </Text>
          <Text strong className="w-[17%] text-xs">
            Inferred purpose
          </Text>
          <Text strong className="w-[10%] text-right text-xs">
            Rows
          </Text>
          <Text strong className="w-[14%] text-xs">
            Timestamp
          </Text>
          <Text strong className="w-[18%] text-right text-xs">
            Action
          </Text>
        </Flex>

        {/* Rows */}
        {queryLog.map((entry) => (
          <Flex
            key={entry.id}
            align="center"
            className="border-b border-solid px-3 py-2.5"
            style={{
              borderColor: palette.FIDESUI_NEUTRAL_75,
              backgroundColor: entry.matches_policy
                ? undefined
                : "#fff7e6",
            }}
          >
            <div className="w-[4%]">
              {entry.matches_policy ? (
                <Icons.Checkmark
                  size={14}
                  style={{ color: palette.FIDESUI_SUCCESS }}
                />
              ) : (
                <Icons.Close
                  size={14}
                  style={{ color: palette.FIDESUI_ERROR }}
                />
              )}
            </div>
            <div className="w-[15%]">
              <Link href={`${DATA_CONSUMERS_ROUTE}/${entry.consumer_id}`}>
                <Text
                  className="text-xs"
                  style={{ color: palette.FIDESUI_MINOS }}
                >
                  {entry.consumer_name}
                </Text>
              </Link>
            </div>
            <Text className="w-[14%] font-mono text-xs">
              {entry.table_accessed}
            </Text>
            <div className="w-[8%]">
              <Tag bordered={false} className="!m-0 !text-[10px]">
                {entry.query_type}
              </Tag>
            </div>
            <div className="w-[17%]">
              <Flex align="center" gap={4}>
                <SparkleIcon size={11} className="shrink-0" />
                <Text
                  className="text-xs"
                  style={
                    entry.matches_policy
                      ? undefined
                      : { color: palette.FIDESUI_ERROR }
                  }
                >
                  {entry.inferred_purpose}
                </Text>
                <Text type="secondary" className="text-[9px]">
                  {entry.inference_confidence}%
                </Text>
              </Flex>
            </div>
            <Text type="secondary" className="w-[10%] text-right text-xs">
              {entry.rows_accessed.toLocaleString()}
            </Text>
            <Text type="secondary" className="w-[14%] text-xs">
              {formatTimestamp(entry.timestamp)}
            </Text>
            <div className="w-[18%] text-right">
              <Link href={`${DATA_CONSUMERS_ROUTE}/${entry.consumer_id}`}>
                <Text
                  className="text-xs"
                  style={{ color: palette.FIDESUI_MINOS }}
                >
                  View consumer →
                </Text>
              </Link>
            </div>
          </Flex>
        ))}

        {queryLog.length === 0 && (
          <Flex justify="center" className="py-8">
            <Text type="secondary">No queries match the current filters.</Text>
          </Flex>
        )}
      </Flex>
    </Flex>
  );
};

export default PolicyDrillDown;
