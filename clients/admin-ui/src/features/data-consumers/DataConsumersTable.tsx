import { Alert, Button, Empty, Flex, Select, Table } from "fidesui";
import { useRouter } from "next/router";
import { useMemo } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { ProgressCard } from "~/features/data-discovery-and-detection/action-center/ProgressCard/ProgressCard";

import {
  CONSUMER_TYPE_UI_LABELS,
  CONSUMER_TYPE_UI_OPTIONS,
  PLATFORM_OPTIONS,
  STATUS_FILTER_OPTIONS,
} from "./constants";
import type { ConsumerType, MockDataConsumer } from "./types";
import useDataConsumersTable from "./useDataConsumersTable";

const DataConsumersTable = () => {
  const router = useRouter();
  const {
    consumers: allConsumers,
    filteredConsumers,
    columns,
    metrics,
    unresolvedCount,
    search,
    setSearch,
    typeFilter,
    setTypeFilter,
    statusFilter,
    setStatusFilter,
    platformFilter,
    setPlatformFilter,
  } = useDataConsumersTable();

  const healthyCount =
    metrics.total - metrics.withViolations - metrics.noPurposes;
  const healthyPercent =
    metrics.total > 0 ? Math.round((healthyCount / metrics.total) * 100) : 0;

  const typeBreakdown = useMemo(() => {
    const counts: Record<string, number> = {};
    allConsumers.forEach((c) => {
      const label = CONSUMER_TYPE_UI_LABELS[c.type as ConsumerType] ?? c.type;
      counts[label] = (counts[label] || 0) + 1;
    });
    return Object.entries(counts).map(([label, count]) => ({
      label,
      value: Math.round((count / allConsumers.length) * 100),
    }));
  }, [allConsumers]);

  return (
    <Flex vertical gap="middle">
      {/* Unresolved accessors banner */}
      <Alert
        type="info"
        showIcon
        message={
          <Flex justify="space-between" align="center">
            <span>
              <strong>
                {unresolvedCount} unresolved accessors detected in query logs
              </strong>
              {" — identities seen accessing data with no matching consumer"}
            </span>
            <Button size="small">Resolve ↗</Button>
          </Flex>
        }
      />

      {/* Slim dashboard */}
      <ProgressCard
        title="Data Consumers"
        subtitle={`${metrics.total} consumers`}
        compact
        progress={{
          label: "Healthy consumers",
          percent: healthyPercent,
          numerator: healthyCount,
          denominator: metrics.total,
        }}
        numericStats={{
          label: "Summary",
          data: [
            { label: "total", count: metrics.total },
            { label: "with violations", count: metrics.withViolations },
            { label: "no purposes", count: metrics.noPurposes },
            { label: "AI agents", count: metrics.aiAgents },
          ],
        }}
        percentageStats={{
          label: "By type",
          data: typeBreakdown,
        }}
      />

      {/* Search and filters */}
      <Flex justify="space-between" align="center" gap="small">
        <DebouncedSearchInput
          value={search}
          onChange={setSearch}
          placeholder="Search consumers..."
        />
        <Flex gap="small">
          <Select
            allowClear
            placeholder="All types"
            options={CONSUMER_TYPE_UI_OPTIONS}
            value={typeFilter}
            onChange={setTypeFilter}
            style={{ width: 180 }}
          />
          <Select
            allowClear
            placeholder="All statuses"
            options={STATUS_FILTER_OPTIONS}
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 160 }}
          />
          <Select
            allowClear
            placeholder="All platforms"
            options={PLATFORM_OPTIONS}
            value={platformFilter}
            onChange={setPlatformFilter}
            style={{ width: 180 }}
          />
        </Flex>
      </Flex>

      {/* Table */}
      <Table<MockDataConsumer>
        dataSource={filteredConsumers}
        columns={columns}
        rowKey="id"
        size="small"
        pagination={{
          pageSize: 7,
          showTotal: (total, range) =>
            `Showing ${range[0]}-${range[1]} of ${total} consumers`,
        }}
        onRow={(record) => ({
          onClick: () => router.push(`/data-consumers/${record.id}`),
          style: { cursor: "pointer" },
        })}
        locale={{
          emptyText: (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="No data consumers match your filters"
              data-testid="no-results-notice"
            />
          ),
        }}
        data-testid="data-consumers-table"
      />
    </Flex>
  );
};

export default DataConsumersTable;
