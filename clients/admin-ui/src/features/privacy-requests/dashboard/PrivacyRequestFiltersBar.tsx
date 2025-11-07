import dayjs from "dayjs";
import {
  AntButton as Button,
  AntDatePicker as DatePicker,
  AntFlex as Flex,
  AntInput as Input,
  AntSelect as Select,
  Icons,
} from "fidesui";

import {
  SubjectRequestActionTypeOptions,
  SubjectRequestStatusOptions,
} from "~/features/privacy-requests/constants";
import { ActionType, PrivacyRequestStatus } from "~/types/api";

interface PrivacyRequestFiltersBarProps {
  modalFilters: {
    from: string | null;
    to: string | null;
    status: PrivacyRequestStatus[] | null;
    action_type: ActionType[] | null;
  };
  setModalFilters: (filters: {
    from: string | null;
    to: string | null;
    status: PrivacyRequestStatus[] | null;
    action_type: ActionType[] | null;
  }) => void;
  onOpenAdvancedSearch: () => void;
  fuzzySearchTerm: string | null;
  setFuzzySearchTerm: (value: string | null) => void;
}

export const PrivacyRequestFiltersBar = ({
  modalFilters,
  setModalFilters,
  onOpenAdvancedSearch,
  fuzzySearchTerm,
  setFuzzySearchTerm,
}: PrivacyRequestFiltersBarProps) => {
  // Convert modalFilters to date range value
  const getDateRange = (): [dayjs.Dayjs, dayjs.Dayjs] | null => {
    if (modalFilters.from && modalFilters.to) {
      return [dayjs(modalFilters.from), dayjs(modalFilters.to)];
    }
    if (modalFilters.from) {
      return [dayjs(modalFilters.from), dayjs()];
    }
    if (modalFilters.to) {
      return [dayjs(), dayjs(modalFilters.to)];
    }
    return null;
  };

  const handleDateRangeChange = (
    dates: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null,
  ) => {
    const [from, to] = dates || [null, null];
    setModalFilters({
      ...modalFilters,
      from: from ? from.format("YYYY-MM-DD") : null,
      to: to ? to.format("YYYY-MM-DD") : null,
    });
  };

  const handleStatusChange = (value: PrivacyRequestStatus[]) => {
    setModalFilters({
      ...modalFilters,
      status: value.length > 0 ? value : null,
    });
  };

  const handleActionTypeChange = (value: ActionType[]) => {
    setModalFilters({
      ...modalFilters,
      action_type: value.length > 0 ? value : null,
    });
  };

  const actionTypeLabelRender = () => {
    const count = modalFilters.action_type?.length || 0;
    return (
      <span style={{ fontWeight: "bold" }}>
        Request type{count > 0 ? ` (${count})` : ""}
      </span>
    );
  };

  return (
    <Flex gap="small" align="center">
      <Input.Search
        placeholder="Request ID or identity value"
        value={fuzzySearchTerm || ""}
        onChange={(e) => setFuzzySearchTerm(e.target.value || null)}
        allowClear
        data-testid="privacy-request-search"
        className="w-60"
      />
      <DatePicker.RangePicker
        format="YYYY-MM-DD"
        value={getDateRange()}
        onChange={handleDateRangeChange}
        placeholder={["From date", "To date"]}
        allowClear
        data-testid="date-range-filter"
        aria-label="Date range"
        className="w-64"
      />
      <Select
        mode="multiple"
        placeholder="Status"
        options={SubjectRequestStatusOptions}
        value={modalFilters.status || []}
        onChange={handleStatusChange}
        allowClear
        maxTagCount={1}
        data-testid="request-status-filter"
        aria-label="Status"
        className="w-44"
      />
      <Select
        mode="multiple"
        placeholder="Request type"
        options={SubjectRequestActionTypeOptions}
        value={modalFilters.action_type || []}
        onChange={handleActionTypeChange}
        allowClear
        maxTagCount={1}
        data-testid="request-action-type-filter"
        aria-label="Request type"
        className="w-44"
        labelRender={actionTypeLabelRender}
      />
      <Button
        data-testid="advanced-search-btn"
        onClick={onOpenAdvancedSearch}
        icon={<Icons.SearchAdvanced />}
        aria-label="Advanced search"
      />
    </Flex>
  );
};
