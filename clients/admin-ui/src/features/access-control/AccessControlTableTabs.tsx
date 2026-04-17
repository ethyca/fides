import { Flex, Segmented, Select, Table, Tabs, Text, Title } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { parseAsString, parseAsStringLiteral, useQueryState } from "nuqs";
import { useCallback, useMemo, useState } from "react";

import { MOCK_DATA_CONSUMERS } from "~/features/data-consumers/mockData";

import { MOCK_UNRESOLVED_IDENTITIES } from "./mockData";
import { RequestLogTable } from "./RequestLogTable";
import { consumerColumns, formatRelativeTime, SummaryCards } from "./SummaryCards";
import type { PolicyViolationLog } from "./types";
import { ViolationDetailDrawer } from "./ViolationDetailDrawer";

type TableTab = "summary" | "log" | "consumers";
type ConsumerView = "all" | "registered" | "unresolved";

// ─── Consumers tab content ───────────────────────────────────────────────────

const registeredConsumerColumns = [
  {
    title: "Name",
    dataIndex: "name",
    render: (name: string) => <Text className="text-xs">{name}</Text>,
  },
  {
    title: "Type",
    dataIndex: "type",
    render: (type: string) => (
      <Text type="secondary" className="text-xs capitalize">
        {type.replace("_", " ")}
      </Text>
    ),
  },
  {
    title: "Identifier",
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
    title: "Purposes",
    dataIndex: "purposes",
    render: (purposes: string[]) =>
      purposes.length > 0 ? (
        <Text type="secondary" className="text-xs">
          {purposes.join(", ")}
        </Text>
      ) : (
        <Text type="secondary" className="text-xs">
          —
        </Text>
      ),
  },
  {
    title: "Findings",
    dataIndex: "findingsCount",
    align: "right" as const,
    render: (count: number) => (
      <Text
        className="text-xs"
        style={count > 0 ? { color: palette.FIDESUI_ERROR } : undefined}
        type={count === 0 ? "secondary" : undefined}
      >
        {count}
      </Text>
    ),
  },
];

const unresolvedColumns = [
  ...consumerColumns.slice(0, -1),
  {
    title: "Last seen",
    dataIndex: "last_seen",
    render: (ts: string) => formatRelativeTime(ts),
  },
  consumerColumns[consumerColumns.length - 1],
];

const ConsumersContent = ({
  defaultFilter,
}: {
  defaultFilter?: ConsumerView;
}) => {
  const [view, setView] = useState<ConsumerView>(defaultFilter ?? "all");

  const registered = MOCK_DATA_CONSUMERS;
  const unresolved = MOCK_UNRESOLVED_IDENTITIES;

  return (
    <Flex vertical gap={16}>
      <Flex justify="space-between" align="center">
        <Flex vertical>
          <Title level={5} className="!mb-0">
            Consumers
          </Title>
          <Text type="secondary" className="text-xs">
            Registered consumers and unresolved identities observed in query
            logs.
          </Text>
        </Flex>
        <Segmented
          size="small"
          value={view}
          onChange={(v) => setView(v as ConsumerView)}
          options={[
            { label: `All (${registered.length + unresolved.length})`, value: "all" },
            { label: `Registered (${registered.length})`, value: "registered" },
            { label: `Unresolved (${unresolved.length})`, value: "unresolved" },
          ]}
        />
      </Flex>

      {(view === "all" || view === "registered") && registered.length > 0 && (
        <div>
          {view === "all" && (
            <Text strong className="mb-2 block text-xs">
              Registered consumers
            </Text>
          )}
          <Table
            columns={registeredConsumerColumns}
            dataSource={registered}
            rowKey="id"
            size="small"
            pagination={false}
            bordered={false}
          />
        </div>
      )}

      {(view === "all" || view === "unresolved") && unresolved.length > 0 && (
        <div>
          {view === "all" && (
            <Text strong className="mb-2 block text-xs">
              Unresolved identities
            </Text>
          )}
          <Table
            columns={unresolvedColumns}
            dataSource={unresolved}
            rowKey="id"
            size="small"
            pagination={false}
            bordered={false}
          />
        </div>
      )}
    </Flex>
  );
};

// ─── Main tabs ───────────────────────────────────────────────────────────────

export const AccessControlTableTabs = () => {
  const [activeTab, setActiveTab] = useQueryState(
    "tab",
    parseAsStringLiteral(["summary", "log", "consumers"] as const)
      .withDefault("summary")
      .withOptions({ history: "push" }),
  );

  const [selectedViolationId, setSelectedViolationId] = useQueryState(
    "violationId",
    parseAsString.withOptions({ history: "push" }),
  );

  const consumerDefaultFilter: ConsumerView | undefined =
    MOCK_UNRESOLVED_IDENTITIES.length > 0 ? "unresolved" : undefined;

  const handleLogRowClick = useCallback(
    (record: PolicyViolationLog) => {
      setSelectedViolationId(record.id);
    },
    [setSelectedViolationId],
  );

  const items = useMemo(
    () => [
      {
        key: "summary",
        label: "Summary",
        children: <SummaryCards />,
      },
      {
        key: "log",
        label: "Log",
        children: <RequestLogTable onRowClick={handleLogRowClick} />,
      },
      {
        key: "consumers",
        label: "Consumers",
        children: <ConsumersContent defaultFilter={consumerDefaultFilter} />,
      },
    ],
    [handleLogRowClick, consumerDefaultFilter],
  );

  return (
    <>
      <Tabs
        activeKey={activeTab}
        onChange={(key) => setActiveTab(key as TableTab)}
        items={items}
      />
      <ViolationDetailDrawer
        violationId={selectedViolationId}
        open={!!selectedViolationId}
        onClose={() => setSelectedViolationId(null)}
      />
    </>
  );
};
