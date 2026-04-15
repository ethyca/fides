import { Flex, Input, Select } from "fidesui";
import { ReactNode } from "react";

import {
  FRESHNESS_FILTER_OPTIONS,
  HEALTH_FILTER_OPTIONS,
  SEVERITY_FILTER_OPTIONS,
} from "../constants";
import { HealthStatus, RiskFreshness, RiskSeverity } from "../types";

interface SystemInventoryFiltersProps {
  search: string;
  onSearchChange: (value: string) => void;
  healthFilter: HealthStatus | null;
  onHealthFilterChange: (value: HealthStatus | null) => void;
  typeFilter: string | null;
  onTypeFilterChange: (value: string | null) => void;
  groupFilter: string | null;
  onGroupFilterChange: (value: string | null) => void;
  severityFilter: RiskSeverity[];
  onSeverityFilterChange: (value: RiskSeverity[]) => void;
  freshnessFilter: RiskFreshness | null;
  onFreshnessFilterChange: (value: RiskFreshness | null) => void;
  typeOptions: { label: string; value: string }[];
  groupOptions: { label: string; value: string }[];
  expandToggle?: ReactNode;
}

const SystemInventoryFilters = ({
  search,
  onSearchChange,
  healthFilter,
  onHealthFilterChange,
  typeFilter,
  onTypeFilterChange,
  groupFilter,
  onGroupFilterChange,
  severityFilter,
  onSeverityFilterChange,
  freshnessFilter,
  onFreshnessFilterChange,
  typeOptions,
  groupOptions,
  expandToggle,
}: SystemInventoryFiltersProps) => (
  <Flex gap="small" align="center" wrap className="mb-4">
    <Input
      placeholder="Search systems..."
      value={search}
      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
        onSearchChange(e.target.value)
      }
      allowClear
      style={{ width: 260 }}
    />
    <div className="ml-auto" />
    <Select
      aria-label="Filter by health status"
      placeholder="All health"
      options={HEALTH_FILTER_OPTIONS}
      value={healthFilter}
      onChange={onHealthFilterChange}
      allowClear
      style={{ width: 160 }}
    />
    <Select
      aria-label="Filter by risk severity"
      placeholder="Any severity"
      mode="multiple"
      options={SEVERITY_FILTER_OPTIONS}
      value={severityFilter}
      onChange={onSeverityFilterChange}
      allowClear
      maxTagCount="responsive"
      style={{ width: 200 }}
    />
    <Select
      aria-label="Filter by risk freshness"
      placeholder="Any freshness"
      options={FRESHNESS_FILTER_OPTIONS}
      value={freshnessFilter}
      onChange={onFreshnessFilterChange}
      allowClear
      style={{ width: 200 }}
    />
    <Select
      aria-label="Filter by system type"
      placeholder="All types"
      options={typeOptions}
      value={typeFilter}
      onChange={onTypeFilterChange}
      allowClear
      style={{ width: 180 }}
    />
    <Select
      aria-label="Filter by group"
      placeholder="All groups"
      options={groupOptions}
      value={groupFilter}
      onChange={onGroupFilterChange}
      allowClear
      style={{ width: 180 }}
    />
    {expandToggle}
  </Flex>
);

export default SystemInventoryFilters;
