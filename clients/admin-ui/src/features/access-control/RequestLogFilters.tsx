import { Flex, Select } from "fidesui";

import SearchInput from "~/features/common/SearchInput";

import {
  DATA_USE_OPTIONS,
  POLICY_OPTIONS,
  TIME_RANGE_OPTIONS,
} from "./mock-data";

interface RequestLogFiltersProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  policyFilter: string | undefined;
  onPolicyChange: (value: string | undefined) => void;
  dataUseFilter: string | undefined;
  onDataUseChange: (value: string | undefined) => void;
  timeRange: string;
  onTimeRangeChange: (value: string) => void;
}

const RequestLogFilters = ({
  searchQuery,
  onSearchChange,
  policyFilter,
  onPolicyChange,
  dataUseFilter,
  onDataUseChange,
  timeRange,
  onTimeRangeChange,
}: RequestLogFiltersProps) => {
  return (
    <Flex justify="space-between" align="center" className="mb-6">
      <SearchInput
        value={searchQuery}
        onChange={onSearchChange}
        placeholder="Search requests..."
        className="w-64"
      />
      <Flex gap="small">
        <Select
          aria-label="Filter by policy"
          value={policyFilter}
          onChange={onPolicyChange}
          options={POLICY_OPTIONS}
          placeholder="Policy"
          allowClear
          className="w-44"
        />
        <Select
          aria-label="Filter by data use"
          value={dataUseFilter}
          onChange={onDataUseChange}
          options={DATA_USE_OPTIONS}
          placeholder="Data use"
          allowClear
          className="w-44"
        />
        <Select
          aria-label="Time range"
          value={timeRange}
          onChange={onTimeRangeChange}
          options={TIME_RANGE_OPTIONS}
          className="w-48"
        />
      </Flex>
    </Flex>
  );
};

export default RequestLogFilters;
