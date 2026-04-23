import {
  Button,
  Col,
  Divider,
  Flex,
  Input,
  Result,
  Row,
  Select,
  Text,
  Title,
} from "fidesui";
import { useMemo, useState } from "react";

import type { DataPurpose, PurposeSummary } from "./data-purpose.slice";
import PurposeCard from "./PurposeCard";
import { computeCategoryDrift, formatDataUse } from "./purposeUtils";

interface PurposeCardGridProps {
  purposes: DataPurpose[];
  summaries: PurposeSummary[];
  dataUseFilter: string | null;
  onDataUseFilterChange: (value: string | null) => void;
  onCreatePurpose: () => void;
}

const STATUS_OPTIONS = [
  { value: "drift", label: "Has risks" },
  { value: "compliant", label: "Compliant" },
  { value: "unknown", label: "Not scanned" },
];

const PurposeCardGrid = ({
  purposes,
  summaries,
  dataUseFilter,
  onDataUseFilterChange,
  onCreatePurpose,
}: PurposeCardGridProps) => {
  // `data_use` is filtered server-side via the list endpoint. The remaining
  // filters below run client-side because (a) `search` / `data_category` need
  // new params on `/data-purpose`, and (b) `consumer` / `status` depend on the
  // summaries endpoint, which is still mock-only. Move these server-side once
  // the real summaries endpoint lands and the list endpoint gains the params.
  const [search, setSearch] = useState("");
  const [consumerFilter, setConsumerFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);

  const summariesByKey = useMemo(
    () => new Map(summaries.map((s) => [s.fides_key, s])),
    [summaries],
  );

  const consumerOptions = useMemo(() => {
    const seen = new Set<string>();
    const options: { value: string; label: string }[] = [];
    summaries.forEach((summary) => {
      summary.systems
        .filter((a) => a.assigned)
        .forEach((a) => {
          if (!seen.has(a.system_id)) {
            seen.add(a.system_id);
            options.push({ value: a.system_id, label: a.system_name });
          }
        });
    });
    return options.sort((a, b) => a.label.localeCompare(b.label));
  }, [summaries]);

  const dataUseOptions = useMemo(
    () =>
      [...new Set(purposes.map((p) => p.data_use))].map((du) => ({
        value: du,
        label: formatDataUse(du),
      })),
    [purposes],
  );

  const categoryOptions = useMemo(() => {
    const all = new Set<string>();
    purposes.forEach((p) =>
      (p.data_categories ?? []).forEach((c) => all.add(c)),
    );
    return Array.from(all)
      .sort()
      .map((c) => ({ value: c, label: c }));
  }, [purposes]);

  const clearFilters = () => {
    setSearch("");
    setConsumerFilter(null);
    onDataUseFilterChange(null);
    setStatusFilter(null);
    setCategoryFilter(null);
  };

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    return purposes.filter((p) => {
      if (query && !p.name.toLowerCase().includes(query)) {
        return false;
      }
      if (
        categoryFilter &&
        !(p.data_categories ?? []).includes(categoryFilter)
      ) {
        return false;
      }
      if (!consumerFilter && !statusFilter) {
        return true;
      }
      const summary = summariesByKey.get(p.fides_key);
      if (
        consumerFilter &&
        !summary?.systems.some(
          (a) => a.assigned && a.system_id === consumerFilter,
        )
      ) {
        return false;
      }
      if (statusFilter) {
        const { status } = computeCategoryDrift(
          p.data_categories ?? [],
          summary?.detected_data_categories ?? [],
        );
        if (status !== statusFilter) {
          return false;
        }
      }
      return true;
    });
  }, [
    purposes,
    summariesByKey,
    search,
    consumerFilter,
    statusFilter,
    categoryFilter,
  ]);

  const groups = useMemo(() => {
    const byDataUse = new Map<
      string,
      { items: DataPurpose[]; systemCount: number; datasetCount: number }
    >();
    filtered.forEach((p) => {
      const summary = summariesByKey.get(p.fides_key);
      const group = byDataUse.get(p.data_use) ?? {
        items: [],
        systemCount: 0,
        datasetCount: 0,
      };
      group.items.push(p);
      group.systemCount += summary?.system_count ?? 0;
      group.datasetCount += summary?.dataset_count ?? 0;
      byDataUse.set(p.data_use, group);
    });
    return Array.from(byDataUse, ([dataUse, group]) => ({ dataUse, ...group }));
  }, [filtered, summariesByKey]);

  const emptyState =
    purposes.length === 0 ? (
      <Result
        status="info"
        title="No purposes yet"
        subTitle="Define your first purpose to start governing how data flows through your systems."
        extra={
          <Button type="primary" onClick={onCreatePurpose}>
            + New purpose
          </Button>
        }
      />
    ) : (
      <Result
        status="info"
        title="No purposes match your filters"
        subTitle="Try adjusting your search or clearing filters to see more results."
        extra={<Button onClick={clearFilters}>Clear filters</Button>}
      />
    );

  return (
    <div>
      <Flex justify="space-between" align="center" className="mb-4">
        <Input
          placeholder="Search purposes..."
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setSearch(e.target.value)
          }
          allowClear
          style={{ width: 280 }}
        />
        <Flex gap={8} align="center">
          <Select
            aria-label="Filter by status"
            placeholder="Status"
            allowClear
            style={{ width: 160 }}
            options={STATUS_OPTIONS}
            value={statusFilter}
            onChange={(v) => setStatusFilter(v ?? null)}
          />
          <Select
            aria-label="Filter by consumer"
            placeholder="Consumer"
            allowClear
            style={{ width: 200 }}
            options={consumerOptions}
            value={consumerFilter}
            onChange={(v) => setConsumerFilter(v ?? null)}
          />
          <Select
            aria-label="Filter by data category"
            placeholder="Data category"
            allowClear
            style={{ width: 200 }}
            options={categoryOptions}
            value={categoryFilter}
            onChange={(v) => setCategoryFilter(v ?? null)}
          />
          <Select
            aria-label="Filter by data use"
            placeholder="Data use"
            allowClear
            style={{ width: 200 }}
            options={dataUseOptions}
            value={dataUseFilter}
            onChange={(v) => onDataUseFilterChange(v ?? null)}
          />
        </Flex>
      </Flex>
      {filtered.length === 0 && emptyState}
      {filtered.length > 0 &&
        groups.map(({ dataUse, items, systemCount, datasetCount }) => (
          <div key={dataUse} className="mb-8">
            <Flex gap="middle" align="center" className="mb-2">
              <Title level={4} className="!mb-0">
                {formatDataUse(dataUse)}
              </Title>
              <Text type="secondary" className="text-sm">
                {items.length} {items.length === 1 ? "purpose" : "purposes"}{" "}
                &middot; {systemCount} systems &middot; {datasetCount} datasets
              </Text>
            </Flex>
            <Divider className="!mt-0 mb-4" />
            <Row gutter={[16, 16]}>
              {items.map((p) => (
                <Col key={p.id ?? p.fides_key} span={6}>
                  <PurposeCard
                    purpose={p}
                    summary={summariesByKey.get(p.fides_key)}
                  />
                </Col>
              ))}
            </Row>
          </div>
        ))}
    </div>
  );
};

export default PurposeCardGrid;
