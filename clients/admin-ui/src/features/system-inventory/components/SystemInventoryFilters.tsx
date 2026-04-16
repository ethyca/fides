import type { Dayjs } from "dayjs";
import { DatePicker, Flex, Input, Select } from "fidesui";

import { HEALTH_FILTER_OPTIONS, SEVERITY_FILTER_OPTIONS } from "../constants";
import { HealthStatus, RiskSeverity } from "../types";

type StatusFilterValue = RiskSeverity | HealthStatus;

const STATUS_FILTER_OPTIONS: { label: string; value: StatusFilterValue }[] = [
  ...HEALTH_FILTER_OPTIONS,
  ...SEVERITY_FILTER_OPTIONS,
];

interface SystemInventoryFiltersProps {
  search: string;
  onSearchChange: (value: string) => void;
  statusFilter: StatusFilterValue[];
  onStatusFilterChange: (value: StatusFilterValue[]) => void;
  dateRange: [Dayjs, Dayjs] | null;
  onDateRangeChange: (range: [Dayjs, Dayjs] | null) => void;
  stewardFilter: string | null;
  onStewardFilterChange: (value: string | null) => void;
  groupFilter: string | null;
  onGroupFilterChange: (value: string | null) => void;
  stewardOptions: { label: string; value: string }[];
  groupOptions: { label: string; value: string }[];
}

const SystemInventoryFilters = ({
  search,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  dateRange,
  onDateRangeChange,
  groupFilter,
  onGroupFilterChange,
  stewardFilter,
  onStewardFilterChange,
  stewardOptions,
  groupOptions,
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
    <DatePicker.RangePicker
      format="YYYY-MM-DD"
      value={dateRange}
      onChange={(dates) => {
        if (dates && dates[0] && dates[1]) {
          onDateRangeChange([dates[0], dates[1]]);
        } else {
          onDateRangeChange(null);
        }
      }}
      placeholder={["From", "To"]}
      allowClear
      style={{ width: 260 }}
    />
    <div className="ml-auto" />
    <Select
      aria-label="Filter by status"
      placeholder="Status"
      mode="multiple"
      options={STATUS_FILTER_OPTIONS}
      value={statusFilter}
      onChange={onStatusFilterChange}
      allowClear
      maxTagCount="responsive"
      style={{ width: 220 }}
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
      aria-label="Filter by steward"
      placeholder="All stewards"
      options={stewardOptions}
      value={stewardFilter}
      onChange={onStewardFilterChange}
      allowClear
      style={{ width: 180 }}
    />
  </Flex>
);

export default SystemInventoryFilters;
