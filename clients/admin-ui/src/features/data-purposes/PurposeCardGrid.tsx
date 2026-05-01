import {
  Button,
  Col,
  Divider,
  Flex,
  Icons,
  Input,
  Result,
  Row,
  Select,
  Text,
  Title,
} from "fidesui";

import type {
  DataPurpose,
  DataPurposeFilterOptions,
  PurposeSummary,
} from "./data-purpose.slice";
import PurposeCard from "./PurposeCard";
import { formatDataUse } from "./purposeUtils";
import usePurposeCardFilters from "./usePurposeCardFilters";

interface PurposeCardGridProps {
  purposes: DataPurpose[];
  summaries: PurposeSummary[];
  filterOptions: DataPurposeFilterOptions;
  dataUseFilter: string | null;
  onDataUseFilterChange: (value: string | null) => void;
  consumerFilter: string | null;
  onConsumerFilterChange: (value: string | null) => void;
  categoryFilter: string | null;
  onCategoryFilterChange: (value: string | null) => void;
  statusFilter: string | null;
  onStatusFilterChange: (value: string | null) => void;
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
  filterOptions,
  dataUseFilter,
  onDataUseFilterChange,
  consumerFilter,
  onConsumerFilterChange,
  categoryFilter,
  onCategoryFilterChange,
  statusFilter,
  onStatusFilterChange,
  searchQuery,
  onSearchChange,
  onCreatePurpose,
}: PurposeCardGridProps) => {
  const { groups, summariesByKey } = usePurposeCardFilters(purposes, summaries);

  const isEmpty = groups.length === 0;

  return (
    <div>
      <Flex justify="space-between" align="center" className="mb-4">
        <Input
          placeholder="Search purposes..."
          value={searchQuery}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            onSearchChange(e.target.value)
          }
          debounce
          allowClear
          className="w-[280px]"
        />
        <Flex gap={8} align="center">
          <Select
            aria-label="Filter by status"
            placeholder="Status"
            allowClear
            className="w-40"
            options={STATUS_OPTIONS}
            value={statusFilter}
            onChange={(v) => onStatusFilterChange(v ?? null)}
          />
          <Select
            aria-label="Filter by consumer"
            placeholder="Consumer"
            allowClear
            className="w-[200px]"
            options={filterOptions.consumers}
            value={consumerFilter}
            onChange={(v) => onConsumerFilterChange(v ?? null)}
          />
          <Select
            aria-label="Filter by data category"
            placeholder="Data category"
            allowClear
            className="w-[200px]"
            options={filterOptions.categories}
            value={categoryFilter}
            onChange={(v) => onCategoryFilterChange(v ?? null)}
          />
          <Select
            aria-label="Filter by data use"
            placeholder="Data use"
            allowClear
            className="w-[200px]"
            options={filterOptions.data_uses}
            value={dataUseFilter}
            onChange={(v) => onDataUseFilterChange(v ?? null)}
          />
        </Flex>
      </Flex>
      {isEmpty && (
        <Result
          status="info"
          title="No purposes to show"
          subTitle="Create a new purpose to get started."
          extra={
            <Button
              type="primary"
              icon={<Icons.Add />}
              onClick={onCreatePurpose}
            >
              New purpose
            </Button>
          }
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
                <Col
                  key={purpose.id ?? purpose.fides_key}
                  xs={24}
                  sm={12}
                  lg={8}
                  xl={6}
                >
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
