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

import type { DataPurpose, PurposeSummary } from "./data-purpose.slice";
import PurposeCard from "./PurposeCard";
import { formatDataUse } from "./purposeUtils";
import usePurposeCardFilters from "./usePurposeCardFilters";

interface PurposeCardGridProps {
  purposes: DataPurpose[];
  summaries: PurposeSummary[];
  dataUseFilter: string | null;
  onDataUseFilterChange: (value: string | null) => void;
  searchQuery: string;
  onSearchChange: (value: string) => void;
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
  searchQuery,
  onSearchChange,
  onCreatePurpose,
}: PurposeCardGridProps) => {
  const {
    consumerFilter,
    setConsumerFilter,
    statusFilter,
    setStatusFilter,
    categoryFilter,
    setCategoryFilter,
    consumerOptions,
    dataUseOptions,
    categoryOptions,
    groups,
    summariesByKey,
    hasActiveFilters,
    clearFilters,
  } = usePurposeCardFilters(purposes, summaries);

  const handleClearAll = () => {
    clearFilters();
    onDataUseFilterChange(null);
    onSearchChange("");
  };

  const hasAnyFilter =
    hasActiveFilters || Boolean(dataUseFilter) || Boolean(searchQuery);

  const isEmpty = groups.length === 0;
  const hasNoPurposes = purposes.length === 0 && !hasAnyFilter;

  return (
    <div>
      <Flex justify="space-between" align="center" className="mb-4">
        <Input
          placeholder="Search purposes..."
          value={searchQuery}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            onSearchChange(e.target.value)
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
      {isEmpty && hasNoPurposes && (
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
      )}
      {isEmpty && !hasNoPurposes && (
        <Result
          status="info"
          title="No purposes match your filters"
          subTitle="Try adjusting your search or clearing filters to see more results."
          extra={<Button onClick={handleClearAll}>Clear filters</Button>}
        />
      )}
      {!isEmpty &&
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
              {items.map((purpose) => (
                <Col key={purpose.id ?? purpose.fides_key} span={6}>
                  <PurposeCard
                    purpose={purpose}
                    summary={summariesByKey.get(purpose.fides_key)}
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
