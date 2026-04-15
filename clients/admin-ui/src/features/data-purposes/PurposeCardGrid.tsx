import { Col, Divider, Flex, Icons, Input, Row, Segmented, Select, Text, Title } from "fidesui";
import { useMemo, useState } from "react";

import { MOCK_SYSTEM_ASSIGNMENTS } from "./mockData";
import PurposeCard from "./PurposeCard";
import PurposeNetworkView from "./PurposeNetworkView";
import { computeCategoryDrift, formatDataUse } from "./purposeUtils";
import type { DataPurpose, PurposeSummary } from "./types";

interface PurposeCardGridProps {
  purposes: DataPurpose[];
  summaries: PurposeSummary[];
}

const PurposeCardGrid = ({ purposes, summaries }: PurposeCardGridProps) => {
  const [viewMode, setViewMode] = useState<"grid" | "network">("grid");
  const [search, setSearch] = useState("");
  const [consumerFilter, setConsumerFilter] = useState<string | null>(null);
  const [dataUseFilter, setDataUseFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);

  const consumerOptions = useMemo(() => {
    const seen = new Set<string>();
    const options: { value: string; label: string }[] = [];
    Object.values(MOCK_SYSTEM_ASSIGNMENTS).forEach((assignments) => {
      assignments
        .filter((a) => a.assigned)
        .forEach((a) => {
          if (!seen.has(a.system_id)) {
            seen.add(a.system_id);
            options.push({ value: a.system_id, label: a.system_name });
          }
        });
    });
    return options.sort((a, b) => a.label.localeCompare(b.label));
  }, []);

  const dataUseOptions = useMemo(
    () =>
      [...new Set(purposes.map((p) => p.data_use))].map((du) => ({
        value: du,
        label: formatDataUse(du),
      })),
    [purposes],
  );

  const statusOptions = [
    { value: "drift", label: "Has risks" },
    { value: "compliant", label: "Compliant" },
    { value: "unknown", label: "Not scanned" },
  ];

  const categoryOptions = useMemo(() => {
    const all = new Set<string>();
    purposes.forEach((p) => p.data_categories.forEach((c) => all.add(c)));
    return Array.from(all)
      .sort()
      .map((c) => ({ value: c, label: c }));
  }, [purposes]);

  const filtered = useMemo(
    () =>
      purposes.filter((p) => {
        if (search && !p.name.toLowerCase().includes(search.toLowerCase()))
          return false;
        if (dataUseFilter && p.data_use !== dataUseFilter) return false;
        if (consumerFilter) {
          const assignments = MOCK_SYSTEM_ASSIGNMENTS[p.id] ?? [];
          if (
            !assignments.some(
              (a) => a.assigned && a.system_id === consumerFilter,
            )
          )
            return false;
        }
        if (statusFilter) {
          const drift = computeCategoryDrift(
            p.data_categories,
            p.detected_data_categories,
          );
          if (drift.status !== statusFilter) return false;
        }
        if (categoryFilter && !p.data_categories.includes(categoryFilter))
          return false;
        return true;
      }),
    [purposes, search, dataUseFilter, consumerFilter, statusFilter, categoryFilter],
  );

  const groups = useMemo(() => {
    const map: Record<string, typeof filtered> = {};
    filtered.forEach((p) => {
      if (!map[p.data_use]) {
        map[p.data_use] = [];
      }
      map[p.data_use].push(p);
    });
    return Object.entries(map);
  }, [filtered]);

  return (
    <div
      style={
        viewMode === "network"
          ? { flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }
          : undefined
      }
    >
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
            placeholder="Status"
            allowClear
            style={{ width: 160 }}
            options={statusOptions}
            value={statusFilter}
            onChange={(v) => setStatusFilter(v ?? null)}
          />
          <Select
            placeholder="Data category"
            allowClear
            style={{ width: 200 }}
            options={categoryOptions}
            value={categoryFilter}
            onChange={(v) => setCategoryFilter(v ?? null)}
          />
          <Select
            placeholder="Consumer"
            allowClear
            style={{ width: 200 }}
            options={consumerOptions}
            value={consumerFilter}
            onChange={(v) => setConsumerFilter(v ?? null)}
          />
          <Select
            placeholder="Data use"
            allowClear
            style={{ width: 200 }}
            options={dataUseOptions}
            value={dataUseFilter}
            onChange={(v) => setDataUseFilter(v ?? null)}
          />
          <Segmented
            value={viewMode}
            onChange={(v) => setViewMode(v as "grid" | "network")}
            options={[
              { label: <Icons.ShowDataCards size={16} />, value: "grid" },
              { label: <Icons.Fork size={16} />, value: "network" },
            ]}
          />
        </Flex>
      </Flex>
      {viewMode === "network" ? (
        <div style={{ flex: 1, minHeight: 0 }}>
          <PurposeNetworkView purposes={filtered} summaries={summaries} />
        </div>
      ) : null}
      {viewMode === "grid" && groups.map(([dataUse, items]) => {
        const groupSystemCount = items.reduce((sum, p) => {
          const s = summaries.find((su) => su.id === p.id);
          return sum + (s?.system_count ?? 0);
        }, 0);
        const groupDatasetCount = items.reduce((sum, p) => {
          const s = summaries.find((su) => su.id === p.id);
          return sum + (s?.dataset_count ?? 0);
        }, 0);

        return (
          <div key={dataUse} className="mb-8">
            <Flex gap="middle" align="center" className="mb-2">
              <Title level={4} className="!mb-0">
                {formatDataUse(dataUse)}
              </Title>
              <Text type="secondary" className="text-sm">
                {items.length}{" "}
                {items.length === 1 ? "purpose" : "purposes"} &middot;{" "}
                {groupSystemCount} systems &middot; {groupDatasetCount}{" "}
                datasets
              </Text>
            </Flex>
            <Divider className="!mt-0 mb-4" />
            <Row gutter={[16, 16]}>
              {items.map((p) => (
                <Col key={p.id} span={6}>
                  <PurposeCard
                    purpose={p}
                    summary={summaries.find((s) => s.id === p.id)}
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
