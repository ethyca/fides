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
  onCreatePurpose,
}: PurposeCardGridProps) => {
  const [search, setSearch] = useState("");
  const [consumerFilter, setConsumerFilter] = useState<string | null>(null);
  const [dataUseFilter, setDataUseFilter] = useState<string | null>(null);
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
    setDataUseFilter(null);
    setStatusFilter(null);
    setCategoryFilter(null);
  };

  const filtered = useMemo(
    () =>
      purposes.filter((p) => {
        if (search && !p.name.toLowerCase().includes(search.toLowerCase())) {
          return false;
        }
        if (dataUseFilter && p.data_use !== dataUseFilter) {
          return false;
        }
        if (consumerFilter) {
          const summary = summariesByKey.get(p.fides_key);
          if (
            !summary?.systems.some(
              (a) => a.assigned && a.system_id === consumerFilter,
            )
          ) {
            return false;
          }
        }
        if (statusFilter) {
          const summary = summariesByKey.get(p.fides_key);
          const drift = computeCategoryDrift(
            p.data_categories ?? [],
            summary?.detected_data_categories ?? [],
          );
          if (drift.status !== statusFilter) {
            return false;
          }
        }
        if (
          categoryFilter &&
          !(p.data_categories ?? []).includes(categoryFilter)
        ) {
          return false;
        }
        return true;
      }),
    [
      purposes,
      summariesByKey,
      search,
      dataUseFilter,
      consumerFilter,
      statusFilter,
      categoryFilter,
    ],
  );

  const groups = useMemo(() => {
    const map: Record<string, DataPurpose[]> = {};
    filtered.forEach((p) => {
      if (!map[p.data_use]) {
        map[p.data_use] = [];
      }
      map[p.data_use].push(p);
    });
    return Object.entries(map);
  }, [filtered]);

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
            onChange={(v) => setDataUseFilter(v ?? null)}
          />
        </Flex>
      </Flex>
      {filtered.length === 0 && emptyState}
      {filtered.length > 0 &&
        groups.map(([dataUse, items]) => {
          const groupSystemCount = items.reduce((sum, p) => {
            const s = summariesByKey.get(p.fides_key);
            return sum + (s?.system_count ?? 0);
          }, 0);
          const groupDatasetCount = items.reduce((sum, p) => {
            const s = summariesByKey.get(p.fides_key);
            return sum + (s?.dataset_count ?? 0);
          }, 0);

          return (
            <div key={dataUse} className="mb-8">
              <Flex gap="middle" align="center" className="mb-2">
                <Title level={4} className="!mb-0">
                  {formatDataUse(dataUse)}
                </Title>
                <Text type="secondary" className="text-sm">
                  {items.length} {items.length === 1 ? "purpose" : "purposes"}{" "}
                  &middot; {groupSystemCount} systems &middot;{" "}
                  {groupDatasetCount} datasets
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
          );
        })}
    </div>
  );
};

export default PurposeCardGrid;
