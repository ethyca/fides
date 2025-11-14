import dayjs from "dayjs";
import {
  AntDatePicker as DatePicker,
  AntDisplayValueType as DisplayValueType,
  AntFlex as Flex,
  AntSelect as Select,
} from "fidesui";
import { useMemo } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import {
  SubjectRequestActionTypeOptions,
  SubjectRequestStatusOptions,
} from "~/features/privacy-requests/constants";
import { useGetPrivacyCenterConfigQuery } from "~/features/privacy-requests/privacy-requests.slice";
import {
  ActionType,
  PrivacyRequestOption,
  PrivacyRequestStatus,
} from "~/types/api";

import { CustomFieldDefinition, CustomFieldFilter } from "./CustomFieldFilter";

/**
 * Extracts all unique custom fields from the privacy center config actions.
 * Returns a map of field_name -> field_definition for all unique custom fields.
 */
const extractUniqueCustomFields = (
  actions: PrivacyRequestOption[] | undefined,
): Record<string, CustomFieldDefinition> => {
  if (!actions) {
    return {};
  }

  const uniqueFields: Record<string, CustomFieldDefinition> = {};

  actions.forEach((action) => {
    if (action.custom_privacy_request_fields) {
      Object.entries(action.custom_privacy_request_fields).forEach(
        ([fieldName, fieldInfo]) => {
          // Only add if not already present (first occurrence wins)
          if (!uniqueFields[fieldName]) {
            // Cast to our extended type that includes field_type and options
            uniqueFields[fieldName] = fieldInfo as CustomFieldDefinition;
          }
        },
      );
    }
  });

  return uniqueFields;
};

interface PrivacyRequestFiltersBarProps {
  filters: {
    search: string | null;
    from: string | null;
    to: string | null;
    status: PrivacyRequestStatus[] | null;
    action_type: ActionType[] | null;
    custom_privacy_request_fields?: Record<string, string | null> | null;
  };
  setFilters: (filters: {
    search?: string | null;
    from?: string | null;
    to?: string | null;
    status?: PrivacyRequestStatus[] | null;
    action_type?: ActionType[] | null;
    custom_privacy_request_fields?: Record<string, string | null> | null;
  }) => void;
}

export const PrivacyRequestFiltersBar = ({
  filters,
  setFilters,
}: PrivacyRequestFiltersBarProps) => {
  // Fetch privacy center config to get custom fields
  const { data: config } = useGetPrivacyCenterConfigQuery();

  // Extract unique custom fields from all actions
  const uniqueCustomFields = useMemo(
    () => extractUniqueCustomFields(config?.actions),
    [config?.actions],
  );

  // Convert filters to date range value
  const getDateRange = (): [dayjs.Dayjs, dayjs.Dayjs] | null => {
    if (filters.from && filters.to) {
      return [dayjs(filters.from), dayjs(filters.to)];
    }
    return null;
  };

  const handleDateRangeChange = (
    dates: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null,
  ) => {
    const [from, to] = dates || [null, null];
    setFilters({
      from: from?.format("YYYY-MM-DD"),
      to: to?.format("YYYY-MM-DD"),
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

  const handleCustomFieldChange = (fieldName: string, value: string | null) => {
    const currentCustomFields = filters.custom_privacy_request_fields || {};
    const updatedCustomFields = {
      ...currentCustomFields,
      [fieldName]: value,
    };

    // Remove null values to keep the object clean
    const cleanedFields = Object.fromEntries(
      Object.entries(updatedCustomFields).filter(([, v]) => v !== null),
    );

    setFilters({
      custom_privacy_request_fields:
        Object.keys(cleanedFields).length > 0 ? cleanedFields : null,
    });
  };

  const maxTagPlaceholder = (omittedValues: DisplayValueType[]) => (
    <span>+ {omittedValues.length}</span>
  );

  return (
    <Flex gap="small" align="center" justify="flex-start" wrap>
      <DebouncedSearchInput
        placeholder="Request ID or identity value"
        value={filters.search || ""}
        onChange={(value) => setFilters({ search: value || null })}
        variant="compact"
        data-testid="privacy-request-search"
      />
      <DatePicker.RangePicker
        format="YYYY-MM-DD"
        value={getDateRange()}
        onChange={handleDateRangeChange}
        placeholder={["From", "To"]}
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
        maxTagCount="responsive"
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
        maxTagCount="responsive"
        data-testid="request-action-type-filter"
        aria-label="Request type"
        className="w-44"
        maxTagPlaceholder={maxTagPlaceholder}
      />
      {Object.entries(uniqueCustomFields).map(
        ([fieldName, fieldDefinition]) => (
          <CustomFieldFilter
            key={fieldName}
            fieldName={fieldName}
            fieldDefinition={fieldDefinition}
            value={filters.custom_privacy_request_fields?.[fieldName] ?? null}
            onChange={(value) => handleCustomFieldChange(fieldName, value)}
          />
        ),
      )}
    </Flex>
  );
};
