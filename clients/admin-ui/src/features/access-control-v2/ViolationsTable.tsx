import { Button, Flex, Input, Segmented, Select, SparkleIcon, Text, useMessage } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { DATA_CONSUMERS_ROUTE, DATA_PURPOSES_ROUTE } from "~/features/common/nav/routes";

import type { FindingSeverity } from "../access-control/mockData";
import {
  MOCK_GAP_CARDS,
  MOCK_UNRESOLVED_IDENTITIES,
  MOCK_VIOLATION_CARDS,
} from "../access-control/mockData";

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

const getRiskLevel = (
  queryCount: number,
  datasetCount: number,
): { label: string; color: string } => {
  if (queryCount > 2000 || datasetCount > 4)
    return { label: "High", color: palette.FIDESUI_ERROR };
  if (queryCount > 500 || datasetCount > 2)
    return { label: "Medium", color: palette.FIDESUI_WARNING };
  return { label: "Low", color: palette.FIDESUI_MINOS };
};

// ─── Grouped types ───────────────────────────────────────────────────────────

interface PolicyGroup {
  policy: string;
  severity: FindingSeverity;
  consumerCount: number;
  consumers: string[];
  totalQueries: number;
  lastSeen: string;
}

interface ConsumerGapGroup {
  consumerName: string;
  consumerId: string | null;
  severity: FindingSeverity;
  datasetCount: number;
  datasets: string[];
  totalQueries: number;
  lastSeen: string;
  inferred_purpose: string;
  inference_confidence: number;
}

function buildPolicyGroups(): PolicyGroup[] {
  const map = new Map<string, typeof MOCK_VIOLATION_CARDS>();
  for (const v of MOCK_VIOLATION_CARDS) {
    const existing = map.get(v.purpose) ?? [];
    existing.push(v);
    map.set(v.purpose, existing);
  }
  return [...map.entries()]
    .map(([policy, violations]) => {
      const consumerNames = [
        ...new Set(violations.map((v) => v.consumer_name)),
      ];
      const highestSeverity = violations.reduce(
        (best, v) =>
          SEVERITY_ORDER[v.severity] < SEVERITY_ORDER[best]
            ? v.severity
            : best,
        "low" as FindingSeverity,
      );
      return {
        policy,
        severity: highestSeverity,
        consumerCount: consumerNames.length,
        consumers: consumerNames,
        totalQueries: violations.reduce((s, v) => s + v.query_count, 0),
        lastSeen: violations.reduce(
          (latest, v) => (v.last_seen > latest ? v.last_seen : latest),
          "",
        ),
      };
    })
    .sort(
      (a, b) =>
        SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity] ||
        b.lastSeen.localeCompare(a.lastSeen),
    );
}

function buildConsumerGapGroups(): ConsumerGapGroup[] {
  const map = new Map<string, typeof MOCK_GAP_CARDS>();
  for (const g of MOCK_GAP_CARDS) {
    const key = g.consumer_id ?? g.consumer_name;
    const existing = map.get(key) ?? [];
    existing.push(g);
    map.set(key, existing);
  }
  return [...map.entries()]
    .map(([, gaps]) => {
      const highestSeverity = gaps.reduce(
        (best, g) =>
          SEVERITY_ORDER[g.severity] < SEVERITY_ORDER[best]
            ? g.severity
            : best,
        "low" as FindingSeverity,
      );
      const bestInference = gaps.reduce((best, g) =>
        g.inference_confidence > best.inference_confidence ? g : best,
      );
      return {
        consumerName: gaps[0].consumer_name,
        consumerId: gaps[0].consumer_id,
        severity: highestSeverity,
        datasetCount: gaps.length,
        datasets: gaps.map((g) => g.dataset),
        totalQueries: gaps.reduce((s, g) => s + g.query_count, 0),
        lastSeen: gaps.reduce(
          (latest, g) => (g.last_seen > latest ? g.last_seen : latest),
          "",
        ),
        inferred_purpose: bestInference.inferred_purpose,
        inference_confidence: bestInference.inference_confidence,
      };
    })
    .sort(
      (a, b) =>
        SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity] ||
        b.lastSeen.localeCompare(a.lastSeen),
    );
}

// ─── Component ───────────────────────────────────────────────────────────────

export type TableTab = "violations" | "ungoverned" | "unknown";

interface ViolationsTableProps {
  activeTab?: TableTab;
  onInvestigate?: (policyName: string) => void;
}

const ViolationsTable = ({ activeTab, onInvestigate }: ViolationsTableProps) => {
  const msg = useMessage();
  const [tab, setTab] = useState<TableTab>(activeTab ?? "violations");
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState<FindingSeverity | null>(
    null,
  );
  const [consumerFilter, setConsumerFilter] = useState<string | null>(null);

  // Sync controlled tab from parent
  useEffect(() => {
    if (activeTab) setTab(activeTab);
  }, [activeTab]);

  const policyGroups = useMemo(() => {
    let result = buildPolicyGroups();
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (g) =>
          g.policy.toLowerCase().includes(q) ||
          g.consumers.some((c) => c.toLowerCase().includes(q)),
      );
    }
    if (severityFilter) {
      result = result.filter((g) => g.severity === severityFilter);
    }
    if (consumerFilter) {
      result = result.filter((g) =>
        g.consumers.some((c) => c === consumerFilter),
      );
    }
    return result;
  }, [search, severityFilter, consumerFilter]);

  const gapGroups = useMemo(() => {
    let result = buildConsumerGapGroups();
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (g) =>
          g.consumerName.toLowerCase().includes(q) ||
          g.datasets.some((d) => d.toLowerCase().includes(q)),
      );
    }
    if (severityFilter) {
      result = result.filter((g) => g.severity === severityFilter);
    }
    if (consumerFilter) {
      result = result.filter((g) => g.consumerName === consumerFilter);
    }
    return result;
  }, [search, severityFilter, consumerFilter]);

  const identities = useMemo(() => {
    let result = [...MOCK_UNRESOLVED_IDENTITIES];
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (i) =>
          i.identifier.toLowerCase().includes(q) ||
          i.datasets.some((d) => d.toLowerCase().includes(q)),
      );
    }
    return result;
  }, [search]);

  const policyCount = buildPolicyGroups().length;
  const gapConsumerCount = buildConsumerGapGroups().length;
  const unknownCount = MOCK_UNRESOLVED_IDENTITIES.length;

  const consumerOptions = useMemo(() => {
    const names = new Set<string>();
    MOCK_VIOLATION_CARDS.forEach((v) => names.add(v.consumer_name));
    MOCK_GAP_CARDS.forEach((g) => names.add(g.consumer_name));
    return [...names].sort().map((n) => ({ label: n, value: n }));
  }, []);

  const severityOptions: { label: string; value: FindingSeverity }[] = [
    { label: "Critical", value: "critical" },
    { label: "High", value: "high" },
    { label: "Medium", value: "medium" },
    { label: "Low", value: "low" },
  ];

  return (
    <Flex vertical gap={12}>
      {/* Toolbar */}
      <Flex justify="space-between" align="center">
        <Input
          placeholder="Search..."
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setSearch(e.target.value)
          }
          allowClear
          style={{ width: 240 }}
        />
        <Flex gap={8} align="center">
          <Segmented
            value={tab}
            onChange={(v) => setTab(v as TableTab)}
            options={[
              {
                label: `Violations (${policyCount})`,
                value: "violations",
              },
              {
                label: `Gaps (${gapConsumerCount})`,
                value: "ungoverned",
              },
              {
                label: `Unknown identities (${unknownCount})`,
                value: "unknown",
              },
            ]}
          />
          {tab !== "unknown" && (
            <Select
              placeholder="Severity"
              allowClear
              style={{ width: 150 }}
              options={severityOptions}
              value={severityFilter}
              onChange={(v) => setSeverityFilter(v ?? null)}
            />
          )}
          {tab !== "unknown" && (
            <Select
              placeholder="Consumer"
              allowClear
              style={{ width: 180 }}
              options={consumerOptions}
              value={consumerFilter}
              onChange={(v) => setConsumerFilter(v ?? null)}
            />
          )}
        </Flex>
      </Flex>

      {/* ─── Violations: grouped by policy ──────────────────────────────── */}
      {tab === "violations" && (
        <>
          <Flex
            className="border-b border-solid px-4 py-2"
            align="center"
            style={{
              backgroundColor: palette.FIDESUI_CORINTH,
              borderColor: palette.FIDESUI_NEUTRAL_100,
            }}
          >
            <Text strong className="w-[12%] text-xs">Severity</Text>
            <Text strong className="w-[22%] text-xs">Policy</Text>
            <Text strong className="w-[24%] text-xs">Consumers</Text>
            <Text strong className="w-[14%] text-xs">Queries</Text>
            <Text strong className="w-[14%] text-xs">Last seen</Text>
            <Text strong className="w-[14%] text-xs">Action</Text>
          </Flex>

          {policyGroups.map((group) => (
            <Flex
              key={group.policy}
              align="center"
              className="border-b border-solid px-4 py-3"
              style={{ borderColor: palette.FIDESUI_NEUTRAL_75 }}
            >
              <div className="w-[12%]">
                <Flex align="center" gap={6}>
                  <div
                    className="size-2 shrink-0 rounded-full"
                    style={{ backgroundColor: SEVERITY_COLORS[group.severity] }}
                  />
                  <Text className="text-xs capitalize">{group.severity}</Text>
                </Flex>
              </div>
              <Text strong className="w-[22%] text-xs">{group.policy}</Text>
              <div className="w-[24%]">
                <Text type="secondary" className="text-xs">
                  {group.consumers.join(", ")}
                </Text>
                {group.consumerCount > 2 && (
                  <Text type="secondary" className="ml-1 text-[10px]">
                    ({group.consumerCount} total)
                  </Text>
                )}
              </div>
              <Text type="secondary" className="w-[14%] text-xs">
                {group.totalQueries.toLocaleString()}
              </Text>
              <Text type="secondary" className="w-[14%] text-xs">
                {formatRelativeTime(group.lastSeen)}
              </Text>
              <div className="w-[14%]">
                <Text
                  className="cursor-pointer text-xs"
                  style={{ color: palette.FIDESUI_MINOS }}
                  onClick={() => onInvestigate?.(group.policy)}
                >
                  Investigate →
                </Text>
              </div>
            </Flex>
          ))}

          {policyGroups.length === 0 && (
            <Flex justify="center" className="py-8">
              <Text type="secondary">No violations match the current filters.</Text>
            </Flex>
          )}
        </>
      )}

      {/* ─── Gaps: grouped by consumer ──────────────────────────────────── */}
      {tab === "ungoverned" && (
        <>
          <Flex
            className="border-b border-solid px-4 py-2"
            align="center"
            style={{
              backgroundColor: palette.FIDESUI_CORINTH,
              borderColor: palette.FIDESUI_NEUTRAL_100,
            }}
          >
            <Text strong className="w-[10%] text-xs">Severity</Text>
            <Text strong className="w-[16%] text-xs">Consumer</Text>
            <Text strong className="w-[18%] text-xs">Datasets</Text>
            <Text strong className="w-[18%] text-xs">Inferred purpose</Text>
            <Text strong className="w-[10%] text-xs">Queries</Text>
            <Text strong className="w-[12%] text-xs">Last seen</Text>
            <Text strong className="w-[16%] text-xs">Action</Text>
          </Flex>

          {gapGroups.map((group) => (
            <Flex
              key={group.consumerName}
              align="center"
              className="border-b border-solid px-4 py-3"
              style={{
                borderColor: palette.FIDESUI_NEUTRAL_75,
                ...(group.consumerId === null
                  ? { borderLeft: "2px dashed #faad14" }
                  : {}),
              }}
            >
              <div className="w-[10%]">
                <Flex align="center" gap={6}>
                  <div
                    className="size-2 shrink-0 rounded-full"
                    style={{ backgroundColor: SEVERITY_COLORS[group.severity] }}
                  />
                  <Text className="text-xs capitalize">{group.severity}</Text>
                </Flex>
              </div>
              <Text
                className="w-[16%] text-xs"
                type={group.consumerId === null ? "warning" : undefined}
              >
                {group.consumerName}
              </Text>
              <div className="w-[18%]">
                <Text type="secondary" className="text-xs">
                  {group.datasets.length <= 2
                    ? group.datasets.join(", ")
                    : `${group.datasets.slice(0, 2).join(", ")} +${group.datasets.length - 2} more`}
                </Text>
              </div>
              <div className="w-[18%]">
                <Flex align="center" gap={4}>
                  <SparkleIcon size={12} className="shrink-0" />
                  <Text className="text-xs">{group.inferred_purpose}</Text>
                  <Text type="secondary" className="text-[10px]">
                    {group.inference_confidence}%
                  </Text>
                </Flex>
              </div>
              <Text type="secondary" className="w-[10%] text-xs">
                {group.totalQueries.toLocaleString()}
              </Text>
              <Text type="secondary" className="w-[12%] text-xs">
                {formatRelativeTime(group.lastSeen)}
              </Text>
              <Flex className="w-[16%]" gap={6}>
                <Button
                  size="small"
                  type="primary"
                  className="!text-[10px]"
                  onClick={() =>
                    msg.success(
                      `Policy "${group.inferred_purpose}" confirmed for ${group.consumerName}`,
                    )
                  }
                >
                  Confirm
                </Button>
                <Button
                  size="small"
                  type="text"
                  className="!text-[10px]"
                  onClick={() =>
                    msg.info(`Inference rejected for ${group.consumerName}`)
                  }
                >
                  Reject
                </Button>
              </Flex>
            </Flex>
          ))}

          {gapGroups.length === 0 && (
            <Flex justify="center" className="py-8">
              <Text type="secondary">No ungoverned access found.</Text>
            </Flex>
          )}
        </>
      )}

      {/* ─── Unknown consumers ──────────────────────────────────────────── */}
      {tab === "unknown" && (
        <>
          <Flex
            className="border-b border-solid px-4 py-2"
            align="center"
            style={{
              backgroundColor: palette.FIDESUI_CORINTH,
              borderColor: palette.FIDESUI_NEUTRAL_100,
            }}
          >
            <Text strong className="w-[20%] text-xs">Identity</Text>
            <Text strong className="w-[14%] text-xs">Inferred type</Text>
            <Text strong className="w-[14%] text-xs">Suggested purpose</Text>
            <Text strong className="w-[14%] text-xs">Data accessed</Text>
            <Text strong className="w-[10%] text-xs">Queries</Text>
            <Text strong className="w-[8%] text-xs">Risk</Text>
            <Text strong className="w-[20%] text-xs">Actions</Text>
          </Flex>

          {identities.map((identity) => {
            const risk = getRiskLevel(
              identity.query_count,
              identity.datasets.length,
            );
            const datasetsDisplay =
              identity.datasets.length <= 2
                ? identity.datasets.join(", ")
                : `${identity.datasets.slice(0, 2).join(", ")} +${identity.datasets.length - 2} more`;

            return (
              <Flex
                key={identity.id}
                align="center"
                className="border-b border-solid px-4 py-2.5"
                style={{ borderColor: palette.FIDESUI_NEUTRAL_75 }}
              >
                <Text
                  className="w-[20%] font-mono text-xs"
                  ellipsis={{ tooltip: identity.identifier }}
                >
                  {identity.identifier}
                </Text>
                <div className="w-[14%]">
                  <Flex align="center" gap={4}>
                    <SparkleIcon size={12} className="shrink-0" />
                    <Text className="text-xs">{identity.inferred_type}</Text>
                  </Flex>
                  <Text type="secondary" className="text-[10px]">
                    {identity.inference_confidence}% confidence
                  </Text>
                </div>
                <div className="w-[14%]">
                  <Text className="text-xs">{identity.inferred_purpose}</Text>
                </div>
                <Text type="secondary" className="w-[14%] text-xs">
                  {datasetsDisplay}
                </Text>
                <Text type="secondary" className="w-[10%] text-xs">
                  {identity.query_count.toLocaleString()}
                </Text>
                <div className="w-[8%]">
                  <Flex align="center" gap={4}>
                    <div
                      className="size-1.5 rounded-full"
                      style={{ backgroundColor: risk.color }}
                    />
                    <Text className="text-xs">{risk.label}</Text>
                  </Flex>
                </div>
                <Flex className="w-[20%]" gap={6}>
                  <Link href={DATA_CONSUMERS_ROUTE}>
                    <Button size="small" type="primary" className="!text-[10px]">
                      Register as {identity.inferred_type.toLowerCase()}
                    </Button>
                  </Link>
                  <Button size="small" className="!text-[10px]">
                    Map
                  </Button>
                </Flex>
              </Flex>
            );
          })}

          {identities.length === 0 && (
            <Flex justify="center" className="py-8">
              <Text type="secondary">No unknown consumers found.</Text>
            </Flex>
          )}
        </>
      )}
    </Flex>
  );
};

export default ViolationsTable;
