import {
  Alert,
  antTheme,
  Button,
  Divider,
  Empty,
  Flex,
  Select,
  Table,
  Text,
} from "fidesui";
import { useRouter } from "next/router";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";

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
  const { token } = antTheme.useToken();
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
    metrics.total - metrics.withFindings - metrics.noPurposes;
  const healthyPct =
    metrics.total > 0 ? (healthyCount / metrics.total) * 100 : 0;
  const findingsPct =
    metrics.total > 0 ? (metrics.withFindings / metrics.total) * 100 : 0;
  const noPurposesPct =
    metrics.total > 0 ? (metrics.noPurposes / metrics.total) * 100 : 0;

  // Type breakdown for section 3
  const typeCounts: Partial<Record<ConsumerType, number>> = {};
  allConsumers.forEach((c) => {
    typeCounts[c.type] = (typeCounts[c.type] ?? 0) + 1;
  });
  const typeBreakdownText = Object.entries(typeCounts)
    .sort(([, a], [, b]) => b - a)
    .map(
      ([type, count]) =>
        `${count} ${(CONSUMER_TYPE_UI_LABELS[type as ConsumerType] ?? type).toLowerCase()}`,
    )
    .join(", ");

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
                {unresolvedCount} unresolved identities detected in query logs
              </strong>
              {" — identities seen accessing data with no matching consumer"}
            </span>
            <Button size="small">Resolve ↗</Button>
          </Flex>
        }
      />

      {/* Dashboard — SchemaExplorerDashboard layout */}
      <Flex className="w-full py-2" align="stretch">
        {/* Section 1: Health overview */}
        <Flex vertical gap={6} className="min-w-0 flex-1 pr-4">
          <Flex vertical>
            <Text
              strong
              className="text-2xl leading-none"
              style={{ fontVariantNumeric: "tabular-nums" }}
            >
              {metrics.total}
            </Text>
            <Text type="secondary" className="text-xs mt-0.5">
              consumers
            </Text>
          </Flex>

          {/* Stacked progress bar */}
          <div className="flex h-2 w-full overflow-hidden rounded-sm bg-gray-100">
            <div
              className="transition-all duration-1000 ease-in-out"
              style={{ width: `${healthyPct}%`, backgroundColor: token.colorSuccess }}
            />
            <div
              className="transition-all duration-1000 ease-in-out"
              style={{ width: `${findingsPct}%`, backgroundColor: token.colorError }}
            />
            <div
              className="transition-all duration-1000 ease-in-out"
              style={{ width: `${noPurposesPct}%`, backgroundColor: token.colorWarning }}
            />
          </div>

          {/* Legend */}
          <Flex gap="middle">
            <Flex align="center" gap={6}>
              <div
                className="h-2 w-2 flex-none rounded-full"
                style={{ backgroundColor: token.colorSuccess }}
              />
              <Text className="text-xs">{healthyCount} compliant</Text>
            </Flex>
            <Flex align="center" gap={6}>
              <div
                className="h-2 w-2 flex-none rounded-full"
                style={{ backgroundColor: token.colorError }}
              />
              <Text className="text-xs">{metrics.withFindings} non-compliant</Text>
            </Flex>
            <Flex align="center" gap={6}>
              <div
                className="h-2 w-2 flex-none rounded-full"
                style={{ backgroundColor: token.colorWarning }}
              />
              <Text className="text-xs">{metrics.noPurposes} needs setup</Text>
            </Flex>
          </Flex>
        </Flex>

        <Divider type="vertical" className="!mx-0 !h-auto self-stretch" />

        {/* Section 2: Findings breakdown */}
        <div className="min-w-0 flex-1 px-4">
          <Text strong className="mb-2 block text-xs">
            Findings
          </Text>
          <div className="mb-1">
            <Text type="secondary" className="text-xs">
              Policy deviations:{" "}
            </Text>
            <Text className="text-xs">{metrics.withFindings} consumers</Text>
          </div>
          <div>
            <Text type="secondary" className="text-xs">
              No coverage:{" "}
            </Text>
            <Text className="text-xs">{metrics.noPurposes} consumers</Text>
          </div>
        </div>

        <Divider type="vertical" className="!mx-0 !h-auto self-stretch" />

        {/* Section 3: Consumer breakdown */}
        <div className="min-w-0 flex-1 pl-4">
          <Text strong className="mb-2 block text-xs">
            Consumers by type
          </Text>
          <div className="truncate">
            <Text type="secondary" className="text-xs">
              {typeBreakdownText || "None"}
            </Text>
          </div>
        </div>
      </Flex>

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
