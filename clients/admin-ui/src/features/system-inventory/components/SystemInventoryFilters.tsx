import { Flex, Input, Select } from "fidesui";

import { HEALTH_FILTER_OPTIONS } from "../constants";
import { HealthStatus } from "../types";

interface SystemInventoryFiltersProps {
  search: string;
  onSearchChange: (value: string) => void;
  healthFilter: HealthStatus | null;
  onHealthFilterChange: (value: HealthStatus | null) => void;
  typeFilter: string | null;
  onTypeFilterChange: (value: string | null) => void;
  groupFilter: string | null;
  onGroupFilterChange: (value: string | null) => void;
  purposeFilter: string | null;
  onPurposeFilterChange: (value: string | null) => void;
  typeOptions: { label: string; value: string }[];
  groupOptions: { label: string; value: string }[];
  purposeOptions: { label: string; value: string }[];
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
  purposeFilter,
  onPurposeFilterChange,
  typeOptions,
  groupOptions,
  purposeOptions,
}: SystemInventoryFiltersProps) => (
  <Flex gap="small" align="center" className="mb-4">
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
    <Select
      aria-label="Filter by purpose"
      placeholder="All purposes"
      options={purposeOptions}
      value={purposeFilter}
      onChange={onPurposeFilterChange}
      allowClear
      style={{ width: 180 }}
    />
  </Flex>
);

export default SystemInventoryFilters;
