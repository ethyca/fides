// PROTOTYPE — delete with TCF history
import dayjs from "dayjs";
import { DatePicker, Flex, Select } from "fidesui";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";

import {
  HISTORY_TYPE_OPTIONS,
  HISTORY_USER_OPTIONS,
  HistoryEventType,
} from "./mockHistory";

export interface VersionHistoryFiltersState {
  search: string;
  types: HistoryEventType[];
  users: string[];
  from: string | null;
  to: string | null;
}

interface VersionHistoryFiltersProps {
  filters: VersionHistoryFiltersState;
  setFilters: (next: Partial<VersionHistoryFiltersState>) => void;
}

export const VersionHistoryFilters = ({
  filters,
  setFilters,
}: VersionHistoryFiltersProps) => {
  const dateRange: [dayjs.Dayjs, dayjs.Dayjs] | null =
    filters.from && filters.to
      ? [dayjs(filters.from), dayjs(filters.to)]
      : null;

  const handleDateRangeChange = (
    dates: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null,
  ) => {
    const [from, to] = dates ?? [null, null];
    setFilters({
      from: from ? from.format("YYYY-MM-DD") : null,
      to: to ? to.format("YYYY-MM-DD") : null,
    });
  };

  return (
    <Flex gap="small" align="center" justify="space-between" wrap>
      <Flex gap="small" align="center" wrap>
        <DebouncedSearchInput
          placeholder="Search by hash"
          value={filters.search}
          onChange={(value) => setFilters({ search: value })}
          variant="compact"
          data-testid="history-search"
        />
        <DatePicker.RangePicker
          format="YYYY-MM-DD"
          value={dateRange}
          onChange={handleDateRangeChange}
          placeholder={["From", "To"]}
          allowClear
          data-testid="history-date-range-filter"
          aria-label="Date range"
          className="w-60"
        />
      </Flex>
      <Flex gap="small" align="center" wrap>
        <Select
          mode="multiple"
          placeholder="Type"
          options={HISTORY_TYPE_OPTIONS}
          value={filters.types}
          onChange={(value: HistoryEventType[]) => setFilters({ types: value })}
          allowClear
          maxTagCount="responsive"
          data-testid="history-type-filter"
          aria-label="Type"
          className="w-56"
        />
        <Select
          mode="multiple"
          placeholder="User"
          options={HISTORY_USER_OPTIONS}
          value={filters.users}
          onChange={(value: string[]) => setFilters({ users: value })}
          allowClear
          maxTagCount="responsive"
          data-testid="history-user-filter"
          aria-label="User"
          className="w-56"
        />
      </Flex>
    </Flex>
  );
};
