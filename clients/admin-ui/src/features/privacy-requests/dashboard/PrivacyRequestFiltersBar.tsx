import dayjs from "dayjs";
import {
  AntDatePicker as DatePicker,
  AntFlex as Flex,
  AntSelect as Select,
} from "fidesui";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import {
  SubjectRequestActionTypeOptions,
  SubjectRequestStatusOptions,
} from "~/features/privacy-requests/constants";
import { ActionType, PrivacyRequestStatus } from "~/types/api";

interface PrivacyRequestFiltersBarProps {
  filters: {
    search: string | null;
    from: string | null;
    to: string | null;
    status: PrivacyRequestStatus[] | null;
    action_type: ActionType[] | null;
  };
  setFilters: (filters: {
    search?: string | null;
    from?: string | null;
    to?: string | null;
    status?: PrivacyRequestStatus[] | null;
    action_type?: ActionType[] | null;
  }) => void;
}

export const PrivacyRequestFiltersBar = ({
  filters,
  setFilters,
}: PrivacyRequestFiltersBarProps) => {
  // Convert filters to date range value
  const getDateRange = (): [dayjs.Dayjs, dayjs.Dayjs] | null => {
    if (filters.from && filters.to) {
      return [dayjs(filters.from), dayjs(filters.to)];
    }
    if (filters.from) {
      return [dayjs(filters.from), dayjs()];
    }
    if (filters.to) {
      return [dayjs(), dayjs(filters.to)];
    }
    return null;
  };

  const handleDateRangeChange = (
    dates: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null,
  ) => {
    const [from, to] = dates || [null, null];
    setFilters({
      from: from ? from.format("YYYY-MM-DD") : null,
      to: to ? to.format("YYYY-MM-DD") : null,
    });
  };

  const handleStatusChange = (value: PrivacyRequestStatus[]) => {
    setFilters({
      status: value.length > 0 ? value : null,
    });
  };

  const handleActionTypeChange = (value: ActionType[]) => {
    setFilters({
      action_type: value.length > 0 ? value : null,
    });
  };

  const maxTagPlaceholder = (omittedValues: any[]) => (
    <span>+ {omittedValues.length}</span>
  );

  return (
    <Flex gap="small" align="center" justify="flex-start">
      <DebouncedSearchInput
        placeholder="Request ID or identity value"
        value={filters.search || ""}
        onChange={(value) => setFilters({ search: value || null })}
        variant="compact"
        data-testid="privacy-request-search"
        wrapperClassName="w-60"
      />
      <DatePicker.RangePicker
        format="YYYY-MM-DD"
        value={getDateRange()}
        onChange={handleDateRangeChange}
        placeholder={["From date", "To date"]}
        allowClear
        data-testid="date-range-filter"
        aria-label="Date range"
        className="w-60"
      />
      <Select
        mode="multiple"
        placeholder="Status"
        options={SubjectRequestStatusOptions}
        value={filters.status || []}
        onChange={handleStatusChange}
        allowClear
        maxTagCount={1}
        data-testid="request-status-filter"
        aria-label="Status"
        className="w-44"
        maxTagPlaceholder={maxTagPlaceholder}
      />
      <Select
        mode="multiple"
        placeholder="Request type"
        options={SubjectRequestActionTypeOptions}
        value={filters.action_type || []}
        onChange={handleActionTypeChange}
        allowClear
        maxTagCount={1}
        data-testid="request-action-type-filter"
        aria-label="Request type"
        className="w-44"
        maxTagPlaceholder={maxTagPlaceholder}
      />
    </Flex>
  );
};
